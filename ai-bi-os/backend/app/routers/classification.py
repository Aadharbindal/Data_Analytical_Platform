import re
import json
from datetime import datetime

import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Literal, Optional
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
async def get_classification_columns(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded")

    total_rows = len(df)

    # Targets: low-cardinality columns (2-20 distinct values) usable as class labels
    targets = []
    for col in df.columns:
        if _is_date_like(df, col):
            continue
        num_unique = df[col].nunique()
        if num_unique < 2 or num_unique > 20:
            continue
        if 'id' in col.lower() or num_unique > total_rows * 0.5:
            continue
        targets.append(col)

    # Features: same rules as regression (numeric, or low-cardinality categorical)
    features = []
    for col in df.columns:
        if _is_date_like(df, col):
            continue
        num_unique = df[col].nunique()
        if 'id' in col.lower() or num_unique > total_rows * 0.5:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]) and num_unique > 20:
            continue
        features.append(col)

    return {"targets": targets, "features": features}


class TrainRequest(BaseModel):
    target: str
    features: List[str]
    algorithm: Literal["logistic", "decision_tree"] = "logistic"


@router.post("/train")
async def train_classification_model(req: TrainRequest, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")

    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded")

    if req.target not in df.columns:
        raise HTTPException(status_code=400, detail=f"Target column '{req.target}' not found")

    total_rows = len(df)
    target_unique = df[req.target].nunique()
    if _is_date_like(df, req.target):
        raise HTTPException(status_code=400, detail="Target column cannot be date-like.")
    if target_unique < 2 or target_unique > 20:
        raise HTTPException(status_code=400, detail=f"Target must have between 2 and 20 distinct classes (has {target_unique}).")
    if 'id' in req.target.lower() or target_unique > total_rows * 0.5:
        raise HTTPException(status_code=400, detail=f"'{req.target}' looks identifier-like and can't be used as a target.")

    for f in req.features:
        if f not in df.columns:
            raise HTTPException(status_code=400, detail=f"Feature column '{f}' not found")
        if _is_date_like(df, f):
            raise HTTPException(status_code=400, detail=f"'{f}' cannot be used: date-like columns are not supported.")
        num_unique = df[f].nunique()
        if 'id' in f.lower() or num_unique > total_rows * 0.5:
            raise HTTPException(status_code=400, detail=f"'{f}' cannot be used: identifier-like column ({num_unique} distinct values in {total_rows} rows).")
        if not pd.api.types.is_numeric_dtype(df[f]) and num_unique > 20:
            raise HTTPException(status_code=400, detail=f"'{f}' cannot be used: categorical column with >20 distinct values ({num_unique}).")

    cols = [req.target] + req.features
    df_sub = df[cols].dropna()

    if len(df_sub) < 20:
        raise HTTPException(status_code=400, detail="Not enough data: must have >= 20 rows after dropping nulls")

    if df_sub[req.target].nunique() < 2:
        raise HTTPException(status_code=400, detail="Target must have at least 2 classes after dropping missing values.")

    X = df_sub[req.features]
    y_original = df_sub[req.target].astype(str)

    cat_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
    for col in cat_cols:
        if X[col].nunique() > 20:
            raise HTTPException(status_code=400, detail=f"Column '{col}' has >20 distinct values. Too many categories for one-hot encoding.")
    if cat_cols:
        X = pd.get_dummies(X, columns=cat_cols, drop_first=True)

    from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
    from sklearn.linear_model import LogisticRegression
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, roc_auc_score

    le = LabelEncoder()
    y = le.fit_transform(y_original)
    class_labels = le.classes_.tolist()
    n_classes = len(class_labels)

    n_rows_used = len(df_sub)

    # Class balance of the full modeled subset (used for the "beat the baseline" check)
    full_counts = pd.Series(y_original).value_counts()
    baseline_accuracy = float(full_counts.max() / n_rows_used)
    class_distribution = [
        {"label": label, "count": int(full_counts.get(label, 0))} for label in class_labels
    ]

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    except ValueError:
        # A class too small to stratify a held-out split from — fall back to a plain random split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

    def make_model():
        if req.algorithm == "decision_tree":
            return DecisionTreeClassifier(max_depth=6, min_samples_leaf=5, random_state=42)
        return LogisticRegression(max_iter=1000, random_state=42)

    model = make_model()
    model.fit(X_train, y_train)

    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    accuracy_train = float(accuracy_score(y_train, y_pred_train))
    accuracy_test = float(accuracy_score(y_test, y_pred_test))

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred_test, average='macro', zero_division=0
    )
    precision_test = float(precision)
    recall_test = float(recall)
    f1_test = float(f1)

    cm = confusion_matrix(y_test, y_pred_test, labels=list(range(n_classes)))
    confusion = cm.tolist()

    roc_auc = None
    if n_classes == 2:
        try:
            if hasattr(model, "predict_proba"):
                y_proba = model.predict_proba(X_test)[:, 1]
            else:
                y_proba = model.decision_function(X_test)
            roc_auc = float(roc_auc_score(y_test, y_proba))
        except Exception:
            roc_auc = None

    feature_importance = []
    if req.algorithm == "logistic":
        coefs = model.coef_
        if n_classes == 2:
            for feature_name, coef in zip(X.columns, coefs[0]):
                feature_importance.append({"feature": feature_name, "value": float(coef)})
        else:
            avg_importance = np.mean(np.abs(coefs), axis=0)
            for feature_name, val in zip(X.columns, avg_importance):
                feature_importance.append({"feature": feature_name, "value": float(val)})
    else:
        for feature_name, val in zip(X.columns, model.feature_importances_):
            feature_importance.append({"feature": feature_name, "value": float(val)})

    # Sample predictions for a results table
    predictions_sample = []
    sample_size = min(100, len(y_test))
    y_test_arr = np.asarray(y_test)[:sample_size]
    y_pred_arr = np.asarray(y_pred_test)[:sample_size]
    for act, pred in zip(y_test_arr, y_pred_arr):
        predictions_sample.append({
            "actual": class_labels[int(act)],
            "predicted": class_labels[int(pred)],
            "correct": bool(act == pred)
        })

    # ── Stratified K-fold cross-validation — a single 80/20 split is a noisy
    # accuracy estimate on small/imbalanced datasets; averaging over folds
    # (with class proportions preserved per-fold) is more robust ──
    cross_validation = None
    try:
        n_folds = min(5, n_rows_used // 4)
        min_class_count = int(np.min(np.bincount(y)))
        n_folds = min(n_folds, min_class_count)
        if n_folds >= 2:
            skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
            cv_scores = cross_val_score(make_model(), X, y, cv=skf, scoring='accuracy')
            cross_validation = {
                "folds": n_folds,
                "accuracy_mean": float(np.mean(cv_scores)),
                "accuracy_std": float(np.std(cv_scores)),
                "accuracy_per_fold": [float(s) for s in cv_scores]
            }
    except Exception:
        cross_validation = None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO classification_models
            (dataset_id, target, features, algorithm, accuracy_train, accuracy_test,
             precision_test, recall_test, f1_test, roc_auc, baseline_accuracy,
             class_labels, confusion_matrix, feature_importance, n_rows_used, timestamp, user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        dataset_info["id"],
        req.target,
        json.dumps(req.features),
        req.algorithm,
        accuracy_train,
        accuracy_test,
        precision_test,
        recall_test,
        f1_test,
        roc_auc,
        baseline_accuracy,
        json.dumps(class_labels),
        json.dumps(confusion),
        json.dumps(feature_importance),
        n_rows_used,
        datetime.now().isoformat(),
        current_user["id"]
    ))
    conn.commit()
    conn.close()

    return {
        "algorithm": req.algorithm,
        "accuracy_train": accuracy_train,
        "accuracy_test": accuracy_test,
        "precision_test": precision_test,
        "recall_test": recall_test,
        "f1_test": f1_test,
        "roc_auc": roc_auc,
        "baseline_accuracy": baseline_accuracy,
        "class_labels": class_labels,
        "confusion_matrix": confusion,
        "class_distribution": class_distribution,
        "feature_importance": feature_importance,
        "predictions_sample": predictions_sample,
        "n_rows_used": n_rows_used,
        "cross_validation": cross_validation
    }


