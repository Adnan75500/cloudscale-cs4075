import sys
import threading
import time
import urllib.request

if len(sys.argv) < 2:
    print("Usage: python scripts/loadtest.py <URL> [DURATION_IN_SECONDS]")
    sys.exit(1)

url = sys.argv[1]
secs = int(sys.argv[2]) if len(sys.argv) > 2 else 600
workers = 40
end = time.time() + secs
completed_requests = 0
lock = threading.Lock()

print(f"Starting load test against: {url}")
print(f"Workers: {workers} concurrent threads")
print(f"Duration: {secs} seconds (~{secs // 60} minutes)")
print("Generating continuous CPU load to trigger ASG scale-out (TargetTracking CPU > 50%)...\n")

def work():
    global completed_requests
    while time.time() < end:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CloudScale-LoadTest/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp.read()
            with lock:
                completed_requests += 1
        except Exception:
            pass

threads = []
for _ in range(workers):
    t = threading.Thread(target=work)
    t.daemon = True
    t.start()
    threads.append(t)

start_time = time.time()
try:
    while time.time() < end:
        elapsed = int(time.time() - start_time)
        remaining = max(0, secs - elapsed)
        with lock:
            reqs = completed_requests
        rate = reqs / elapsed if elapsed > 0 else 0
        sys.stdout.write(f"\rElapsed: {elapsed}s | Remaining: {remaining}s | Requests sent: {reqs} ({rate:.1f} req/s) ")
        sys.stdout.flush()
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[!] Load test interrupted by user.")

print(f"\nLoad test completed! Total requests sent: {completed_requests}")

