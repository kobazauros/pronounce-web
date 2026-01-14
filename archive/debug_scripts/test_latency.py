import time
import requests
import statistics


def measure_latency(url, name, num_requests=5):
    print(f"\nTesting {name} ({url})...")
    latencies = []

    # Warm-up request
    try:
        requests.get(url)
    except Exception as e:
        print(f"  Warm-up failed: {e}")
        return

    for i in range(num_requests):
        try:
            start = time.time()
            response = requests.get(url)
            end = time.time()

            latency = (end - start) * 1000
            latencies.append(latency)
            print(f"  Request {i+1}: {latency:.2f} ms (Status: {response.status_code})")
        except Exception as e:
            print(f"  Request {i+1} failed: {e}")

    if latencies:
        avg = statistics.mean(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        print(f"  --- Stats ---")
        print(f"  Average: {avg:.2f} ms")
        print(f"  Min: {min_lat:.2f} ms")
        print(f"  Max: {max_lat:.2f} ms")


if __name__ == "__main__":
    local_url = "http://127.0.0.1:5000/"
    ngrok_url = "https://unaudaciously-vivacious-jaelynn.ngrok-free.dev/"

    print("=== PronounceWeb Latency Test ===")
    measure_latency(local_url, "Localhost (Direct)")
    measure_latency(ngrok_url, "Ngrok (Tunnel via Internet)")
