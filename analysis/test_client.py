import asyncio
import aiohttp
import json
import requests
import time
from collections import Counter

BASE_URL = "http://localhost:5000"

async def fetch_home(session, sem):
    async with sem:
        try:
            async with session.get(f"{BASE_URL}/home", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("message", "Unknown")
                return f"Error_{response.status}"
        except Exception as e:
            return f"Exception_{type(e).__name__}"

async def send_async_requests(total_requests=10000, concurrency=50):
    sem = asyncio.Semaphore(concurrency)
    timeout = aiohttp.ClientTimeout(total=10)
    connector = aiohttp.TCPConnector(limit=concurrency, force_close=False, enable_cleanup_closed=True)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [fetch_home(session, sem) for _ in range(total_requests)]
        results = await asyncio.gather(*tasks)
    return Counter(results)

def run_experiment_a1():
    print("\n--- Running Experiment A-1 (10,000 Requests on N=3) ---")
    counts = asyncio.run(send_async_requests(total_requests=10000, concurrency=50))
    print("A-1 Distribution:", dict(counts))
    with open("a1_results.json", "w") as f:
        json.dump(counts, f, indent=2)

def run_experiment_a2():
    print("\n--- Running Experiment A-2 (Scaling N from 2 to 6) ---")
    avg_loads = {}
    
    # Scale/reset to N=2
    rep_info = requests.get(f"{BASE_URL}/rep").json()["message"]
    current_replicas = rep_info["replicas"]
    if len(current_replicas) > 2:
        rem_count = len(current_replicas) - 2
        requests.delete(f"{BASE_URL}/rm", json={"n": rem_count, "hostnames": current_replicas[:rem_count]})
    elif len(current_replicas) < 2:
        requests.post(f"{BASE_URL}/add", json={"n": 2 - len(current_replicas), "hostnames": []})
    
    time.sleep(2)

    for n in range(2, 7):
        current_n = requests.get(f"{BASE_URL}/rep").json()["message"]["N"]
        if current_n < n:
            requests.post(f"{BASE_URL}/add", json={"n": n - current_n, "hostnames": []})
        time.sleep(2)
        
        print(f"Testing with N = {n}...")
        counts = asyncio.run(send_async_requests(total_requests=10000, concurrency=50))
        valid_counts = [v for k, v in counts.items() if "Hello from" in k]
        avg_load = sum(valid_counts) / n if n > 0 else 0
        avg_loads[n] = {
            "average_load": avg_load,
            "distribution": dict(counts)
        }
        print(f"N={n} Average Load: {avg_load}")

    with open("a2_results.json", "w") as f:
        json.dump(avg_loads, f, indent=2)

def run_experiment_a3():
    print("\n--- Running Experiment A-3 (Fault Recovery Verification) ---")
    rep_res = requests.get(f"{BASE_URL}/rep").json()["message"]
    active_replicas = rep_res["replicas"]
    target = active_replicas[0]
    print(f"Initial Replicas: {active_replicas}")
    print(f"Stopping container: {target}...")
    
    import os
    os.system(f"docker stop {target}")
    
    print("Waiting 4 seconds for load balancer heartbeat detector...")
    time.sleep(4)
    
    new_rep_res = requests.get(f"{BASE_URL}/rep").json()["message"]
    print(f"Replicas after recovery: {new_rep_res['replicas']}")
    is_replaced = target not in new_rep_res['replicas']
    print(f"Target {target} replaced successfully: {is_replaced}")

if __name__ == '__main__':
    run_experiment_a1()
    run_experiment_a2()
    run_experiment_a3()