#!/usr/bin/env bash
# =============================================================================
# fetch-secrets.sh
# Pull secrets from Infisical (self-hosted) and write to local .env files.
#
# Usage:
#   ./scripts/fetch-secrets.sh           # defaults to dev environment
#   ./scripts/fetch-secrets.sh staging   # explicit environment
#
# Prerequisites:
#   - Infisical CLI installed: https://infisical.com/docs/cli/overview
#     Windows: winget install Infisical.Infisical
#     macOS:   brew install infisical/get-cli/infisical
#     Linux:   curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | sudo bash && sudo apt install infisical
#   - .env.infisical file present at repo root (copy .env.infisical and fill in PROJECT_ID)
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_INFISICAL="$REPO_ROOT/.env.infisical"
ENV="${1:-dev}"

# ── 1. Load credentials from .env.infisical ───────────────────────────────────
if [[ ! -f "$ENV_INFISICAL" ]]; then
  echo "ERROR: $ENV_INFISICAL not found."
  echo "  Copy .env.infisical, fill in INFISICAL_PROJECT_ID, and try again."
  exit 1
fi

# shellcheck source=/dev/null
source "$ENV_INFISICAL"

: "${INFISICAL_API_URL:?INFISICAL_API_URL not set in .env.infisical}"
: "${INFISICAL_CLIENT_ID:?INFISICAL_CLIENT_ID not set in .env.infisical}"
: "${INFISICAL_CLIENT_SECRET:?INFISICAL_CLIENT_SECRET not set in .env.infisical}"
: "${INFISICAL_PROJECT_ID:?INFISICAL_PROJECT_ID not set — edit .env.infisical}"

if [[ "$INFISICAL_PROJECT_ID" == "YOUR_INFISICAL_PROJECT_ID" ]]; then
  echo "ERROR: Replace YOUR_INFISICAL_PROJECT_ID in .env.infisical with your real Project ID."
  echo "  Find it: $INFISICAL_API_URL → your project → Settings → Project ID"
  exit 1
fi

# ── 2. Check Infisical CLI ────────────────────────────────────────────────────
# On Windows/winget the binary may not be in PATH yet for this shell session
INFISICAL_BIN=""
if command -v infisical &>/dev/null; then
  INFISICAL_BIN="infisical"
else
  WINGET_PATH="/c/Users/User/AppData/Local/Microsoft/WinGet/Packages/infisical.infisical_Microsoft.Winget.Source_8wekyb3d8bbwe/infisical.exe"
  if [[ -f "$WINGET_PATH" ]]; then
    INFISICAL_BIN="$WINGET_PATH"
  else
    echo "ERROR: 'infisical' CLI not found. Install: https://infisical.com/docs/cli/overview"
    exit 1
  fi
fi

# ── 3. Authenticate (Universal Auth / Machine Identity) ───────────────────────
echo "Authenticating with Infisical at $INFISICAL_API_URL ..."

export INFISICAL_UNIVERSAL_AUTH_CLIENT_ID="$INFISICAL_CLIENT_ID"
export INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET="$INFISICAL_CLIENT_SECRET"

# Obtain a short-lived access token — used for all export calls below
INFISICAL_TOKEN=$("$INFISICAL_BIN" login \
  --method=universal-auth \
  --client-id="$INFISICAL_CLIENT_ID" \
  --client-secret="$INFISICAL_CLIENT_SECRET" \
  --domain="$INFISICAL_API_URL" \
  --plain \
  --silent)

export INFISICAL_TOKEN

# Prevent Git Bash from converting /path arguments to Windows paths
export MSYS_NO_PATHCONV=1

echo "Authenticated. Fetching secrets for environment: $ENV"
echo ""

# ── Helper: export one Infisical path → one local file ───────────────────────
export_secrets() {
  local infisical_path="$1"
  local output_file="$2"

  echo "  $infisical_path  →  $output_file"

  "$INFISICAL_BIN" export \
    --token="$INFISICAL_TOKEN" \
    --projectId="$INFISICAL_PROJECT_ID" \
    --env="$ENV" \
    --path="$infisical_path" \
    --domain="$INFISICAL_API_URL" \
    --format=dotenv \
    > "$REPO_ROOT/$output_file"
}

# ── 4. Export secrets per service ─────────────────────────────────────────────
# Infisical path          Local .env file
export_secrets  /                                .env
export_secrets  /server                          server/.env
export_secrets  /client                          client/.env.local
export_secrets  /realtime                        services/realtime/.env.dev
export_secrets  /notifications                   services/notification-realtime/.env.dev

# /storage secrets belong to the Django backend — append to server/.env.dev
echo "" >> "$REPO_ROOT/server/.env"
echo "# --- /storage (Backblaze B2) ---" >> "$REPO_ROOT/server/.env"
"$INFISICAL_BIN" export \
  --token="$INFISICAL_TOKEN" \
  --projectId="$INFISICAL_PROJECT_ID" \
  --env="$ENV" \
  --path="/storage" \
  --domain="$INFISICAL_API_URL" \
  --format=dotenv \
  >> "$REPO_ROOT/server/.env"

echo ""
echo "Done. Secret files written:"
echo "  .env"
echo "  server/.env      (includes /server + /storage)"
echo "  client/.env.local"
echo "  services/realtime/.env.dev"
echo "  services/notification-realtime/.env.dev"
echo ""
echo "Next steps:"
echo "  Infrastructure (Docker):  docker-compose -f docker-compose.dev.yml up -d"
echo "  Django (native):          cd server && python manage.py runserver"
echo "  Next.js (native):         cd client && npm run dev"
echo "  Celery (native):          cd server && celery -A server worker -l info"
