import pytest
from app.services.forecast.forecast_validator import forecast_validator
from app.services.forecast.forecast_model_selector import forecast_model_selector
from app.services.forecast.forecast_planner import forecast_planner

def test_forecast_validator():
    """Ensure stationarity checks work."""
    
    meta = {"is_stationary": False, "total_observations": 150}
    res = forecast_validator.validate_series(meta)
    
    stat = next(c for c in res if c["check_name"] == "STATIONARITY")
    assert stat["passed"] is False

def test_forecast_model_selector():
    """Ensure minimum AIC/RMSE wins."""
    
    cands = [
        {"model_name": "ARIMA", "aic": 100.0, "rmse": 5.0},
        {"model_name": "HOLT_WINTERS", "aic": 50.0, "rmse": 2.0},
    ]
    
    res = forecast_model_selector.select_best_model(cands)
    assert res["model_name"] == "HOLT_WINTERS"

def test_forecast_planner():
    """Ensure baseline generation scales properly."""
    
    base = [{"timestamp": "2023-01-01T00:00:00Z", "expected_value": 100.0}]
    scens = forecast_planner.generate_scenarios(base)
    
    opt = next(s for s in scens if s["scenario_type"] == "OPTIMISTIC")
    con = next(s for s in scens if s["scenario_type"] == "CONSERVATIVE")
    
    assert opt["scenario_series"][0]["scenario_value"] == 115.0 # +15%
    assert con["scenario_series"][0]["scenario_value"] == 85.0  # -15%
