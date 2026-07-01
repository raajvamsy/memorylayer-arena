# memorylayer-arena

Minimal [Render](https://render.com) deployment for the **MemoryLayer Trust Arena** demo engine.

The [Trust Arena](https://memorylayer.in/arena) on Vercel calls this service over HTTP (`/mcp`) for `recall`, `remember`, and `verify`. This repo contains **no application code** — only deploy config that installs the published [`@raajvamsy/memorylayer`](https://www.npmjs.com/package/@raajvamsy/memorylayer) npm package and runs it.

## Why a separate repo?

The main [MemoryLayer](https://github.com/raajvamsy/MemoryLayer) monorepo pins Node via `node/package.json`, which caused Render to pick **Node 26** and fail native module builds. This repo deploys via **Docker** (`node:22-bookworm-slim` + build toolchain) so `tree-sitter` and other native addons compile reliably.

## Deploy on Render (Free tier)

### Option A — Blueprint (recommended)

1. Render Dashboard → **New** → **Blueprint** (or **Generate Blueprint** from project menu).
2. Connect `raajvamsy/memorylayer-arena`.
3. Set `MEMORY_API_KEY` when prompted (`sk-ml-...` from [memorylayer.in/dashboard](https://memorylayer.in/dashboard)).
4. Deploy. Render builds from `Dockerfile` (`runtime: docker` in `render.yaml`).

### Option B — Manual Web Service

1. Render Dashboard → **New** → **Web Service**.
2. Connect `raajvamsy/memorylayer-arena`, branch `main`.
3. Settings:

| Field | Value |
|-------|-------|
| **Language / Runtime** | **Docker** (not Node) |
| **Dockerfile Path** | `./Dockerfile` |
| **Health Check Path** | *(leave blank for now — see note below)* |
| **Instance Type** | Free |

4. Environment variables:

| Key | Value |
|-----|-------|
| `MEMORY_API_KEY` | your `sk-ml-...` key |
| `MEMORY_HOST` | `0.0.0.0` |
| `MEMORY_DATA_DIR` | `/data` |

Do **not** use Render's Native Node runtime — it lacks the C++ toolchain and fails on `tree-sitter-markdown`. Do **not** connect the MemoryLayer monorepo here.

The `Dockerfile` installs via `--ignore-scripts`, rebuilds native addons, then compiles `tree-sitter-markdown` with `CXXFLAGS=-fexceptions`. It also **pre-downloads the embedding model** during the image build so deploy startup binds `PORT` in seconds. Full image build takes ~3–5 minutes on Render.

**Health check:** Leave **Health Check Path** blank in Render settings for `@raajvamsy/memorylayer@1.3.4` — with `MEMORY_API_KEY` set, `GET /health` returns 401 on `0.0.0.0`, and Render never marks the deploy live. After a future npm release with the `/health` auth fix, set it back to `/health`.

## Wire Vercel

After deploy, set on the `web` Vercel project:

```
MEMORYLAYER_DEMO_URL=https://YOUR-SERVICE.onrender.com
MEMORYLAYER_DEMO_KEY=sk-ml-your-key   # same as MEMORY_API_KEY
```

## Smoke test

```bash
curl https://YOUR-SERVICE.onrender.com/health

curl -X POST https://YOUR-SERVICE.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-ml-YOUR-KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"remember","arguments":{"content":"Hello arena","namespace":"smoke","tags":["test"]}}}'
```

## Notes

- **First boot** downloads the embedding model (~130MB) + WCM binary from [memorylayer-releases](https://github.com/raajvamsy/memorylayer-releases). Allow 5–15 minutes.
- **Free tier** spins down after ~15 min idle; first request after sleep is slow.
- **Data is ephemeral** on Free (no persistent disk). Fine for Arena — each visitor uploads fresh docs per session.
- **License quota** — public demo traffic counts against your API key's plan limits.
