import os
import threading
import pandas as pd
import uuid
import json
import hashlib
from datetime import datetime
from app.core.database import get_db_connection

from pathlib import Path

# ─── In-memory performance caches ─────────────────────────────────────────────
# Keyed by (dataset_id, user_id) → pd.DataFrame
_df_cache: dict = {}
# Keyed by user_id → dataset_info dict
_active_cache: dict = {}
_cache_lock = threading.Lock()


def invalidate_user_cache(user_id: str) -> None:
    """Clear all in-memory cache for a user. Call whenever dataset changes."""
    with _cache_lock:
        _active_cache.pop(user_id, None)
        keys_to_del = [k for k in _df_cache if k[1] == user_id]
        for k in keys_to_del:
            del _df_cache[k]

class DuplicateDatasetError(Exception):
    def __init__(self, existing_info):
        self.existing_info = existing_info
        super().__init__("Duplicate dataset")
from app.core.config import DATA_DIR, DB_PATH

from app.services.storage import s3_manager

def get_dataset_path(filename: str, skip_s3_download: bool = False) -> str:
    """Returns the absolute path to the dataset file based on its basename.
    If the file is not found locally, it attempts to download it from S3."""
    local_path = str(Path(DATA_DIR) / os.path.basename(filename))
    
    if not os.path.exists(local_path) and not skip_s3_download:
        # Try to download from S3 if it doesn't exist locally (ephemeral storage fallback)
        if s3_manager.enabled:
            print(f"File {filename} not found locally, attempting S3 download...")
            s3_manager.download_file(filename, local_path)
            
    return local_path

