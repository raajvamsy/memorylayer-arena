FROM node:22-bookworm-slim

# Native addons (tree-sitter, better-sqlite3, hnswlib) need a C++ toolchain.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 make g++ ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN npm install -g @raajvamsy/memorylayer

ENV NODE_ENV=production \
    MEMORY_HOST=0.0.0.0 \
    MEMORY_DATA_DIR=/data

RUN mkdir -p /data

EXPOSE 8080

CMD ["sh", "-c", "memorylayer start --host 0.0.0.0 --port ${PORT:-8080} --data /data"]
