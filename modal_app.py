"""
MemoryLayer Trust Arena — Modal deployment (scale-to-zero).

Runs the same Docker image as Render but only bills while handling requests.
Default: min_containers=0, scaledown_window=1800s (container stops ~30 min
after last hit — long enough that a demo session or return visit within that
window stays warm; see the SCALEDOWN_WINDOW comment below for why this isn't
shorter).

Deploy:
  pip install modal
  modal setup
  modal secret create memorylayer-arena MEMORY_API_KEY=sk-ml-...
  modal deploy modal_app.py

Then set on Vercel:
  MEMORYLAYER_DEMO_URL=https://<workspace>--memorylayer-arena-engine.modal.run
  MEMORYLAYER_DEMO_KEY=<same key>
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request

import modal

app = modal.App("memorylayer-arena")

# Node image has python3 for apt but not Modal's expected `python`+`pip` on PATH.
# add_python installs a compatible standalone Python for Modal's web_server wrapper.
image = modal.Image.from_dockerfile("Dockerfile", add_python="3.11")

# Tune via env when deploying, e.g.:
#   MODAL_SCALEDOWN_WINDOW=120 modal deploy modal_app.py
#
# Why 1800s (30min) by default: the Node HTTP server opens its port fast, well
# before the internal wcm child process (spaCy/sklearn import chain) has ever
# been touched — Modal's own readiness poll only waits on the port, not on wcm
# being warm, so a short scaledown window means most "return after a break"
# visits hit a container whose wcm process is STILL cold even though the
# container itself looks warm. A long window keeps wcm hot for realistic demo
# usage; the warm-up call below (best-effort, not a guarantee against Modal's
# poll-vs-function-return race) and the Arena's own raised fetch timeouts are
# the actual safety net for the unavoidable first-ever cold start.
SCALEDOWN_WINDOW = int(os.environ.get("MODAL_SCALEDOWN_WINDOW", "1800"))
STARTUP_TIMEOUT = int(os.environ.get("MODAL_STARTUP_TIMEOUT", "300"))


def _wait_for_health(base_url: str, timeout_s: int) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


def _warm_up_wcm(base_url: str, api_key: str, timeout_s: int) -> None:
    """Fire a real verify() call through the local HTTP server so the wcm
    child process's cold-start (spaCy import chain, measured 40-124s) happens
    during container boot instead of during a live user's first request."""
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "verify", "arguments": {"text": "A dog is an animal."}},
    }).encode()
    req = urllib.request.Request(
        f"{base_url}/mcp", data=body, method="POST",
        headers={"Content-Type": "application/json", "x-api-key": api_key},
    )
    try:
        start = time.time()
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            resp.read()
        print(f"[warmup] wcm warm-up call completed in {time.time() - start:.1f}s")
    except urllib.error.URLError as e:
        print(f"[warmup] wcm warm-up call failed (non-fatal, first real request will pay the cost): {e}")


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("memorylayer-arena")],
    cpu=2.0,
    memory=4096,
    min_containers=0,
    scaledown_window=SCALEDOWN_WINDOW,
    timeout=600,
)
@modal.concurrent(max_inputs=8)
@modal.web_server(port=8080, startup_timeout=STARTUP_TIMEOUT)
def engine():
    """Expose memorylayer's HTTP server (health + /mcp JSON-RPC)."""
    env = os.environ.copy()
    env.setdefault("MEMORY_HOST", "0.0.0.0")
    env.setdefault("MEMORY_DATA_DIR", "/data")
    env["PORT"] = "8080"
    os.makedirs(env["MEMORY_DATA_DIR"], exist_ok=True)
    subprocess.Popen(
        ["memorylayer", "start", "--host", "0.0.0.0", "--port", "8080", "--data", "/data"],
        env=env,
    )
    base_url = "http://127.0.0.1:8080"
    if _wait_for_health(base_url, timeout_s=60):
        _warm_up_wcm(base_url, env.get("MEMORY_API_KEY", ""), timeout_s=STARTUP_TIMEOUT - 60)
