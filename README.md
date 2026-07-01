# memorylayer-arena

Docker deployment for the **MemoryLayer Trust Arena** demo engine.

The [Trust Arena](https://memorylayer.in/arena) on Vercel calls this service over HTTP (`/mcp`) for `recall`, `remember`, and `verify`. This repo contains **no application code** — only deploy config that installs the published [`@raajvamsy/memorylayer`](https://www.npmjs.com/package/@raajvamsy/memorylayer) npm package and runs it.

## Why a separate repo?

The main [MemoryLayer](https://github.com/raajvamsy/MemoryLayer) monorepo pins Node via `node/package.json`, which caused Render to pick **Node 26** and fail native module builds. This repo deploys via **Docker** (`node:22-bookworm-slim` + build toolchain) so `tree-sitter` and other native addons compile reliably.

## Deploy on Modal (recommended — scale to zero)

Modal only bills while the container is running. Arena wakes the engine on **first Ask click**, then shuts down after idle (`scaledown_window`, default 2 min). Starter plan includes **$30/mo free compute** — plenty for a public demo.

### 1. Install & authenticate

```bash
pip install -r requirements-modal.txt
modal setup   # opens browser for rraajvamsy workspace
```

### 2. Store your API key as a Modal secret

```bash
modal secret create memorylayer-arena MEMORY_API_KEY=sk-ml-YOUR-KEY
```

### 3. Deploy

```bash
modal deploy modal_app.py
```

Modal prints a URL like:

```
https://rraajvamsy--memorylayer-arena-engine.modal.run
```

### 4. Wire Vercel

```
MEMORYLAYER_DEMO_URL=https://rraajvamsy--memorylayer-arena-engine.modal.run
MEMORYLAYER_DEMO_KEY=sk-ml-YOUR-KEY
```

### Cost estimate (Starter, $30 credits)

| Resource | Rate | Typical Arena session |
|----------|------|----------------------|
| 2 CPU cores | ~$0.000026/s | ~2 min active ≈ **$0.003** |
| 4 GiB RAM | ~$0.000009/s | included above |
| Idle after last request | `scaledown_window=120` | ~2 min tail, then **$0** |

~100 demo sessions/day ≈ **$9/mo** worst case — well inside $30 free credits for moderate traffic.

Tune shutdown delay:

```bash
MODAL_SCALEDOWN_WINDOW=60 modal deploy modal_app.py   # stop 1 min after last hit
```

### Smoke test

```bash
BASE=https://rraajvamsy--memorylayer-arena-engine.modal.run
KEY=sk-ml-YOUR-KEY

curl -X POST "$BASE/mcp" \
  -H "Content-Type: application/json" -H "x-api-key: $KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

First request after idle may take **30–90s** (cold container). Subsequent requests in the same session are fast.

---

## Deploy on Render (Free tier — fallback)

Render free tier spins down after ~15 min idle and is slower / less reliable for multi-doc ingest. Use Modal if you have credits.

### Option A — Blueprint

1. Render Dashboard → **New** → **Blueprint**.
2. Connect `raajvamsy/memorylayer-arena`.
3. Set `MEMORY_API_KEY` when prompted.
4. Deploy from `Dockerfile` (`render.yaml`).

### Option B — Manual Web Service

| Field | Value |
|-------|-------|
| **Runtime** | **Docker** |
| **Dockerfile Path** | `./Dockerfile` |
| **Health Check Path** | *(leave blank — see note below)* |
| **Instance Type** | Free |

Environment: `MEMORY_API_KEY`, `MEMORY_HOST=0.0.0.0`, `MEMORY_DATA_DIR=/data`

**Health check:** Leave blank for `@raajvamsy/memorylayer@1.3.4` — `GET /health` returns 401 when `MEMORY_API_KEY` is set.

## Notes

- **Embedding model** (~130MB) is pre-cached in the Docker image build.
- **Arena data is ephemeral** — each visitor uploads fresh docs per session; no persistent volume needed.
- **License quota** — public demo traffic counts against your API key's plan limits.
