from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import uuid
import asyncio
import hashlib
from datetime import datetime
from app.core.database import get_db_connection
import json
import os
from app.services.data_processing import (
    save_dataset, save_dataframe_as_new_version, DB_PATH, get_dataset_path, get_active_dataset,
    get_dataframe, invalidate_user_cache,
    create_upload_job, update_upload_job, complete_upload_job, fail_upload_job, get_upload_job,
    find_duplicate_dataset,
)
from app.services import file_store
from app.services.storage import s3_manager
from app.core.security import get_current_user
from app.services.stats_service import compute_kpis
from app.services.formula_engine import evaluate_formula, FormulaError
import pandas as pd

router = APIRouter()

class UploadResponse(BaseModel):
    job_id: str
    status: str

@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...), force: bool = Form(False), current_user: dict = Depends(get_current_user)):
    from app.core.config import MAX_UPLOAD_MB
    content = await file.read()

    # File size limit check
    max_size = MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"File size exceeds maximum limit of {MAX_UPLOAD_MB}MB.")

    # Computed unconditionally (not just when checking) so it's also stored
    # on the job row below — that's what lets an identical file uploaded
    # again *while the first is still processing* get caught too, not just
    # ones that already finished.
    content_hash = hashlib.sha256(content).hexdigest()

    # Duplicate detection stays synchronous and fast (hash + one indexed
    # lookup) so it can still respond immediately with the "upload anyway?"
    # prompt, instead of spinning up a background job just to reject it.
    if not force:
        existing = find_duplicate_dataset(content_hash, current_user["id"])
        if existing:
            if existing.get("in_progress"):
                message = f"An identical file ('{existing['name']}') is already being uploaded. Wait for it to finish, or upload anyway to create a duplicate copy."
            else:
                message = f"This file is identical to an already-uploaded dataset ('{existing['name']}', v{existing['version']}). Upload anyway to create a duplicate copy, or cancel."
            raise HTTPException(status_code=409, detail={
                "duplicate": True,
                "existing_dataset": existing,
                "message": message,
            })

    # Parsing, profiling, quality scoring and semantic classification can take
    # real time on a large file — previously all of that ran inline here,
    # blocking this request (and, since FastAPI's event loop is single-
    # threaded, every OTHER request this worker was serving) until it
    # finished. Handing it to a worker thread returns this response
    # immediately and lets the event loop keep serving other requests while
    # the upload_jobs row this creates gets real progress written to it.
    job_id = str(uuid.uuid4())
    create_upload_job(job_id, current_user["id"], file.filename, content_hash)

    def _run_upload():
        try:
            dataset_info = save_dataset(
                content, file.filename, current_user["id"], force=True,
                on_progress=lambda pct, step: update_upload_job(job_id, pct, step),
            )
            complete_upload_job(job_id, dataset_info["id"])
            # Detection should react to new data landing, not only to someone
            # happening to open the Rules page afterwards. Best-effort: a
            # rules bug should never fail an otherwise-successful upload.
            try:
                from app.services.rule_engine import evaluate_and_persist_rules
                evaluate_and_persist_rules(current_user["id"], dataset_info["id"])
            except Exception as rule_err:
                print(f"Warning: post-upload rule evaluation failed: {rule_err}")
        except ValueError as ve:
            fail_upload_job(job_id, str(ve))
        except Exception as e:
            fail_upload_job(job_id, f"Failed to process file: {str(e)}")

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _run_upload)

    return {"job_id": job_id, "status": "processing"}

def _mark_dataset_source(dataset_id: str, source_type: str, source_url: str) -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE datasets SET source_type=%s, source_url=%s, source_synced_at=%s WHERE id=%s",
            (source_type, source_url, datetime.utcnow().isoformat(), dataset_id),
        )
        conn.commit()
    finally:
        conn.close()


