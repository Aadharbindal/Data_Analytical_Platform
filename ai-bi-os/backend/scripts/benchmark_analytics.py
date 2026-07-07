import asyncio
import httpx
import time
import pandas as pd

API_URL = "http://localhost:8000/api/v1"
DATASET_ID = "benchmark_ds_1"

ENDPOINTS = [
    f"/kpi/{DATASET_ID}/summary",
    f"/metrics/{DATASET_ID}/summary",
    f"/eda/{DATASET_ID}",
    f"/correlation/{DATASET_ID}/matrix",
    f"/statistics/{DATASET_ID}/summary",
    f"/regression/{DATASET_ID}/summary",
    f"/validation/{DATASET_ID}/summary",
    f"/distribution/{DATASET_ID}/profiles",
    f"/outliers/{DATASET_ID}/summary",
    f"/timeseries/{DATASET_ID}/summary",
    f"/trends/{DATASET_ID}/summary",
    f"/forecast/{DATASET_ID}/summary",
    f"/forecast/governance?model_id={DATASET_ID}",
]

async def benchmark_endpoint(client, endpoint, num_requests=10):
    start_time = time.time()
    errors = 0
    for _ in range(num_requests):
        try:
            response = await client.get(f"{API_URL}{endpoint}")
            # we don't assert 200 here because mock dataset might return 404, we just measure latency
            if response.status_code >= 500:
                errors += 1
        except Exception:
            errors += 1
    duration = time.time() - start_time
    return {
        "endpoint": endpoint,
        "total_requests": num_requests,
        "errors": errors,
        "avg_latency_ms": (duration / num_requests) * 1000,
        "throughput_req_sec": num_requests / duration if duration > 0 else 0
    }

async def main():
    print(f"Starting benchmark on {API_URL}...")
    results = []
    async with httpx.AsyncClient() as client:
        # For this test, we do 10 requests per endpoint
        for endpoint in ENDPOINTS:
            res = await benchmark_endpoint(client, endpoint, num_requests=10)
            results.append(res)
            print(f"Completed {endpoint}: {res['avg_latency_ms']:.2f} ms/req")

    df = pd.DataFrame(results)
    df.to_csv("benchmark_results.csv", index=False)
    print("\nBenchmark complete. Results saved to benchmark_results.csv")
    print(df.to_string())

if __name__ == "__main__":
    asyncio.run(main())
