#!/usr/bin/env bash
set -euo pipefail

# 使い方:
#   export GCP_PROJECT_ID="your-project-id"
#   export GEMINI_API_KEY="..."
#   export GOOGLE_MAPS_API_KEY_SERVER="..."      # Elevation/Places のサーバー利用用
#   export GOOGLE_SHEETS_ID="..."
#   export GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'
#   ./scripts/set_gcp_secrets.sh

required_vars=(
  GCP_PROJECT_ID
  GEMINI_API_KEY
  GOOGLE_MAPS_API_KEY_SERVER
  GOOGLE_SHEETS_ID
  GOOGLE_APPLICATION_CREDENTIALS_JSON
)

for v in "${required_vars[@]}"; do
  if [[ -z "${!v:-}" ]]; then
    echo "Missing required env var: $v" >&2
    exit 1
  fi
done

create_or_update_secret() {
  local name="$1"
  local value="$2"

  if gcloud secrets describe "$name" --project "$GCP_PROJECT_ID" >/dev/null 2>&1; then
    printf '%s' "$value" | gcloud secrets versions add "$name" --data-file=- --project "$GCP_PROJECT_ID"
  else
    printf '%s' "$value" | gcloud secrets create "$name" --replication-policy="automatic" --data-file=- --project "$GCP_PROJECT_ID"
  fi
}

create_or_update_secret "GEMINI_API_KEY" "$GEMINI_API_KEY"
create_or_update_secret "GOOGLE_MAPS_API_KEY_SERVER" "$GOOGLE_MAPS_API_KEY_SERVER"
create_or_update_secret "GOOGLE_SHEETS_ID" "$GOOGLE_SHEETS_ID"
create_or_update_secret "GOOGLE_APPLICATION_CREDENTIALS_JSON" "$GOOGLE_APPLICATION_CREDENTIALS_JSON"

echo "Secrets have been created/updated in Secret Manager."