def _ingest_sheet(url: str, user_id: str, force: bool = True) -> dict:
    """Fetch a link-shared sheet and put it through the normal upload path.

    Reusing save_dataset rather than writing a parallel importer is the point:
    sheet data then gets the same parsing, profiling, quality scoring and
    semantic classification an uploaded file does, and because the generated
    filename is stable, a re-sync continues the same version lineage.

    `force=False` on a refresh is what keeps that lineage meaningful. Each
    version is its own row, so syncing a sheet nobody has edited would add an
    identical row every time — a dataset list full of versions that carry no
    new information. With the duplicate check left on, an unchanged sheet
    reports back as already current instead.
    """
    from app.services.google_sheets import fetch_sheet_csv, sheet_display_name, SheetError
    from app.services.data_processing import DuplicateDatasetError

    try:
        content, export_url = fetch_sheet_csv(url)
    except SheetError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        info = save_dataset(content, sheet_display_name(url), user_id, force=force)
    except DuplicateDatasetError as dup:
        existing = dup.existing_info
        _mark_dataset_source(existing["id"], "google_sheet", url)
        return {
            **existing,
            "unchanged": True,
            "source_type": "google_sheet",
            "source_url": url,
        }

    _mark_dataset_source(info["id"], "google_sheet", url)
    info["source_type"] = "google_sheet"
    info["source_url"] = url
    info["unchanged"] = False
    return info


@router.post("/connect-sheet")
async def connect_google_sheet(payload: dict, current_user: dict = Depends(get_current_user)):
    url = (payload or {}).get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="Paste the link to your Google Sheet.")
    return _ingest_sheet(url, current_user["id"])


