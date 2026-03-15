#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/init_and_push_fortune_core.sh /workspaces/fortune-core-repo
# Optional env vars:
#   REMOTE_URL=git@github.com:norinori-jan/fortune-core.git
#   DEFAULT_BRANCH=main

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${1:-/workspaces/fortune-core-repo}"
REMOTE_URL="${REMOTE_URL:-git@github.com:norinori-jan/fortune-core.git}"
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"

if [[ -e "$TARGET_DIR" ]] && [[ -n "$(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
  echo "Target directory is not empty: $TARGET_DIR" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"

rsync -a \
  --exclude '.git/' \
  --exclude '.pytest_cache/' \
  --exclude '__pycache__/' \
  --exclude 'build/' \
  --exclude 'dist/' \
  --exclude '*.egg-info/' \
  "$SOURCE_DIR/" "$TARGET_DIR/"

cd "$TARGET_DIR"

git init
git add README.md pyproject.toml .gitignore src tests scripts
git commit -m "Initial import of fortune-core"
git branch -M "$DEFAULT_BRANCH"

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

cat <<EOF

fortune-core repository prepared at: $TARGET_DIR

Next command:
  git push -u origin $DEFAULT_BRANCH

Remote:
  $REMOTE_URL

EOF
