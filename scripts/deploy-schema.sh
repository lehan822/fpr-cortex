#!/usr/bin/env bash
set -euo pipefail

# deploy-schema.sh — Generate schemas locally + upload to S3
#
# Usage:
#   ./scripts/deploy-schema.sh          # gen + deploy to stg
#   ./scripts/deploy-schema.sh prod     # gen + deploy to prod
#   ./scripts/deploy-schema.sh --gen-only  # gen only, no upload
#
# Prerequisites:
#   - Python 3 + pyyaml (pip install pyyaml)
#   - AWS credentials: assume Engineer@tvlk-fpr-stg (or DeployerExt for prod)
#   - fpr-fprtool-backend cloned alongside this repo (optional, for CRUD scanning)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

STG_BUCKET="bedrock-agentcore-runtime-354767975881-ap-southeast-1-a1beixhzs"
PROD_BUCKET="bedrock-agentcore-runtime-348767535692-ap-southeast-1-837werwc9"
REGION="ap-southeast-1"

ENV="${1:-stg}"
GEN_ONLY=false

if [[ "$ENV" == "--gen-only" ]]; then
    GEN_ONLY=true
    ENV="stg"
fi

# Determine backend path (optional)
BACKEND_PATH="${ROOT}/../fpr-fprtool-backend"
BACKEND_FLAG=""
if [[ -d "$BACKEND_PATH" ]]; then
    BACKEND_FLAG="--backend-path $BACKEND_PATH"
    echo "📦 Backend found: $BACKEND_PATH"
else
    echo "⚠️  Backend not found — CRUD ops will have minimal metadata"
fi

# Step 1: Generate schemas
echo "🔧 Generating schemas from exposed-ops.yaml..."
cd "$ROOT"
python3 infra/scripts/gen-schema.py $BACKEND_FLAG --output-dir infra/schemas

echo ""

if [[ "$GEN_ONLY" == "true" ]]; then
    echo "✅ Generation complete (--gen-only, skipping S3 upload)"
    exit 0
fi

# Step 2: Upload to S3
if [[ "$ENV" == "prod" ]]; then
    BUCKET="$PROD_BUCKET"
    PROFILE="DeployerExt@tvlk-fpr-prod"
else
    BUCKET="$STG_BUCKET"
    PROFILE="DeployerExt@tvlk-fpr-stg"
fi

echo "📤 Uploading to S3 ($ENV)..."
echo "   Bucket: $BUCKET"
echo "   Profile: $PROFILE"
echo ""

for domain in pricing supply demand config; do
    SCHEMA_FILE="infra/schemas/$domain/$domain.json"
    if [[ -f "$SCHEMA_FILE" ]]; then
        aws s3 cp "$SCHEMA_FILE" "s3://$BUCKET/schemas/$domain.json" \
            --profile "$PROFILE" --region "$REGION" --quiet
        echo "  ✅ $domain.json → s3://$BUCKET/schemas/$domain.json"
    fi
done

# Upload fprtool-full.json if exists
if [[ -f "infra/schemas/fprtool-full.json" ]]; then
    aws s3 cp "infra/schemas/fprtool-full.json" "s3://$BUCKET/schemas/fprtool-full.json" \
        --profile "$PROFILE" --region "$REGION" --quiet
    echo "  ✅ fprtool-full.json uploaded"
fi

echo ""
echo "✅ Schema deployed to $ENV"
echo ""

# Step 3: Verify
echo "📋 S3 contents:"
aws s3 ls "s3://$BUCKET/schemas/" --profile "$PROFILE" --region "$REGION"
