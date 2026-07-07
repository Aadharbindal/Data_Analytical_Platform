from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_catalog_endpoint():
    response = client.get("/api/v1/catalog")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"Catalog entries found: {len(data)}")

def test_insights_endpoint():
    # Pass dataset_version_id if needed, but the endpoint takes it optionally
    response = client.get("/api/v1/insights")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"Insights found: {len(data)}")

def test_recommendations_endpoint():
    response = client.get("/api/v1/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"Recommendations found: {len(data)}")

if __name__ == "__main__":
    print("Testing Catalog Integration...")
    test_catalog_endpoint()
    
    print("\nTesting Insights Integration...")
    test_insights_endpoint()
    
    print("\nTesting Recommendations Integration...")
    test_recommendations_endpoint()
    
    print("\nAll integration tests passed successfully.")
