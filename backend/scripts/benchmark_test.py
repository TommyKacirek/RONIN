import time
import requests
import statistics
import concurrent.futures

API_URL = "http://127.0.0.1:8000/api/portfolio"

def measure_request():
    start = time.time()
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        latency = time.time() - start
        return latency, response.status_code
    except Exception as e:
        return time.time() - start, str(e)

def benchmark(n_requests=10, concurrency=1):
    print(f"Starting benchmark: {n_requests} requests, concurrency={concurrency}...")
    latencies = []
    errors = 0
    
    start_total = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(measure_request) for _ in range(n_requests)]
        for future in concurrent.futures.as_completed(futures):
            lat, status = future.result()
            if isinstance(status, str) and not status.isdigit(): # Error msg
                errors += 1
                print(f"Error: {status}")
            else:
                latencies.append(lat)
                
    total_time = time.time() - start_total
    
    if not latencies:
        print("No successful requests.")
        return

    print("\n--- Results ---")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Requests: {n_requests}")
    print(f"Concurrency: {concurrency}")
    print(f"Errors: {errors}")
    print(f"Avg Latency: {statistics.mean(latencies):.4f}s")
    print(f"Median Latency: {statistics.median(latencies):.4f}s")
    print(f"Min Latency: {min(latencies):.4f}s")
    print(f"Max Latency: {max(latencies):.4f}s")
    print(f"Requests/sec: {n_requests / total_time:.2f}")

if __name__ == "__main__":
    # Warmup
    print("Warming up...")
    measure_request()
    
    # Baseline Test 1: Sequential
    benchmark(n_requests=5, concurrency=1)
    
    # Baseline Test 2: Concurrent (Simulate multiple users/tabs)
    # benchmark(n_requests=10, concurrency=5)