@router.get("/models")
async def get_classification_models(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, target, features, algorithm, accuracy_train, accuracy_test,
               precision_test, recall_test, f1_test, roc_auc, baseline_accuracy,
               class_labels, confusion_matrix, feature_importance, n_rows_used, timestamp
        FROM classification_models
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
            "target": r[1],
            "features": _j(r[2]),
            "algorithm": r[3],
            "accuracy_train": r[4],
            "accuracy_test": r[5],
            "precision_test": r[6],
            "recall_test": r[7],
            "f1_test": r[8],
            "roc_auc": r[9],
            "baseline_accuracy": r[10],
            "class_labels": _j(r[11]),
            "confusion_matrix": _j(r[12]),
            "feature_importance": _j(r[13]),
            "n_rows_used": r[14],
            "timestamp": r[15]
        })
    return models


@router.get("/quality-summary")
async def get_classification_quality_summary(current_user: dict = Depends(get_current_user)):
    """
    Deterministic quality/trust scoring for the most recently trained
    classification model, computed from accuracy_train/accuracy_test
    actually stored in classification_models — mirrors the regression
    engine's quality-summary approach.
    """
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return {"available": False, "reason": "No active dataset"}

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT target, features, algorithm, accuracy_train, accuracy_test, baseline_accuracy, n_rows_used, timestamp
        FROM classification_models
        WHERE dataset_id = %s AND user_id = %s
        ORDER BY timestamp DESC
        LIMIT 1
    ''', (dataset_info["id"], current_user["id"]))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"available": False, "reason": "No classification model trained yet for this dataset"}

    target, features, algorithm, accuracy_train, accuracy_test, baseline_accuracy, n_rows_used, timestamp = row
    accuracy_train = accuracy_train or 0.0
    accuracy_test = accuracy_test or 0.0
    baseline_accuracy = baseline_accuracy or 0.0
    overfitting_gap = round(accuracy_train - accuracy_test, 3)

    quality_score = round(max(0.0, min(100.0, accuracy_test * 100)), 1)
    trust_score = round(max(0.0, quality_score - max(0.0, overfitting_gap) * 100), 1)
    lift_over_baseline = round((accuracy_test - baseline_accuracy) * 100, 1)

    if quality_score >= 60 and overfitting_gap < 0.15 and lift_over_baseline > 0:
        deployment_status = "Approved"
    elif quality_score >= 30:
        deployment_status = "Needs Review"
    else:
        deployment_status = "Not Recommended"

    return {
        "available": True,
        "target": target,
        "features": features if isinstance(features, (dict, list)) else json.loads(features),
        "algorithm": algorithm,
        "accuracy_train": round(accuracy_train, 3),
        "accuracy_test": round(accuracy_test, 3),
        "baseline_accuracy": round(baseline_accuracy, 3),
        "lift_over_baseline": lift_over_baseline,
        "overfitting_gap": overfitting_gap,
        "quality_score": quality_score,
        "trust_score": trust_score,
        "deployment_status": deployment_status,
        "n_rows_used": n_rows_used,
        "version": timestamp
    }
