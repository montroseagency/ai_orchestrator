"""Test if threads actually run inside a subprocess."""
import subprocess, sys, os, time

code = '''
import sys, threading, time, concurrent.futures

print("[main] PID:", __import__("os").getpid(), file=sys.stderr, flush=True)

def worker():
    print("[thread] Starting!", file=sys.stderr, flush=True)
    time.sleep(2)
    print("[thread] Done!", file=sys.stderr, flush=True)

# Test 1: plain thread
t = threading.Thread(target=worker, daemon=True)
t.start()
print("[main] Thread started, active threads:", threading.active_count(), file=sys.stderr, flush=True)

# Test 2: ThreadPoolExecutor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
fut = executor.submit(lambda: print("[executor] Running!", file=sys.stderr, flush=True))
print("[main] Future submitted", file=sys.stderr, flush=True)

# Keep alive for 5s
time.sleep(5)
print("[main] Exiting", file=sys.stderr, flush=True)
'''

proc = subprocess.Popen(
    [r"C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe", "-c", code],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    env={**os.environ, "PYTHONUNBUFFERED": "1"},
)
out, err = proc.communicate(timeout=15)
print("STDOUT:", out.decode())
print("STDERR:", err.decode())
