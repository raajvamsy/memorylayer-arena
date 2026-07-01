# memorylayer-arena

Minimal [Render](https://render.com) deployment for the **MemoryLayer Trust Arena** demo engine.

The [Trust Arena](https://memorylayer.in/arena) on Vercel calls this service over HTTP (`/mcp`) for `recall`, `remember`, and `verify`. This repo contains **no application code** — only deploy config that installs the published [`@raajvamsy/memorylayer`](https://www.npmjs.com/package/@raajvamsy/memorylayer) npm package and runs it.

## Why a separate repo?

The main [MemoryLayer](https://github.com/raajvamsy/MemoryLayer) monorepo pins Node via `node/package.json`, which caused Render to pick **Node 26** and fail native module builds. This repo pins **Node 22 LTS** explicitly ([Render node version docs](https://render.com/docs/node-version)).

## Deploy on Render (Free tier)

### Option A — Blueprint (recommended)

1. Push this repo to GitHub.
2. Render Dashboard → **New** → **Blueprint**.
3. Connect `raajvamsy/memorylayer-arena`.
4. Set `MEMORY_API_KEY` when prompted (`sk-ml-...` from [memorylayer.in/dashboard](https://memorylayer.in/dashboard)).
5. Deploy.

### Option B — Manual Web Service

1. Render Dashboard → **New** → **Web Service**.
2. Connect `raajvamsy/memorylayer-arena`, branch `main`.
3. Settings:

| Field | Value |
|-------|-------|
| **Runtime** | Node |
| **Build Command** | `npm install -g @raajvamsy/memorylayer` |
| **Start Command** | `memorylayer start --host 0.0.0.0 --port $PORT --data /data` |
| **Health Check Path** | `/health` |
| **Instance Type** | Free |

4. Environment variables:

| Key | Value |
|-----|-------|
| `MEMORY_API_KEY` | your `sk-ml-...` key |
| `MEMORY_HOST` | `0.0.0.0` |
| `MEMORY_DATA_DIR` | `/data` |

Node version is pinned by `.node-version` (`22.14.0`) — do **not** connect the MemoryLayer monorepo here.

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
