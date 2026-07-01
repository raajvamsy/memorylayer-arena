FROM node:22-bookworm-slim

# Native addons (tree-sitter, better-sqlite3, hnswlib) need a C++ toolchain.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip make g++ ca-certificates curl \
  && ln -sf /usr/bin/python3 /usr/bin/python \
  && rm -rf /var/lib/apt/lists/*

RUN npm install -g @raajvamsy/memorylayer --ignore-scripts

# Rebuild native addons; tree-sitter-markdown alone needs -fexceptions (uses C++ throw/catch).
RUN ML=/usr/local/lib/node_modules/@raajvamsy/memorylayer && \
    cd "$ML" && \
    npm rebuild better-sqlite3 hnswlib-node tree-sitter tree-sitter-css \
      tree-sitter-gdscript tree-sitter-go tree-sitter-groovy tree-sitter-html \
      tree-sitter-java tree-sitter-javascript tree-sitter-kotlin tree-sitter-python \
      tree-sitter-ruby tree-sitter-rust tree-sitter-swift tree-sitter-typescript && \
    cd "$ML/node_modules/tree-sitter-markdown" && CXXFLAGS="-fexceptions" npm rebuild && \
    node "$ML/scripts/postinstall.mjs"

# Pre-download the embedding model (~130MB) so deploy binds PORT in seconds, not minutes.
RUN mkdir -p /tmp/warmup && \
    memorylayer start --host 127.0.0.1 --port 8765 --data /tmp/warmup >/tmp/warmup.log 2>&1 & \
    SPID=$!; \
    for i in $(seq 1 180); do curl -sf http://127.0.0.1:8765/health >/dev/null && break; sleep 1; done; \
    kill $SPID 2>/dev/null; wait $SPID 2>/dev/null || true; \
    rm -rf /tmp/warmup

ENV NODE_ENV=production \
    MEMORY_HOST=0.0.0.0 \
    MEMORY_DATA_DIR=/data

RUN mkdir -p /data

EXPOSE 8080

CMD ["sh", "-c", "memorylayer start --host 0.0.0.0 --port ${PORT:-8080} --data /data"]
