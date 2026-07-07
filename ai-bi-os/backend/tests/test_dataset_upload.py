import pytest
import os
import pandas as pd
from fastapi.testclient import TestClient

# Mock CELERY so it runs synchronously for testing
from app.worker import celery_app
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True

from app.main import app
from app.core.database import Base, engine, get_db
from sqlalchemy.orm import sessionmaker

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_upload_small_dataset():
    # Create a small valid CSV
    test_csv = "test_upload.csv"
    pd.DataFrame({"A": [1, 2], "B": [3, 4]}).to_csv(test_csv, index=False)
    
    with open(test_csv, "rb") as f:
        response = client.post(
            "/api/v1/datasets/upload",
            data={"dataset_name": "Test Upload Dataset"},
            files={"file": ("test_upload.csv", f, "text/csv")}
        )
    
    os.remove(test_csv)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "job_id" in data
    
    job_id = data["job_id"]
    
    # Check status (should be completed since celery is eager)
    status_response = client.get(f"/api/v1/datasets/upload/status/{job_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["status"] == "completed"
    
def test_upload_invalid_extension():
    test_txt = "test_upload.txt"
    with open(test_txt, "w") as f:
        f.write("hello world")
        
    with open(test_txt, "rb") as f:
        response = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("test_upload.txt", f, "text/plain")}
        )
    os.remove(test_txt)
    
    # In an eager celery setup, the exception will bubble up during the POST 
    # if it's not caught by the router. 
    # Wait, the router returns HTTP 500 when celery raises an error if eager? 
    # Actually, process_upload_task catches the exception and marks the job as failed!
    assert response.status_code == 200
    data = response.json()
    job_id = data["job_id"]
    
    status_response = client.get(f"/api/v1/datasets/upload/status/{job_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["status"] == "failed"
    assert "Unsupported file extension" in status_data["error_message"]