@router.post("/{dataset_id}/refresh")
async def refresh_dataset_from_source(dataset_id: str, current_user: dict = Depends(get_current_user)):
    """Pull the sheet again and save it as a new version of this dataset."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT source_type, source_url FROM datasets WHERE id=%s AND user_id=%s",
        (dataset_id, current_user["id"]),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Dataset not found")
    source_type, source_url = row
    if source_type != "google_sheet" or not source_url:
        raise HTTPException(
            status_code=400,
            detail="This dataset was uploaded as a file, so there's no source to refresh from.",
        )

    info = _ingest_sheet(source_url, current_user["id"], force=False)

    # The refreshed copy is the one the rest of the app should be reading, and
    # the caches still hold the pre-refresh frame and KPIs until they're
    # cleared — otherwise a refresh appears to do nothing.
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO active_dataset (user_id, dataset_id) VALUES (%s, %s) "
            "ON CONFLICT (user_id) DO UPDATE SET dataset_id = EXCLUDED.dataset_id",
            (current_user["id"], info["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    invalidate_user_cache(current_user["id"])
    try:
        from app.routers.analytics import invalidate_analytics_cache
        invalidate_analytics_cache(current_user["id"])
    except Exception:
        pass

    return info


@router.get("/upload/status/{job_id}")
async def get_upload_status(job_id: str, current_user: dict = Depends(get_current_user)):
    job = get_upload_job(job_id, current_user["id"])
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found")
    return job

@router.get("/upload/status/{job_id}/stream")
async def get_upload_status_stream(job_id: str, current_user: dict = Depends(get_current_user)):
    async def event_generator():
        last_sent = None
        # ~4 minutes of polling at 0.4s intervals — comfortably longer than
        # any realistic parse+profile+classify pass; the frontend's own
        # EventSource just reconnects if this generator ever ends early.
        for _ in range(600):
            job = get_upload_job(job_id, current_user["id"])
            if not job:
                yield f"data: {json.dumps({'status': 'failed', 'error_message': 'Upload job not found'})}\n\n"
                return

            snapshot = (job["status"], job["progress"], job["current_step"])
            if snapshot != last_sent:
                yield f"data: {json.dumps(job)}\n\n"
                last_sent = snapshot

            if job["status"] in ("completed", "failed"):
                return

            await asyncio.sleep(0.4)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/active")
async def get_active_dataset_route(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return None
    return {
        "id": dataset_info["id"],
        "name": dataset_info["name"],
        "row_count": dataset_info["latest_version"].get("row_count") if dataset_info.get("latest_version") else None,
        "columns": dataset_info["columns"],
        "skipped_rows": dataset_info.get("skipped_rows", 0),
        "sheet_name": dataset_info.get("sheet_name"),
        "version": dataset_info.get("version", 1),
        "quality_score": dataset_info.get("quality_score", 0),
        "domain": dataset_info.get("domain", "generic"),
        "semantic_dict": dataset_info.get("semantic_dict")
    }

@router.get("")
async def list_datasets(workspace_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, status, created_at, latest_version, filepath, columns, skipped_rows, sheet_name, version, quality_score, source_type, source_url, source_synced_at FROM datasets WHERE user_id=%s ORDER BY created_at DESC', (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()

    # `status` is the processing state and reads "active" for every dataset that
    # uploaded successfully. Which dataset is *selected* lives in a separate
    # table, so the registry was labelling all sixty of a user's uploads
    # "Active" at once. Expose the selection separately and let the UI say which
    # one the rest of the app is actually reading.
    active = get_active_dataset(current_user["id"])
    active_id = active["id"] if active else None

    return [
        {
            "id": r[0], "name": r[1], "status": r[2],
            "is_active": r[0] == active_id,
            "created_at": r[3],
            "latest_version": (r[4] if isinstance(r[4], (dict, list)) else json.loads(r[4])) if r[4] else {}, 
            "filepath": r[5], 
            "columns": (r[6] if isinstance(r[6], (dict, list)) else json.loads(r[6])) if r[6] else [],
            "skipped_rows": r[7],
            "sheet_name": r[8],
            "version": r[9],
            "quality_score": r[10],
            "source_type": r[11] or "upload",
            "source_url": r[12],
            "source_synced_at": r[13],
        }
        for r in rows
    ]

@router.get("/compare")
async def compare_datasets(id_a: str, id_b: str, current_user: dict = Depends(get_current_user)):
    df_a = get_dataframe(id_a, current_user["id"])
    df_b = get_dataframe(id_b, current_user["id"])
    
    if df_a is None or df_b is None:
        raise HTTPException(status_code=400, detail="One or both datasets could not be loaded")
        
    # Schema diff
    cols_a = set(df_a.columns)
    cols_b = set(df_b.columns)
    only_in_a = list(cols_a - cols_b)
    only_in_b = list(cols_b - cols_a)
    common_cols = list(cols_a & cols_b)
    
    # KPI Diffs
    kpis_a = compute_kpis(df_a).get("kpis", [])
    kpis_b = compute_kpis(df_b).get("kpis", [])
    
    kpi_diffs = []
    for ka in kpis_a:
        for kb in kpis_b:
            if ka["name"] == kb["name"]:
                try:
                    val_a = float(str(ka["value"]).replace("$","").replace(",",""))
                    val_b = float(str(kb["value"]).replace("$","").replace(",",""))
                except ValueError:
                    val_a, val_b = 0, 0
                delta = val_b - val_a
                delta_pct = (delta / val_a) * 100 if val_a != 0 else 0
                
                kpi_diffs.append({
                    "name": ka["name"],
                    "value_a": val_a,
                    "value_b": val_b,
                    "delta": delta,
                    "delta_pct": delta_pct
                })
                break
                
    # Numeric column diffs (means)
    num_diffs = []
    import numpy as np
    import pandas as pd
    for col in common_cols:
        if pd.api.types.is_numeric_dtype(df_a[col]) and pd.api.types.is_numeric_dtype(df_b[col]):
            mean_a = float(df_a[col].mean()) if not pd.isna(df_a[col].mean()) else 0
            mean_b = float(df_b[col].mean()) if not pd.isna(df_b[col].mean()) else 0
            delta = mean_b - mean_a
            num_diffs.append({
                "column": col,
                "mean_a": mean_a,
                "mean_b": mean_b,
                "delta": delta
            })
            
    return {
        "schema_diff": {
            "only_in_a": only_in_a,
            "only_in_b": only_in_b,
            "common": common_cols
        },
        "kpi_diffs": kpi_diffs,
        "num_diffs": num_diffs,
        "rows_a": len(df_a),
        "rows_b": len(df_b)
    }

@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, status, created_at, latest_version, filepath, columns, skipped_rows, sheet_name, version, quality_score FROM datasets WHERE id=%s AND user_id=%s', (dataset_id, current_user["id"]))
    r = cursor.fetchone()
    conn.close()
    if not r:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return {
        "id": r[0], "name": r[1], "status": r[2], 
        "created_at": r[3], 
        "latest_version": (r[4] if isinstance(r[4], (dict, list)) else json.loads(r[4])) if r[4] else {}, 
        "filepath": r[5], 
        "columns": (r[6] if isinstance(r[6], (dict, list)) else json.loads(r[6])) if r[6] else [],
        "skipped_rows": r[7],
        "sheet_name": r[8],
        "version": r[9],
        "quality_score": r[10]
    }

@router.get("/{dataset_id}/versions")
async def list_dataset_versions(dataset_id: str, current_user: dict = Depends(get_current_user)):
    """Every version sharing this dataset's lineage, newest first.

    Lineage is keyed on (user_id, name) — deliberately the same key
    save_dataset() uses to pick the next version number, so this returns
    exactly the set those version numbers were counted against.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM datasets WHERE id=%s AND user_id=%s", (dataset_id, current_user["id"]))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Dataset not found")
    name = row[0]

    cursor.execute("SELECT dataset_id FROM active_dataset WHERE user_id=%s", (current_user["id"],))
    active_row = cursor.fetchone()
    active_id = active_row[0] if active_row else None

    cursor.execute(
        '''SELECT id, version, created_at, latest_version, columns, quality_score, status
           FROM datasets WHERE name=%s AND user_id=%s ORDER BY version DESC, created_at DESC''',
        (name, current_user["id"]),
    )
    rows = cursor.fetchall()
    conn.close()

    versions = []
    for r in rows:
        latest_version = (r[3] if isinstance(r[3], (dict, list)) else json.loads(r[3])) if r[3] else {}
        columns = (r[4] if isinstance(r[4], (dict, list)) else json.loads(r[4])) if r[4] else []
        versions.append({
            "id": r[0],
            "version": r[1] or 1,
            "created_at": r[2],
            "row_count": latest_version.get("row_count"),
            "file_size_bytes": latest_version.get("file_size_bytes"),
            "column_count": len(columns),
            "quality_score": r[5],
            "status": r[6],
            "is_active": r[0] == active_id,
        })

    return {
        "name": name,
        "versions": versions,
        "latest_version": versions[0]["version"] if versions else None,
        "latest_id": versions[0]["id"] if versions else None,
    }