def run_filepath_migration():
    """Migrates any stored absolute Windows/Linux paths in SQLite to just their basenames."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name='datasets'")
        if cursor.fetchone():
            cursor.execute("SELECT id, filepath FROM datasets")
            rows = cursor.fetchall()
            for row in rows:
                dataset_id, filepath = row
                if filepath:
                    basename = os.path.basename(filepath)
                    if basename != filepath:
                        cursor.execute("UPDATE datasets SET filepath = %s WHERE id = %s", (basename, dataset_id))
            conn.commit()
    except Exception as e:
        print(f"Error running migration: {e}")
    finally:
        conn.close()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password_hash TEXT,
            full_name TEXT,
            created_at TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY,
            name TEXT,
            status TEXT,
            created_at TEXT,
            latest_version JSONB,
            filepath TEXT,
            columns JSONB
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS catalog (
            id TEXT PRIMARY KEY,
            name TEXT,
            domain TEXT,
            description TEXT,
            owner TEXT,
            tags JSONB
        )
    ''')
    
    # We must migrate active_dataset from global singleton to per-user.
    # Safe to drop since it's just ephemeral session state.
    try:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name='active_dataset'")
            
        if cursor.fetchone():
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='active_dataset'")
            columns = [c[0] for c in cursor.fetchall()]
                
            if 'user_id' not in columns:
                cursor.execute("DROP TABLE active_dataset")
    except Exception:
        pass
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_dataset (
            user_id TEXT PRIMARY KEY,
            dataset_id TEXT,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
    except Exception:
        # Ignore if insufficient privileges, assuming already installed by superuser
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id SERIAL PRIMARY KEY,
            user_id TEXT,
            content TEXT,
            embedding VECTOR(384)
        )
    ''')

    # Added so chunks from the same source document (see RAGEngine.embed_and_store's
    # chunking) stay identifiable as belonging together, even though each chunk is
    # retrieved independently. IF NOT EXISTS keeps this idempotent/safe on existing DBs.
    try:
        cursor.execute("ALTER TABLE knowledge_base ADD COLUMN IF NOT EXISTS doc_id TEXT")
        cursor.execute("ALTER TABLE knowledge_base ADD COLUMN IF NOT EXISTS chunk_index INTEGER")
    except Exception as e:
        print(f"Warning: could not add knowledge_base chunk columns: {e}")

    # DB-backed home for app.ai.governance.PromptManager — previously an
    # in-memory dict that reset on every restart.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id TEXT PRIMARY KEY,
            name TEXT,
            version TEXT,
            template TEXT,
            created_at TEXT,
            UNIQUE(name, version)
        )
    ''')

    # DB-backed home for app.ai.governance.AIEvaluationFramework — previously
    # an in-memory list that reset on every restart, making the RLHF/human
    # feedback path (submit_human_feedback) have nothing to persist to.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_evaluation_logs (
            trace_id TEXT PRIMARY KEY,
            user_id TEXT,
            prompt TEXT,
            response TEXT,
            expected TEXT,
            human_score INTEGER,
            comments TEXT,
            created_at TEXT
        )
    ''')

    # Backs real device/session management on the Settings page (list active
    # sessions, revoke one, "sign out all other devices") — JWTs alone can't be
    # revoked before they expire, so each login/signup gets a row here and its
    # id is embedded in the token pair as `sid`; get_current_user checks it.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            user_agent TEXT,
            ip_address TEXT,
            created_at TEXT,
            last_active_at TEXT,
            revoked INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Real TOTP two-factor auth: totp_secret is only meaningful once totp_enabled=1
    # (a non-null secret with totp_enabled=0 just means setup was started but never
    # confirmed with a valid code — login doesn't check totp_enabled until it's 1).
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret TEXT")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_enabled INTEGER DEFAULT 0")
    except Exception as e:
        print(f"Warning: could not add 2FA columns: {e}")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recovery_codes (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            code_hash TEXT,
            used INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS regression_models (
            id SERIAL PRIMARY KEY,
            dataset_id TEXT,
            target TEXT,
            features JSONB,
            r2_train REAL,
            r2_test REAL,
            coefficients JSONB,
            intercept REAL,
            n_rows_used INTEGER,
            timestamp TEXT,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS insights (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            dataset_id TEXT,
            title TEXT,
            description TEXT,
            category TEXT,
            insight_level TEXT,
            confidence REAL,
            impact REAL,
            recommendation TEXT,
            verified INTEGER,
            audit_sql TEXT,
            score REAL DEFAULT 0.0,
            dimension_type TEXT DEFAULT 'generic',
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            dataset_id TEXT,
            title TEXT,
            rationale TEXT,
            priority TEXT,
            category TEXT,
            verified INTEGER,
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rules (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            dataset_id TEXT,
            name TEXT,
            metric_column TEXT,
            condition TEXT,
            threshold REAL,
            "window" TEXT,
            is_active INTEGER,
            created_at TEXT
        )
    ''')
    conn.commit()
    
    # Dynamically alter table to add columns for older DB schemas
    for col, ctype, default in [
        ("skipped_rows", "INTEGER", "0"),
        ("sheet_name", "TEXT", "NULL"),
        ("version", "INTEGER", "1"),
        ("quality_score", "REAL", "0"),
        ("quality_breakdown", "TEXT", "NULL"),
        ("user_id", "TEXT", "NULL"),
        ("content_hash", "TEXT", "NULL"),
        ("domain", "TEXT", "'generic'"),
        ("semantic_dict", "TEXT", "NULL")
    ]:
        try:
            cursor.execute(f"ALTER TABLE datasets ADD COLUMN {col} {ctype} DEFAULT {default}")
            conn.commit()
        except Exception:
            conn.rollback()
            
    for col, ctype, default in [
        ("score", "REAL", "0.0"),
        ("dimension_type", "TEXT", "'generic'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE insights ADD COLUMN {col} {ctype} DEFAULT {default}")
            conn.commit()
        except Exception:
            conn.rollback()
            
    for col, ctype, default in [
        ("user_id", "TEXT", "NULL")
    ]:
        try:
            cursor.execute(f"ALTER TABLE catalog ADD COLUMN {col} {ctype} DEFAULT {default}")
            conn.commit()
        except Exception:
            conn.rollback()
            
    for col, ctype, default in [
        ("user_id", "TEXT", "NULL")
    ]:
        try:
            cursor.execute(f"ALTER TABLE regression_models ADD COLUMN {col} {ctype} DEFAULT {default}")
            conn.commit()
        except Exception:
            conn.rollback()
            
    # Migration: assign existing datasets without a user to the first created user, if any exists
    try:
        cursor.execute("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")
        first_user = cursor.fetchone()
        if first_user:
            cursor.execute("UPDATE datasets SET user_id = %s WHERE user_id IS NULL", (first_user[0],))
            cursor.execute("UPDATE catalog SET user_id = %s WHERE user_id IS NULL", (first_user[0],))
            cursor.execute("UPDATE regression_models SET user_id = %s WHERE user_id IS NULL", (first_user[0],))
    except Exception as e:
        conn.rollback()
        print(f"Error assigning legacy datasets: {e}")
        
    conn.commit()
    conn.close()
    
    # Run absolute path migration
    run_filepath_migration()
    
    # Run content hash migration
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, filepath FROM datasets WHERE content_hash IS NULL")
        rows = cursor.fetchall()
        for row in rows:
            dataset_id, filepath = row
            if filepath:
                disk_path = get_dataset_path(filepath)
                if os.path.exists(disk_path):
                    import hashlib
                    with open(disk_path, "rb") as f:
                        file_content = f.read()
                        content_hash = hashlib.sha256(file_content).hexdigest()
                        cursor.execute("UPDATE datasets SET content_hash = %s WHERE id = %s", (content_hash, dataset_id))
        conn.commit()
    except Exception as e:
        print(f"Error running hash migration: {e}")
    finally:
        conn.close()

init_db()

def parse_to_dataframe(file_content: bytes, filename: str):
    if not file_content or len(file_content.strip()) == 0:
        raise ValueError("The uploaded file is empty.")
        
    import io
    lower_filename = filename.lower()
    df = None
    metadata = {}
    
    if lower_filename.endswith(".csv") or lower_filename.endswith(".tsv"):
        sep = "\t" if lower_filename.endswith(".tsv") else ","
        
        # a) Encoding
        text = None
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                text = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            raise ValueError("Could not decode file - please save as UTF-8 CSV.")
            
        # b) Malformed CSV with on_bad_lines='skip'
        skipped_count = 0
        def bad_line_handler(line):
            nonlocal skipped_count
            skipped_count += 1
            return None
            
        try:
            # Try normal read first
            df = pd.read_csv(io.StringIO(text), sep=sep)
        except Exception:
            try:
                df = pd.read_csv(io.StringIO(text), sep=sep, on_bad_lines=bad_line_handler, engine='python')
            except Exception as e:
                raise ValueError(f"Failed to parse CSV/TSV file: {str(e)}")
                
        metadata["skipped_rows"] = skipped_count
        
    elif lower_filename.endswith(".xlsx") or lower_filename.endswith(".xls"):
        # c) Excel multi-sheet
        try:
            xl = pd.ExcelFile(io.BytesIO(file_content))
            sheets = xl.sheet_names
            selected_sheet = None
            for sheet in sheets:
                temp_df = xl.parse(sheet)
                if not temp_df.empty:
                    selected_sheet = sheet
                    df = temp_df
                    break
            if df is None:
                raise ValueError("Excel file contains no non-empty sheets.")
            metadata["sheet_name"] = selected_sheet
        except Exception as e:
            raise ValueError(f"Failed to parse Excel file: {str(e)}")
            
    elif lower_filename.endswith(".json"):
        # d) JSON / NDJSON
        text = None
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                text = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            raise ValueError("Could not decode JSON file.")
            
        try:
            data = json.loads(text)
            if isinstance(data, list):
                df = pd.json_normalize(data, max_level=1)
            elif isinstance(data, dict):
                df = pd.json_normalize([data], max_level=1)
            else:
                raise ValueError("JSON content is neither a list nor an object.")
        except Exception as e_json:
            try:
                lines = [json.loads(line) for line in text.splitlines() if line.strip()]
                if not lines:
                    raise ValueError("NDJSON content is empty.")
                df = pd.json_normalize(lines, max_level=1)
            except Exception as e_ndjson:
                raise ValueError(f"Could not parse JSON. Standard JSON error: {str(e_json)}. NDJSON error: {str(e_ndjson)}")
                
        # Deeper nesting: keep as stringified columns
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
                
    elif lower_filename.endswith(".parquet"):
        try:
            df = pd.read_parquet(io.BytesIO(file_content))
        except Exception as e:
            raise ValueError(f"Failed to parse Parquet file: {str(e)}")
            
    else:
        raise ValueError(f"Unsupported file format: {filename}")
        
    # e) Empty file / zero rows / no columns
    if df is None:
        raise ValueError("The parsed file resulted in no data (null dataframe).")
    if len(df) == 0:
        raise ValueError("The dataset contains zero rows of data.")
    if len(df.columns) == 0:
        raise ValueError("The dataset contains zero columns.")
        
    # f) Duplicate column names
    cols = list(df.columns)
    seen = {}
    new_cols = []
    has_duplicates = False
    for col in cols:
        col_str = str(col)
        if col_str in seen:
            has_duplicates = True
            seen[col_str] += 1
            new_cols.append(f"{col_str}_{seen[col_str]}")
        else:
            seen[col_str] = 1
            new_cols.append(col_str)
    df.columns = new_cols
    metadata["duplicate_columns_renamed"] = has_duplicates
    
    return df, metadata

def save_dataset(file_content: bytes, filename: str, user_id: str, force: bool = False):
    content_hash = hashlib.sha256(file_content).hexdigest()

    if not force:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, version, created_at FROM datasets WHERE content_hash = %s AND user_id = %s LIMIT 1", (content_hash, user_id))
        existing = cursor.fetchone()
        conn.close()
        
        if existing:
            raise DuplicateDatasetError({
                "id": existing[0],
                "name": existing[1],
                "version": existing[2],
                "uploaded_at": existing[3]
            })

    # Determine version
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(version) FROM datasets WHERE name = %s AND user_id = %s", (filename, user_id))
    max_ver = cursor.fetchone()[0]
    version = (max_ver + 1) if max_ver is not None else 1
    conn.close()

    # Try parsing first (robust validation)
    df, metadata = parse_to_dataframe(file_content, filename)
    
    dataset_id = str(uuid.uuid4())
    filename_db = f"{dataset_id}_{filename}"
    disk_path = get_dataset_path(filename_db, skip_s3_download=True)  # File doesn't exist yet, skip S3 check
    
    with open(disk_path, "wb") as f:
        f.write(file_content)
        
    # Upload to S3 if enabled
    if s3_manager.enabled:
        s3_manager.upload_file(file_content, filename_db)
        
    row_count = len(df)
    col_count = len(df.columns)
    
    # Create profile
    columns = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        null_count = int(df[col].isnull().sum())
        col_info = {"name": col, "type": dtype, "null_count": null_count}
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info["mean"] = float(df[col].mean()) if not pd.isna(df[col].mean()) else 0.0
            col_info["min"] = float(df[col].min()) if not pd.isna(df[col].min()) else 0.0
            col_info["max"] = float(df[col].max()) if not pd.isna(df[col].max()) else 0.0
        columns.append(col_info)
        
    from app.services.stats_service import quality_report
    quality = quality_report(df)
    quality_score = quality.get("quality_score", 0)
    quality_breakdown = json.dumps(quality.get("breakdown", {}))
        
    dataset_info = {
        "id": dataset_id,
        "name": filename,
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "latest_version": {
            "row_count": row_count,
            "file_size_bytes": len(file_content)
        },
        "filepath": filename_db,
        "columns": columns,
        "skipped_rows": metadata.get("skipped_rows", 0),
        "sheet_name": metadata.get("sheet_name"),
        "version": version,
        "quality_score": quality_score,
        "quality_breakdown": quality_breakdown
    }
    
    from app.services.semantic_classification import classify_dataset_and_build_dictionary
    domain, semantic_dict = classify_dataset_and_build_dictionary(df, filename)
    dataset_info["domain"] = domain
    dataset_info["semantic_dict"] = semantic_dict

    catalog_entry = {
        "id": dataset_id,
        "name": filename,
        "domain": domain,
        "description": f"Auto-generated catalog entry for {filename}. Contains {row_count} rows and {col_count} columns.",
        "owner": "DataMind OS",
        "tags": ["auto-inferred", "raw-data"]
    }
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO datasets (id, name, status, created_at, latest_version, filepath, columns, skipped_rows, sheet_name, version, quality_score, quality_breakdown, user_id, content_hash, domain, semantic_dict)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        dataset_id, filename, dataset_info["status"], dataset_info["created_at"],
        json.dumps(dataset_info["latest_version"]), filename_db, json.dumps(columns),
        dataset_info["skipped_rows"], dataset_info["sheet_name"], dataset_info["version"],
        dataset_info["quality_score"], dataset_info["quality_breakdown"], user_id, content_hash,
        domain, json.dumps(semantic_dict)
    ))
    
    cursor.execute('''
        INSERT INTO catalog (id, name, domain, description, owner, tags, user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (
        dataset_id, catalog_entry["name"], catalog_entry["domain"],
        catalog_entry["description"], catalog_entry["owner"], json.dumps(catalog_entry["tags"]), user_id
    ))
    
    cursor.execute('''
        INSERT INTO active_dataset (user_id, dataset_id) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET dataset_id = EXCLUDED.dataset_id
    ''', (user_id, dataset_id))
    
    conn.commit()
    conn.close()

    # Invalidate cache so next request picks up the new dataset
    invalidate_user_cache(user_id)

    return dataset_info

def get_active_dataset(user_id: str):
    # ── Cache hit ──────────────────────────────────────────────────────────────
    with _cache_lock:
        if user_id in _active_cache:
            return _active_cache[user_id]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT dataset_id FROM active_dataset WHERE user_id = %s
    ''', (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    dataset_id = row[0]
    cursor.execute('''
        SELECT id, name, status, created_at, latest_version, filepath, columns, skipped_rows, sheet_name, version, quality_score, quality_breakdown, domain, semantic_dict
        FROM datasets WHERE id = %s AND user_id = %s
    ''', (dataset_id, user_id))
    dataset_row = cursor.fetchone()
    conn.close()
    
    if not dataset_row:
        return None
        
    dataset_info = {
        "id": dataset_row[0],
        "name": dataset_row[1],
        "status": dataset_row[2],
        "created_at": dataset_row[3],
        "latest_version": dataset_row[4] if isinstance(dataset_row[4], (dict, list)) else json.loads(dataset_row[4]),
        "filepath": dataset_row[5],
        "columns": dataset_row[6] if isinstance(dataset_row[6], (dict, list)) else json.loads(dataset_row[6]),
        "skipped_rows": dataset_row[7],
        "sheet_name": dataset_row[8],
        "version": dataset_row[9],
        "quality_score": dataset_row[10],
        "quality_breakdown": (dataset_row[11] if isinstance(dataset_row[11], (dict, list)) else json.loads(dataset_row[11])) if dataset_row[11] else {},
        "domain": dataset_row[12] if len(dataset_row) > 12 and dataset_row[12] is not None else "generic",
        "semantic_dict": (dataset_row[13] if isinstance(dataset_row[13], (dict, list)) else json.loads(dataset_row[13])) if len(dataset_row) > 13 and dataset_row[13] is not None else None
    }
    
    # Lazy classification if domain or semantic_dict is missing
    if not dataset_info.get("semantic_dict"):
        df = get_dataframe(dataset_info["id"], user_id)
        if df is not None and len(df) > 0:
            from app.services.semantic_classification import classify_dataset_and_build_dictionary
            domain, semantic_dict = classify_dataset_and_build_dictionary(df, dataset_info["name"])
            dataset_info["domain"] = domain
            dataset_info["semantic_dict"] = semantic_dict
            
            # Save back to database
            conn_w = get_db_connection()
            cursor_w = conn_w.cursor()
            cursor_w.execute('''
                UPDATE datasets 
                SET domain = %s, semantic_dict = %s
                WHERE id = %s
            ''', (domain, json.dumps(semantic_dict), dataset_info["id"]))
            
            # Update catalog domain if generic or General
            cursor_w.execute('''
                UPDATE catalog
                SET domain = %s
                WHERE id = %s AND (domain = 'General' OR domain = 'sales' OR domain = 'Sales')
            ''', (domain, dataset_info["id"]))
            
            conn_w.commit()
            conn_w.close()
    
    # Lazy computation for datasets where quality_score is 0.0 (from schema DEFAULT 0)
    if dataset_info["quality_score"] == 0.0:
        df = get_dataframe(dataset_info["id"], user_id)
        if df is not None and len(df) > 0:
            from app.services.stats_service import quality_report
            quality = quality_report(df)
            dataset_info["quality_score"] = quality.get("quality_score", 0)
            dataset_info["quality_breakdown"] = quality.get("breakdown", {})
            
            # Save back to database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE datasets 
                SET quality_score = %s, quality_breakdown = %s
                WHERE id = %s
            ''', (dataset_info["quality_score"], json.dumps(dataset_info["quality_breakdown"]), dataset_info["id"]))
            conn.commit()
            conn.close()

    # ── Cache the resolved dataset_info ───────────────────────────────────────
    with _cache_lock:
        _active_cache[user_id] = dataset_info

    return dataset_info

def get_dataframe(dataset_id: str, user_id: str):
    # ── Cache hit — return instantly without any disk/DB I/O ──────────────────
    cache_key = (dataset_id, user_id)
    with _cache_lock:
        if cache_key in _df_cache:
            return _df_cache[cache_key]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT filepath, sheet_name FROM datasets WHERE id = %s AND user_id = %s', (dataset_id, user_id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    filename_db, sheet_name = row
    disk_path = get_dataset_path(filename_db)
    if not os.path.exists(disk_path):
        return None

    lower_path = disk_path.lower()
    df = None
    if lower_path.endswith(".csv"):
        df = pd.read_csv(disk_path, on_bad_lines='skip')
    elif lower_path.endswith(".tsv"):
        df = pd.read_csv(disk_path, sep="\t", on_bad_lines='skip')
    elif lower_path.endswith(".xlsx") or lower_path.endswith(".xls"):
        if sheet_name:
            df = pd.read_excel(disk_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(disk_path)
    elif lower_path.endswith(".json"):
        with open(disk_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        try:
            data = json.loads(text)
            if isinstance(data, list):
                df = pd.json_normalize(data, max_level=1)
            else:
                df = pd.json_normalize([data], max_level=1)
        except Exception:
            lines = [json.loads(line) for line in text.splitlines() if line.strip()]
            df = pd.json_normalize(lines, max_level=1)
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
    elif lower_path.endswith(".parquet"):
        df = pd.read_parquet(disk_path)
    else:
        df = pd.read_csv(disk_path, on_bad_lines='skip')

    # ── Store in cache for all future requests ─────────────────────────────────
    if df is not None:
        with _cache_lock:
            _df_cache[cache_key] = df

    return df

