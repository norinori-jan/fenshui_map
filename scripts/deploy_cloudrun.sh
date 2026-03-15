#!/usr/bin/env bash
set -euo pipefail

# 使い方:
#   export GCP_PROJECT_ID="your-project-id"
#   export GCP_REGION="asia-northeast1"
#   export CLOUD_RUN_SERVICE="fengshui-api"
#   ./scripts/deploy_cloudrun.sh

PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-asia-northeast1}"
SERVICE="${CLOUD_RUN_SERVICE:-fengshui-api}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Missing required env var: GCP_PROJECT_ID" >&2
  exit 1
fi

gcloud run deploy "$SERVICE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --source . \
  --allow-unauthenticated \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest,GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY_SERVER:latest,GOOGLE_SHEETS_ID=GOOGLE_SHEETS_ID:latest

echo "Cloud Run deployment completed: $SERVICE ($REGION)"