#!/usr/bin/env bash
# Builds the Cloudflare artifact: static assets in dist/, worker bundle in build/.
# Deploy with: npx wrangler deploy
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf dist build
cp -r site dist
mkdir -p dist/data && cp data/corpus.json dist/data/corpus.json
mkdir -p build

npx --yes esbuild cloudflare/worker.mjs \
  --bundle --format=esm \
  --outfile=build/worker.js --log-level=warning

echo "assets: $(du -sh dist | cut -f1) ($(find dist -type f | wc -l) dosya), worker: $(du -h build/worker.js | cut -f1)"
