#!/usr/bin/env bash
set -euo pipefail

# knowledge-support-app 用（固定値を埋め込み済み）
PROJECT_ID="knowledge-support-app"
PROJECT_NUMBER="691124237230"
POOL_ID="github-pool"
PROVIDER_ID="github-provider"
REPO="norinori-jan/fenshui_map"
SA_NAME="github-actions-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Using PROJECT_ID=${PROJECT_ID}"
echo "Using PROJECT_NUMBER=${PROJECT_NUMBER}"
echo "Target REPO=${REPO}"

gcloud config set project "${PROJECT_ID}" >/dev/null

# GitHub OIDC + deploy で利用する API
# 既に有効でも再実行可能です。
gcloud services enable \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  firebasehosting.googleapis.com \
  --project="${PROJECT_ID}"

if ! gcloud iam workload-identity-pools describe "${POOL_ID}" \
  --project="${PROJECT_ID}" \
  --location="global" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "${POOL_ID}" \
    --project="${PROJECT_ID}" \
    --location="global" \
    --display-name="GitHub Actions Pool"
  echo "Created workload identity pool: ${POOL_ID}"
else
  echo "Workload identity pool already exists: ${POOL_ID}"
fi

if ! gcloud iam workload-identity-pools providers describe "${PROVIDER_ID}" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="${POOL_ID}" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_ID}" \
    --project="${PROJECT_ID}" \
    --location="global" \
    --workload-identity-pool="${POOL_ID}" \
    --display-name="GitHub Provider" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
    --attribute-condition="assertion.repository=='${REPO}'"
  echo "Created workload identity provider: ${PROVIDER_ID}"
else
  gcloud iam workload-identity-pools providers update-oidc "${PROVIDER_ID}" \
    --project="${PROJECT_ID}" \
    --location="global" \
    --workload-identity-pool="${POOL_ID}" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
    --attribute-condition="assertion.repository=='${REPO}'"
  echo "Updated workload identity provider: ${PROVIDER_ID}"
fi

if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SA_NAME}" \
    --project="${PROJECT_ID}" \
    --display-name="GitHub Actions Deployer"
  echo "Created service account: ${SA_EMAIL}"
else
  echo "Service account already exists: ${SA_EMAIL}"
fi

# GitHub repo からの OIDC トークンで SA impersonation を許可
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${REPO}" \
  --quiet >/dev/null

# デプロイに必要な代表ロール
for ROLE in \
  roles/run.admin \
  roles/iam.serviceAccountUser \
  roles/secretmanager.secretAccessor \
  roles/artifactregistry.writer \
  roles/cloudbuild.builds.editor \
  roles/firebasehosting.admin
  do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${SA_EMAIL}" \
      --role="${ROLE}" \
      --quiet >/dev/null
  done

WORKLOAD_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"

echo ""
echo "==== GitHub Secrets に設定する値 ===="
echo "GCP_PROJECT_ID=${PROJECT_ID}"
echo "GCP_WORKLOAD_IDENTITY_PROVIDER=${WORKLOAD_PROVIDER}"
echo "GCP_SERVICE_ACCOUNT_EMAIL=${SA_EMAIL}"
echo "====================================="
