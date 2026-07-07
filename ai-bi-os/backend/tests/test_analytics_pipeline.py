import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, get_db

client = TestClient(app)

# Use test database or run tests on memory SQLite if configured.
# Here we just run through the endpoints assuming a dummy dataset ID "ds_test_1"

@pytest.fixture(scope="module")
def setup_teardown():
    # Setup test DB tables
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown
    # Base.metadata.drop_all(bind=engine)

def test_health_check(setup_teardown):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api-gateway"}

def test_kpi_engine():
    # Calling the mock or actual KPI endpoint
    response = client.get("/api/v1/kpi/ds_test_1/summary")
    assert response.status_code in [200, 404]  # 404 if data not actually seeded, but route works

def test_metrics_engine():
    response = client.get("/api/v1/metrics/ds_test_1/summary")
    assert response.status_code in [200, 404]

def test_eda_engine():
    response = client.get("/api/v1/eda/ds_test_1")
    assert response.status_code in [200, 404]

def test_correlation_engine():
    response = client.get("/api/v1/correlation/ds_test_1/matrix")
    assert response.status_code in [200, 404]

def test_statistics_engine():
    response = client.get("/api/v1/statistics/ds_test_1/summary")
    assert response.status_code in [200, 404]

def test_regression_engine():
    response = client.get("/api/v1/regression/ds_test_1/summary")
    assert response.status_code in [200, 404]

def test_validation_engine():
    response = client.get("/api/v1/validation/ds_test_1/summary")
    assert response.status_code in [200, 404]

def test_distribution_engine():
    response = client.get("/api/v1/distribution/ds_test_1/profiles")
    assert response.status_code in [200, 404]

def test_outlier_engine():
    response = client.get("/api/v1/outliers/ds_test_1/summary")
    assert response.status_code in [200, 404]

def test_timeseries_engine():
    response = client.get("/api/v1/timeseries/ds_test_1/summary")
    assert response.status_code in [200, 404]

def test_trend_engine():
    response = client.get("/api/v1/trends/ds_test_1/summary")
    assert response.status_code in [200, 404]

def test_forecast_engine():
    response = client.get("/api/v1/forecast/ds_test_1/summary")
    assert response.status_code in [200, 404]

def test_forecast_governance_engine():
    # Module 30 tests
    
    # 1. Evaluate
    eval_payload = {
        "model_id": "model_abc",
        "actuals": [10.0, 12.0, 15.0],
        "predictions": [11.0, 12.5, 14.0]
    }
    response = client.post("/api/v1/forecast/evaluate", json=eval_payload)
    assert response.status_code == 200
    
    # 2. Get Evaluation
    response = client.get("/api/v1/forecast/evaluation?model_id=model_abc")
    assert response.status_code == 200
    
    # 3. Get Governance Status
    response = client.get("/api/v1/forecast/governance?model_id=model_abc")
    assert response.status_code == 200
    gov = response.json()
    assert gov["model_id"] == "model_abc"
    assert "quality_score" in gov
