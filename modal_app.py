"""
MemoryLayer Trust Arena — Modal deployment (scale-to-zero).

Runs the same Docker image as Render but only bills while handling requests.
Default: min_containers=0, scaledown_window=120s (container stops ~2 min after last hit).

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

import os
import subprocess

import modal

app = modal.App("memorylayer-arena")

# Reuses the Render Dockerfile (Node 22, native rebuilds, embedding pre-cache).
image = modal.Image.from_dockerfile("Dockerfile")

# Tune via env when deploying, e.g.:
#   MODAL_SCALEDOWN_WINDOW=120 modal deploy modal_app.py
SCALEDOWN_WINDOW = int(os.environ.get("MODAL_SCALEDOWN_WINDOW", "120"))
STARTUP_TIMEOUT = int(os.environ.get("MODAL_STARTUP_TIMEOUT", "300"))


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
