import requests
import json
import time

base_url = "http://localhost:8000/api/v1"

# 1. Login or create user
def get_token(email, password, full_name):
    # try login
    r = requests.post(f"{base_url}/auth/login", data={"username": email, "password": password})
    if r.status_code == 200:
        return r.json()["access_token"]
    # register
    r = requests.post(f"{base_url}/auth/register", json={"email": email, "password": password, "full_name": full_name})
    if r.status_code == 200:
        # login
        r = requests.post(f"{base_url}/auth/login", data={"username": email, "password": password})
        return r.json()["access_token"]
    raise Exception(f"Auth failed: {r.text}")

try:
    token_a = get_token("usera@test.com", "pass123", "User A")
    token_b = get_token("userb@test.com", "pass123", "User B")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    print("Tokens acquired")

    # Step 1: Upload a dataset
    file_content = b"col1,col2\n1,2\n3,4"
    files = {"file": ("test1.csv", file_content)}
    r1 = requests.post(f"{base_url}/datasets/upload", files=files, headers=headers_a)
    print("Upload 1:", r1.status_code, r1.text)
    assert r1.status_code == 200

    time.sleep(2) # wait for process
    
    # Step 1 cont: Upload EXACT SAME FILE
    files = {"file": ("test1.csv", file_content)}
    r2 = requests.post(f"{base_url}/datasets/upload", files=files, headers=headers_a)
    print("Upload 2 (duplicate):", r2.status_code, r2.text)
    assert r2.status_code == 409
    assert "duplicate" in r2.json()["detail"]

    # Step 2: Upload Anyway (force=true)
    r3 = requests.post(f"{base_url}/datasets/upload", files=files, headers=headers_a, data={"force": "true"})
    print("Upload 3 (force):", r3.status_code, r3.text)
    assert r3.status_code == 200

    # Step 3: Same content, different filename
    files = {"file": ("test2.csv", file_content)}
    r4 = requests.post(f"{base_url}/datasets/upload", files=files, headers=headers_a)
    print("Upload 4 (diff name):", r4.status_code, r4.text)
    assert r4.status_code == 409

    # Step 4: Modified content, same filename
    mod_content = b"col1,col2\n1,2\n3,4\n5,6"
    files = {"file": ("test1.csv", mod_content)}
    r5 = requests.post(f"{base_url}/datasets/upload", files=files, headers=headers_a)
    print("Upload 5 (mod content):", r5.status_code, r5.text)
    assert r5.status_code == 200

    # Step 5: A/B isolation (User B uploads User A's file)
    files = {"file": ("test_b.csv", file_content)}
    r6 = requests.post(f"{base_url}/datasets/upload", files=files, headers=headers_b)
    print("Upload 6 (isolation):", r6.status_code, r6.text)
    assert r6.status_code == 200

    print("All tests passed!")
except Exception as e:
    print("Test failed:", e)