@router.get("/{dataset_id}/download")
async def download_dataset(dataset_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filepath, name FROM datasets WHERE id=%s AND user_id=%s", (dataset_id, current_user["id"]))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    filename_db, original_name = row
    disk_path = get_dataset_path(filename_db)
    
    if not os.path.exists(disk_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
        
    return FileResponse(disk_path, filename=original_name, media_type="text/csv")

@router.post("/{dataset_id}/activate")
async def activate_dataset(dataset_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM datasets WHERE id=%s AND user_id=%s", (dataset_id, current_user["id"]))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Dataset not found")

    cursor.execute("INSERT INTO active_dataset (user_id, dataset_id) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET dataset_id = EXCLUDED.dataset_id", (current_user["id"], dataset_id))
    conn.commit()
    conn.close()

    # Bust caches so the next request loads fresh data
    invalidate_user_cache(current_user["id"])
    try:
        from app.routers.analytics import invalidate_analytics_cache
        invalidate_analytics_cache(current_user["id"])
    except Exception:
        pass

    return {"status": "success", "message": f"Dataset {dataset_id} activated"}

@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get filepath to delete file
    cursor.execute("SELECT filepath FROM datasets WHERE id=%s AND user_id=%s", (dataset_id, current_user["id"]))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    filename_db = row[0]
    if filename_db:
        disk_path = get_dataset_path(filename_db)
        if os.path.exists(disk_path):
            try:
                os.remove(disk_path)
            except Exception:
                pass
                
        # The durable copy has to go too, or the next read would restore the
        # file the user just deleted back onto disk.
        file_store.delete(os.path.basename(filename_db))

        # Delete from S3 if enabled
        if s3_manager.enabled:
            s3_manager.delete_file(filename_db)
                    
    # Clean up dependent records first to avoid foreign key violations
    cursor.execute("DELETE FROM active_dataset WHERE dataset_id=%s", (dataset_id,))
    cursor.execute("DELETE FROM regression_models WHERE dataset_id=%s", (dataset_id,))
    cursor.execute("DELETE FROM classification_models WHERE dataset_id=%s", (dataset_id,))
    cursor.execute("DELETE FROM clustering_models WHERE dataset_id=%s", (dataset_id,))
    cursor.execute("DELETE FROM shared_links WHERE dataset_id=%s", (dataset_id,))
    cursor.execute("DELETE FROM insights WHERE dataset_id=%s", (dataset_id,))
    cursor.execute("DELETE FROM recommendations WHERE dataset_id=%s", (dataset_id,))
    # rule_events has an FK on rules(id) and notifications point at rule_id, so
    # both have to go before the rules themselves — otherwise deleting a dataset
    # whose rules ever fired raises a foreign-key violation and the whole delete
    # fails.
    cursor.execute(
        "DELETE FROM rule_events WHERE rule_id IN (SELECT id FROM rules WHERE dataset_id=%s)",
        (dataset_id,),
    )
    cursor.execute(
        "DELETE FROM notifications WHERE rule_id IN (SELECT id FROM rules WHERE dataset_id=%s)",
        (dataset_id,),
    )
    cursor.execute("DELETE FROM rules WHERE dataset_id=%s", (dataset_id,))
    cursor.execute("DELETE FROM catalog WHERE id=%s AND user_id=%s", (dataset_id, current_user["id"]))
    
    # Now we can safely delete the dataset
    cursor.execute("DELETE FROM datasets WHERE id=%s AND user_id=%s", (dataset_id, current_user["id"]))
    
    # If we deleted the active dataset, try to fallback to most recent remaining
    cursor.execute("SELECT id FROM datasets WHERE user_id=%s ORDER BY created_at DESC LIMIT 1", (current_user["id"],))
    next_row = cursor.fetchone()
    if next_row:
        cursor.execute("INSERT INTO active_dataset (user_id, dataset_id) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET dataset_id = EXCLUDED.dataset_id", (current_user["id"], next_row[0]))
            
    conn.commit()
    conn.close()

    # Bust caches so deleted dataset is not served from memory
    invalidate_user_cache(current_user["id"])
    try:
        from app.routers.analytics import invalidate_analytics_cache
        invalidate_analytics_cache(current_user["id"])
    except Exception:
        pass


# ─── Transforms ───────────────────────────────────────────────────────────
# Rename and formula both operate on the active-lineage DataFrame and persist
# the result as the NEXT VERSION of the same (user_id, name) — reusing the
# version history/rollback/compare machinery instead of a bespoke "edit
# history" concept. Merge combines two independent lineages, so it produces
# a brand-new dataset rather than a version of either input.

def _get_dataset_name(dataset_id: str, user_id: str) -> Optional[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM datasets WHERE id=%s AND user_id=%s", (dataset_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


class RenameColumnsRequest(BaseModel):
    renames: dict[str, str]


@router.post("/{dataset_id}/transform/rename")
async def rename_columns(dataset_id: str, body: RenameColumnsRequest, current_user: dict = Depends(get_current_user)):
    if not body.renames:
        raise HTTPException(status_code=400, detail="No renames provided")

    name = _get_dataset_name(dataset_id, current_user["id"])
    if not name:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = get_dataframe(dataset_id, current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset could not be loaded")

    missing = [c for c in body.renames if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown column(s): {', '.join(missing)}")

    new_names = list(body.renames.values())
    if len(set(new_names)) != len(new_names):
        raise HTTPException(status_code=400, detail="New column names must be unique")

    untouched = [c for c in df.columns if c not in body.renames]
    collisions = set(new_names) & set(untouched)
    if collisions:
        raise HTTPException(status_code=400, detail=f"Column name(s) already in use: {', '.join(collisions)}")

    renamed_df = df.rename(columns=body.renames)
    rename_summary = ", ".join(f"{k} → {v}" for k, v in body.renames.items())
    info = save_dataframe_as_new_version(
        renamed_df, name, current_user["id"],
        description=f"Renamed columns: {rename_summary}",
        tags=["transformed", "renamed"],
    )
    return {"status": "success", "dataset": info}


class FormulaColumnRequest(BaseModel):
    column_name: str
    expression: str


@router.post("/{dataset_id}/transform/formula")
async def add_formula_column(dataset_id: str, body: FormulaColumnRequest, current_user: dict = Depends(get_current_user)):
    column_name = body.column_name.strip()
    if not column_name:
        raise HTTPException(status_code=400, detail="Column name is required")

    name = _get_dataset_name(dataset_id, current_user["id"])
    if not name:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = get_dataframe(dataset_id, current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset could not be loaded")

    if column_name in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{column_name}' already exists — rename or remove it first")

    try:
        result = evaluate_formula(df, body.expression)
    except FormulaError as e:
        raise HTTPException(status_code=400, detail=str(e))

    new_df = df.copy()
    new_df[column_name] = result
    info = save_dataframe_as_new_version(
        new_df, name, current_user["id"],
        description=f"Added derived column '{column_name}' = {body.expression}",
        tags=["transformed", "formula"],
    )
    return {"status": "success", "dataset": info}


class MergeDatasetsRequest(BaseModel):
    other_dataset_id: str
    left_on: str
    right_on: str
    how: str = "left"
    new_name: Optional[str] = None


MAX_MERGE_ROWS = 2_000_000


@router.post("/{dataset_id}/transform/merge")
async def merge_datasets_transform(dataset_id: str, body: MergeDatasetsRequest, current_user: dict = Depends(get_current_user)):
    if body.how not in ("inner", "left", "right", "outer"):
        raise HTTPException(status_code=400, detail="how must be one of: inner, left, right, outer")

    left_name = _get_dataset_name(dataset_id, current_user["id"])
    right_name = _get_dataset_name(body.other_dataset_id, current_user["id"])
    if not left_name or not right_name:
        raise HTTPException(status_code=404, detail="Dataset not found")

    left_df = get_dataframe(dataset_id, current_user["id"])
    right_df = get_dataframe(body.other_dataset_id, current_user["id"])
    if left_df is None or right_df is None:
        raise HTTPException(status_code=400, detail="One or both datasets could not be loaded")

    if body.left_on not in left_df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{body.left_on}' not found in this dataset")
    if body.right_on not in right_df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{body.right_on}' not found in the other dataset")

    try:
        merged = pd.merge(
            left_df, right_df,
            left_on=body.left_on, right_on=body.right_on,
            how=body.how, suffixes=("", "_right"),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Merge failed: {str(e)}")

    if len(merged) > MAX_MERGE_ROWS:
        raise HTTPException(
            status_code=400,
            detail=f"Merge would produce {len(merged):,} rows (limit {MAX_MERGE_ROWS:,}) — check the join keys for a many-to-many match.",
        )
    if len(merged) == 0:
        raise HTTPException(status_code=400, detail="Merge produced zero rows — the join keys may not match any records")

    merged_name = body.new_name.strip() if body.new_name and body.new_name.strip() else f"{left_name} + {right_name} (merged).csv"
    if not merged_name.lower().endswith((".csv", ".xlsx", ".parquet", ".json")):
        merged_name += ".csv"

    info = save_dataframe_as_new_version(
        merged, merged_name, current_user["id"],
        description=f"Merged '{left_name}' and '{right_name}' on {body.left_on} = {body.right_on} ({body.how} join)",
        tags=["transformed", "merged"],
    )
    return {"status": "success", "dataset": info}

    return {"status": "success", "message": "Dataset deleted"}
