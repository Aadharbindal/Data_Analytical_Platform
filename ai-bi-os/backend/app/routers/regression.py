import pandas as pd
import numpy as np
from app.core.database import get_db_connection
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Dict, Any
from app.services.data_processing import get_active_dataset, get_dataframe
from app.core.config import DB_PATH
from app.core.security import get_current_user
from pydantic import BaseModel

router = APIRouter()

@router.get("/columns")
async def get_regression_columns(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded")

    from app.services.stats_service import find_column
    import re
    
    targets = df.select_dtypes(include=[np.number]).columns.tolist()
    
    features = []
    for col in df.columns:
        is_date = False
        if re.search(r'date|month|year|time', col, re.IGNORECASE):
            is_date = True
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            is_date = True
            
        if is_date:
            continue
            
        num_unique = df[col].nunique()
        total_rows = len(df)
        
        # ID-like columns
        if 'id' in col.lower() or num_unique > total_rows * 0.5:
            continue
            
        # Categorical with too many distinct values
        if not pd.api.types.is_numeric_dtype(df[col]) and num_unique > 20:
            continue
            
        features.append(col)
        
    return {"targets": targets, "features": features}

class TrainRequest(BaseModel):
    target: str
    features: List[str]

@router.post("/train")
async def train_regression_model(req: TrainRequest, current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        raise HTTPException(status_code=400, detail="No active dataset")
    
    df = get_dataframe(dataset_info["id"], current_user["id"])
    if df is None:
        raise HTTPException(status_code=400, detail="Dataset not loaded")
        
    if req.target not in df.columns:
        raise HTTPException(status_code=400, detail=f"Target column '{req.target}' not found")
    
    if not pd.api.types.is_numeric_dtype(df[req.target]):
        raise HTTPException(status_code=400, detail="Target column must be numeric")
        
    for f in req.features:
        if f not in df.columns:
            raise HTTPException(status_code=400, detail=f"Feature column '{f}' not found")
        
        # Validation matching the /columns rules
        is_date = False
        import re
        if re.search(r'date|month|year|time', f, re.IGNORECASE) or pd.api.types.is_datetime64_any_dtype(df[f]):
            raise HTTPException(status_code=400, detail=f"'{f}' cannot be used: date-like columns are not supported in regression.")
            
        num_unique = df[f].nunique()
        total_rows = len(df)
        if 'id' in f.lower() or num_unique > total_rows * 0.5:
            raise HTTPException(status_code=400, detail=f"'{f}' cannot be used: identifier-like column ({num_unique} distinct values in {total_rows} rows).")
            
        if not pd.api.types.is_numeric_dtype(df[f]) and num_unique > 20:
            raise HTTPException(status_code=400, detail=f"'{f}' cannot be used: categorical column with >20 distinct values ({num_unique}).")
            
    # Select subset and drop nulls
    cols = [req.target] + req.features
    df_sub = df[cols].dropna()
    
    if len(df_sub) < 20:
        raise HTTPException(status_code=400, detail="Not enough data: must have >= 20 rows after dropping nulls")
        
    X = df_sub[req.features]
    y = df_sub[req.target]
    
    # One-hot encode categoricals
    cat_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
    for col in cat_cols:
        if X[col].nunique() > 20:
            raise HTTPException(status_code=400, detail=f"Column '{col}' has >20 distinct values. Too many categories for one-hot encoding.")
            
    if cat_cols:
        X = pd.get_dummies(X, columns=cat_cols, drop_first=True)
        
    from sklearn.model_selection import train_test_split, KFold, cross_val_score
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.metrics import r2_score
    from scipy.stats import shapiro

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    r2_train = float(r2_score(y_train, y_pred_train))
    r2_test = float(r2_score(y_test, y_pred_test))

    coefficients = []
    for feature_name, coef in zip(X.columns, model.coef_):
        coefficients.append({"feature": feature_name, "value": float(coef)})

    intercept = float(model.intercept_)
    n_rows_used = len(df_sub)

    # Sample predictions for scatter
    predictions_sample = []
    sample_size = min(100, len(y_test))

    y_test_sample = y_test.head(sample_size)
    y_pred_test_sample = y_pred_test[:sample_size]

    for act, pred in zip(y_test_sample, y_pred_test_sample):
        predictions_sample.append({"actual": float(act), "predicted": float(pred)})

    # ── K-fold cross-validation (a single 80/20 split is a noisy accuracy
    # estimate on small datasets; averaging over folds is more robust) ──
    cross_validation = None
    try:
        n_folds = min(5, len(df_sub) // 4)
        if n_folds >= 2:
            kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
            cv_scores = cross_val_score(LinearRegression(), X, y, cv=kf, scoring='r2')
            cross_validation = {
                "folds": n_folds,
                "r2_mean": float(np.mean(cv_scores)),
                "r2_std": float(np.std(cv_scores)),
                "r2_per_fold": [float(s) for s in cv_scores]
            }
    except Exception:
        cross_validation = None

    # ── Multicollinearity (VIF) — high VIF means a feature is largely
    # explained by the other features, which makes its coefficient unstable
    # and hard to interpret even if overall model R² looks fine ──
    multicollinearity = []
    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        X_vif = X.astype(float).copy()
        X_vif.insert(0, "_intercept", 1.0)
        for i, col in enumerate(X.columns):
            try:
                vif_val = float(variance_inflation_factor(X_vif.values, i + 1))
            except Exception:
                vif_val = None
            multicollinearity.append({
                "feature": col,
                "vif": vif_val,
                "concern": vif_val is not None and vif_val > 10 and np.isfinite(vif_val)
            })
    except Exception:
        multicollinearity = []

    # ── Residual normality (Shapiro-Wilk) — OLS coefficient significance/
    # confidence intervals assume roughly normal residuals; this flags when
    # that assumption doesn't hold instead of asserting it silently ──
    residual_normality = None
    try:
        residuals = (y_test - y_pred_test) if len(y_test) >= 3 else (y_train - y_pred_train)
        if len(residuals) >= 3:
            stat, p_val = shapiro(residuals)
            residual_normality = {
                "statistic": float(stat),
                "p_value": float(p_val),
                "is_normal": bool(p_val > 0.05),
                "sample": "test" if len(y_test) >= 3 else "train"
            }
    except Exception:
        residual_normality = None

    # ── Regularization comparison — Ridge/Lasso vs. plain OLS. The primary
    # returned model/coefficients stay OLS (unchanged, backward compatible);
    # this just shows whether regularization would help, which matters most
    # when multicollinearity above is flagged ──
    regularized_comparison = {}
    for name, reg_model in (("ridge", Ridge(alpha=1.0)), ("lasso", Lasso(alpha=1.0, max_iter=5000))):
        try:
            reg_model.fit(X_train, y_train)
            regularized_comparison[name] = {
                "r2_test": float(r2_score(y_test, reg_model.predict(X_test)))
            }
        except Exception:
            regularized_comparison[name] = None

    # Save to db
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO regression_models (dataset_id, target, features, r2_train, r2_test, coefficients, intercept, n_rows_used, timestamp, user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        dataset_info["id"],
        req.target,
        json.dumps(req.features),
        r2_train,
        r2_test,
        json.dumps(coefficients),
        intercept,
        n_rows_used,
        datetime.now().isoformat(),
        current_user["id"]
    ))
    conn.commit()
    conn.close()
    
    return {
        "r2_train": r2_train,
        "r2_test": r2_test,
        "coefficients": coefficients,
        "intercept": intercept,
        "predictions_sample": predictions_sample,
        "n_rows_used": n_rows_used,
        "cross_validation": cross_validation,
        "multicollinearity": multicollinearity,
        "residual_normality": residual_normality,
        "regularized_comparison": regularized_comparison
    }

@router.get("/models")
async def get_regression_models(current_user: dict = Depends(get_current_user)):
    dataset_info = get_active_dataset(current_user["id"])
    if not dataset_info:
        return []
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, target, features, r2_train, r2_test, coefficients, intercept, n_rows_used, timestamp
        FROM regression_models
        WHERE dataset_id = %s AND user_id = %s
        ORDER BY timestamp DESC
    ''', (dataset_info["id"], current_user["id"]))
    rows = cursor.fetchall()
    conn.close()
    
    models = []
    for r in rows:
        models.append({
            "id": r[0],
            "target": r[1],
            "features": r[2] if isinstance(r[2], (dict, list)) else json.loads(r[2]),
            "r2_train": r[3],
            "r2_test": r[4],
            "coefficients": r[5] if isinstance(r[5], (dict, list)) else json.loads(r[5]),
            "intercept": r[6],
            "n_rows_used": r[7],
            "timestamp": r[8]
        })
    return models
