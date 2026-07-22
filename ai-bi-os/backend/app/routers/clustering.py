import re
import json
from datetime import datetime

import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db_connection
from app.services.data_processing import get_active_dataset, get_dataframe
from app.core.security import get_current_user

router = APIRouter()


def _is_date_like(df: pd.DataFrame, col: str) -> bool:
    if re.search(r'date|month|year|time', col, re.IGNORECASE):
        return True
    if pd.api.types.is_datetime64_any_dtype(df[col]):
        return True
    return False


@router.get("/columns")
async def get_clustering_columns(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded")

    total_rows = len(df)
    features = []
    for col in df.select_dtypes(include=[np.number]).columns:
        if _is_date_like(df, col):
            continue
        num_unique = df[col].nunique()
        if 'id' in col.lower() or num_unique > total_rows * 0.5:
            continue
        features.append(col)

    return {"features": features}


class TrainRequest(BaseModel):
    features: List[str]
    n_clusters: Optional[int] = None


@router.post("/train")
async def train_clustering_model(req: TrainRequest, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")

    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded")

    if len(req.features) < 2:
        raise HTTPException(status_code=400, detail="Select at least 2 numeric features for clustering.")

    total_rows = len(df)
    for f in req.features:
        if f not in df.columns:
            raise HTTPException(status_code=400, detail=f"Feature column '{f}' not found")
        if not pd.api.types.is_numeric_dtype(df[f]):
            raise HTTPException(status_code=400, detail=f"'{f}' must be numeric for clustering.")
        if _is_date_like(df, f):
            raise HTTPException(status_code=400, detail=f"'{f}' cannot be used: date-like columns are not supported.")
        num_unique = df[f].nunique()
        if 'id' in f.lower() or num_unique > total_rows * 0.5:
            raise HTTPException(status_code=400, detail=f"'{f}' cannot be used: identifier-like column ({num_unique} distinct values in {total_rows} rows).")

    df_sub = df[req.features].dropna()
    n_rows_used = len(df_sub)
    if n_rows_used < 20:
        raise HTTPException(status_code=400, detail="Not enough data: must have >= 20 rows after dropping nulls")

    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.decomposition import PCA

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_sub.values)

    max_k = min(10, n_rows_used - 1)
    if max_k < 2:
        raise HTTPException(status_code=400, detail="Not enough rows to form clusters.")

    if req.n_clusters is not None and not (2 <= req.n_clusters <= max_k):
        raise HTTPException(status_code=400, detail=f"n_clusters must be between 2 and {max_k}.")

    # ── Fit every k once: doubles as the elbow chart data and (when no k is
    # requested) the search space for auto-selecting the best-separated k ──
    k_range = list(range(2, max_k + 1))
    elbow_data = []
    fitted = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels_k = km.fit_predict(X_scaled)
        try:
            sil_k = float(silhouette_score(X_scaled, labels_k))
        except Exception:
            sil_k = None
        elbow_data.append({"k": k, "inertia": float(km.inertia_), "silhouette": sil_k})
        fitted[k] = km

    auto_selected = req.n_clusters is None
    if req.n_clusters is not None:
        chosen_k = req.n_clusters
    else:
        valid = [e for e in elbow_data if e["silhouette"] is not None]
        chosen_k = max(valid, key=lambda e: e["silhouette"])["k"] if valid else k_range[0]

    model = fitted[chosen_k]
    labels = model.labels_
    silhouette = float(silhouette_score(X_scaled, labels))
    inertia = float(model.inertia_)

    counts = pd.Series(labels).value_counts().sort_index()
    cluster_sizes = [{"cluster": int(i), "count": int(counts.get(i, 0))} for i in range(chosen_k)]

    centers_original = scaler.inverse_transform(model.cluster_centers_)
    cluster_centers = []
    for i, center in enumerate(centers_original):
        cluster_centers.append({
            "cluster": i,
            "center": {feat: float(val) for feat, val in zip(req.features, center)}
        })

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X_scaled)
    pca_explained_variance = [float(v) for v in pca.explained_variance_ratio_]

    n_points = len(coords)
    if n_points > 500:
        idx = np.random.RandomState(42).choice(n_points, 500, replace=False)
    else:
        idx = np.arange(n_points)
    pca_points = [
        {"x": float(coords[i, 0]), "y": float(coords[i, 1]), "cluster": int(labels[i])}
        for i in idx
    ]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO clustering_models
            (dataset_id, features, n_clusters, auto_selected, silhouette_score, inertia,
             cluster_sizes, cluster_centers, elbow_data, n_rows_used, timestamp, user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        dataset_info["id"],
        json.dumps(req.features),
        chosen_k,
        auto_selected,
        silhouette,
        inertia,
        json.dumps(cluster_sizes),
        json.dumps(cluster_centers),
        json.dumps(elbow_data),
        n_rows_used,
        datetime.now().isoformat(),
        current_user["id"]
    ))
    conn.commit()
    conn.close()

    return {
        "features": req.features,
        "n_clusters": chosen_k,
        "auto_selected": auto_selected,
        "silhouette_score": silhouette,
        "inertia": inertia,
        "cluster_sizes": cluster_sizes,
        "cluster_centers": cluster_centers,
        "elbow_data": elbow_data,
        "pca_points": pca_points,
        "pca_explained_variance": pca_explained_variance,
        "n_rows_used": n_rows_used
    }


