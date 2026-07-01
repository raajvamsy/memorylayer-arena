FROM node:22-bookworm-slim

# Native addons (tree-sitter, better-sqlite3, hnswlib) need a C++ toolchain.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 make g++ ca-certificates \
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

ENV NODE_ENV=production \
    MEMORY_HOST=0.0.0.0 \
    MEMORY_DATA_DIR=/data

RUN mkdir -p /data

EXPOSE 8080

CMD ["sh", "-c", "memorylayer start --host 0.0.0.0 --port ${PORT:-8080} --data /data"]
