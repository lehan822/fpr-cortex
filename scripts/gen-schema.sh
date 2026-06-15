#!/usr/bin/env bash
set -euo pipefail

# gen-schema.sh — Scan fprtool-backend + exposed-ops.yaml → generate schemas
#
# Usage:
#   ./scripts/gen-schema.sh
#
# Flow:
#   1. Run gen-schema.py (reads exposed-ops.yaml + fprtool-backend source)
#   2. Output to infra/schemas/{domain}/{domain}.json
#   3. Commit & push → CI deploys to S3 automatically
#
# Prerequisites:
#   - Python 3 + pyyaml (pip install pyyaml)
#   - fpr-fprtool-backend cloned alongside this repo (optional, for CRUD scanning)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Determine backend path (optional)
BACKEND_PATH="${ROOT}/../fpr-fprtool-backend"
BACKEND_FLAG=""
if [[ -d "$BACKEND_PATH" ]]; then
    BACKEND_FLAG="--backend-path $BACKEND_PATH"
    echo "📦 Backend found: $BACKEND_PATH"
else
    echo "⚠️  Backend not found — CRUD ops will have minimal metadata"
fi

# Generate schemas
echo "🔧 Generating schemas from exposed-ops.yaml..."
cd "$ROOT"
python3 infra/scripts/gen-schema.py $BACKEND_FLAG --output-dir infra/schemas

echo ""
echo "✅ Done. Next steps:"
echo "   git add infra/schemas/ && git commit && git push"
echo "   → CI will deploy to S3 automatically"