@router.get("/models")
async def get_clustering_models(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, features, n_clusters, auto_selected, silhouette_score, inertia,
               cluster_sizes, cluster_centers, elbow_data, n_rows_used, timestamp
        FROM clustering_models
        WHERE dataset_id = %s AND user_id = %s
        ORDER BY timestamp DESC
    ''', (dataset_info["id"], current_user["id"]))
    rows = cursor.fetchall()
    conn.close()

    def _j(v):
        return v if isinstance(v, (dict, list)) else json.loads(v)

    models = []
    for r in rows:
        models.append({
            "id": r[0],
            "features": _j(r[1]),
            "n_clusters": r[2],
            "auto_selected": r[3],
            "silhouette_score": r[4],
            "inertia": r[5],
            "cluster_sizes": _j(r[6]),
            "cluster_centers": _j(r[7]),
            "elbow_data": _j(r[8]),
            "n_rows_used": r[9],
            "timestamp": r[10]
        })
    return models


@router.get("/quality-summary")
async def get_clustering_quality_summary(current_user: dict = Depends(get_current_user)):
    """
    Deterministic quality/trust scoring for the most recently trained
    clustering model, computed from the silhouette score actually stored
    in clustering_models — mirrors the regression engine's quality-summary
    approach, adapted for an unsupervised (no train/test split) setting.
    """
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"available": False, "reason": "No active dataset"}

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT features, n_clusters, silhouette_score, cluster_sizes, n_rows_used, timestamp
        FROM clustering_models
        WHERE dataset_id = %s AND user_id = %s
        ORDER BY timestamp DESC
        LIMIT 1
    ''', (dataset_info["id"], current_user["id"]))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"available": False, "reason": "No clustering model trained yet for this dataset"}

    features, n_clusters, silhouette, cluster_sizes, n_rows_used, timestamp = row
    silhouette = silhouette or 0.0
    cluster_sizes = cluster_sizes if isinstance(cluster_sizes, (dict, list)) else json.loads(cluster_sizes)

    # Silhouette ranges [-1, 1]; map to a 0-100 quality score
    quality_score = round(max(0.0, min(100.0, (silhouette + 1) / 2 * 100)), 1)

    # Penalize badly imbalanced clusters (a tiny sliver cluster is usually noise, not signal)
    min_fraction = min((c["count"] for c in cluster_sizes), default=0) / n_rows_used if n_rows_used else 0
    if min_fraction < 0.02:
        imbalance_penalty = 20.0
    elif min_fraction < 0.05:
        imbalance_penalty = 10.0
    else:
        imbalance_penalty = 0.0
    trust_score = round(max(0.0, quality_score - imbalance_penalty), 1)

    if quality_score >= 60 and imbalance_penalty == 0.0:
        deployment_status = "Approved"
    elif quality_score >= 30:
        deployment_status = "Needs Review"
    else:
        deployment_status = "Not Recommended"

    return {
        "available": True,
        "features": features if isinstance(features, (dict, list)) else json.loads(features),
        "n_clusters": n_clusters,
        "silhouette_score": round(silhouette, 3),
        "quality_score": quality_score,
        "trust_score": trust_score,
        "deployment_status": deployment_status,
        "n_rows_used": n_rows_used,
        "version": timestamp
    }
