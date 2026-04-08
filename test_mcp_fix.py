"""Verify the fixed RAG MCP server responds to tool calls."""
import subprocess, json, sys, time, threading, os

proc = subprocess.Popen(
    [r"C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe", "src/rag_mcp/server.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    cwd=r"C:\Users\Admin\Documents\GitHub\ai_orchestrator",
    env={**os.environ, "PYTHONUNBUFFERED": "1"},
)

def read_stderr():
    for line in proc.stderr:
        print(f"  [STDERR] {line.decode().rstrip()}", flush=True)
threading.Thread(target=read_stderr, daemon=True).start()

def send(obj):
    proc.stdin.write((json.dumps(obj) + "\n").encode())
    proc.stdin.flush()

def recv(timeout=90):
    buf = b""
    start = time.time()
    while time.time() - start < timeout:
        ch = proc.stdout.read(1)
        if not ch:
            return None
        buf += ch
        if ch == b"\n":
            return json.loads(buf.decode().strip())
    return None

print("1. Initialize...", flush=True)
send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}})
r = recv(10)
print(f"   OK: {bool(r)}", flush=True)

send({"jsonrpc":"2.0","method":"notifications/initialized"})
time.sleep(0.5)

print("2. Calling rag_status (will wait for model load)...", flush=True)
t0 = time.time()
send({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"rag_status","arguments":{}}})
r = recv(90)
elapsed = time.time() - t0
if r:
    content = r.get("result", {}).get("content", [{}])[0].get("text", "")
    print(f"   OK in {elapsed:.1f}s: {content[:200]}", flush=True)
else:
    print(f"   FAILED: no response in {elapsed:.1f}s", flush=True)

print("3. Calling search_codebase (needs model)...", flush=True)
t0 = time.time()
send({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_codebase","arguments":{"query":"auth login","n_results":2}}})
r = recv(120)
elapsed = time.time() - t0
if r:
    content = r.get("result", {}).get("content", [{}])[0].get("text", "")
    print(f"   OK in {elapsed:.1f}s: {content[:150]}", flush=True)
else:
    print(f"   FAILED: no response in {elapsed:.1f}s", flush=True)

proc.terminate()
print("DONE", flush=True)
