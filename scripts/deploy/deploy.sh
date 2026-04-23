#!/bin/bash
set -euo pipefail

#######################################################################
# Deploy new changes to an EXISTING Heroku app using HEROKU_API_KEY
#
# Usage:
#   ./tools/deploy/deploy.sh <app_name>
#
# Arguments:
#   app_name  – Name of the existing Heroku app (e.g. publab-agent)
#
# Environment:
#   HEROKU_API_KEY – Must be set (export or inline). Used for
#                    non-interactive / CI authentication.
#
# Prerequisites:
#   - Git repo with committed changes
#   - Heroku CLI installed
#   - HEROKU_API_KEY exported in the environment
#######################################################################

APP_NAME="${1:-}"

# ── Validation ───────────────────────────────────────────────────────
if [[ -z "$APP_NAME" ]]; then
  echo "Usage: $0 <app_name>"
  echo ""
  echo "  app_name  – Existing Heroku app to deploy to"
  echo ""
  echo "Requires HEROKU_API_KEY to be set in the environment."
  exit 1
fi

if [[ -z "${HEROKU_API_KEY:-}" ]]; then
  echo "❌  HEROKU_API_KEY is not set."
  echo "   Export it first:  export HEROKU_API_KEY=your-api-key"
  exit 1
fi

if ! command -v heroku &>/dev/null; then
  echo "❌  Heroku CLI is not installed. Install it first: https://devcenter.heroku.com/articles/heroku-cli"
  exit 1
fi

# ── Verify authentication ───────────────────────────────────────────
echo "🔑  Verifying Heroku authentication ..."
if ! heroku auth:whoami 2>/dev/null; then
  echo "❌  HEROKU_API_KEY is invalid or expired."
  exit 1
fi

# ── Verify app exists ───────────────────────────────────────────────
echo "🔍  Verifying app '$APP_NAME' exists ..."
if ! heroku apps:info --app "$APP_NAME" &>/dev/null; then
  echo "❌  App '$APP_NAME' not found. Check the name or create it first with heroku_new_app.sh"
  exit 1
fi

# ── Ensure heroku remote points to the right app ────────────────────
# ── Ensure heroku remote points to the right app ────────────────────
HEROKU_REMOTE="https://heroku:${HEROKU_API_KEY}@git.heroku.com/${APP_NAME}.git"

# Always reset to ensure correct credentials
git remote remove heroku 2>/dev/null || true
echo "➕  Adding heroku remote for $APP_NAME ..."
git remote add heroku "$HEROKU_REMOTE"

if git remote get-url heroku &>/dev/null; then
  CURRENT_REMOTE="$(git remote get-url heroku)"
  if [[ "$CURRENT_REMOTE" != "$HEROKU_REMOTE" ]]; then
    echo "🔄  Updating heroku remote to $APP_NAME ..."
    git remote set-url heroku "$HEROKU_REMOTE"
  fi
else
  echo "➕  Adding heroku remote for $APP_NAME ..."
  git remote add heroku "$HEROKU_REMOTE"
fi

# ── Deploy ───────────────────────────────────────────────────────────
echo "📦  Deploying to $APP_NAME $2..."
git push heroku $2:main --force || git push heroku $2:master --force

# ── Post-deploy ──────────────────────────────────────────────────────
echo ""
echo "✅  Deployed successfully to $APP_NAME!"
echo "   URL  : https://$APP_NAME.herokuapp.com"
echo "   Logs : heroku logs --tail --app $APP_NAME"
