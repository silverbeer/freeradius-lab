#!/bin/bash
# Verifies Grafana Cloud credentials from .gh-secrets are working.
# Usage: ./scripts/verify-grafana-secrets.sh

set -euo pipefail

SECRETS_FILE="$(git rev-parse --show-toplevel)/.gh-secrets"

if [ ! -f "$SECRETS_FILE" ]; then
  echo "Error: $SECRETS_FILE not found"
  exit 1
fi

# Source the secrets
while IFS='=' read -r key value; do
  [[ -z "$key" || "$key" =~ ^# ]] && continue
  declare "$key=$value"
done < "$SECRETS_FILE"

ERRORS=0

echo "=== Grafana Cloud Credential Verification ==="
echo ""

# --- Check required keys exist ---
for var in GRAFANA_PROMETHEUS_URL GRAFANA_PROMETHEUS_USER GRAFANA_LOKI_URL GRAFANA_LOKI_USER GRAFANA_API_KEY; do
  if [ -z "${!var:-}" ]; then
    echo "FAIL: $var is not set in .gh-secrets"
    ERRORS=1
  fi
done

if [ "$ERRORS" -ne 0 ]; then
  exit 1
fi

echo "Prometheus URL  : $GRAFANA_PROMETHEUS_URL"
echo "Prometheus User : $GRAFANA_PROMETHEUS_USER"
echo "Loki URL        : $GRAFANA_LOKI_URL"
echo "Loki User       : $GRAFANA_LOKI_USER"
echo "API Key         : ${GRAFANA_API_KEY:0:10}..."
echo ""

# --- Test Prometheus (remote write endpoint) ---
PROM_BASE=$(echo "$GRAFANA_PROMETHEUS_URL" | sed 's|/api/prom/push||')
echo -n "Testing Prometheus ($PROM_BASE)... "
HTTP_CODE=$(curl -s -o /tmp/grafana-prom-test.txt -w '%{http_code}' \
  -u "${GRAFANA_PROMETHEUS_USER}:${GRAFANA_API_KEY}" \
  "${PROM_BASE}/api/prom/api/v1/labels" 2>&1)
if [ "$HTTP_CODE" = "200" ]; then
  echo "OK (HTTP $HTTP_CODE)"
else
  echo "FAIL (HTTP $HTTP_CODE)"
  cat /tmp/grafana-prom-test.txt 2>/dev/null
  echo ""
  ERRORS=1
fi

# --- Test Loki ---
echo -n "Testing Loki ($GRAFANA_LOKI_URL)... "
HTTP_CODE=$(curl -s -o /tmp/grafana-loki-test.txt -w '%{http_code}' \
  -u "${GRAFANA_LOKI_USER}:${GRAFANA_API_KEY}" \
  "${GRAFANA_LOKI_URL}/loki/api/v1/labels" 2>&1)
if [ "$HTTP_CODE" = "200" ]; then
  echo "OK (HTTP $HTTP_CODE)"
else
  echo "FAIL (HTTP $HTTP_CODE)"
  cat /tmp/grafana-loki-test.txt 2>/dev/null
  echo ""
  ERRORS=1
fi

# --- Summary ---
echo ""
if [ "$ERRORS" -eq 0 ]; then
  echo "All checks passed. Credentials are valid."
else
  echo "Some checks failed. Verify in Grafana Cloud:"
  echo "  1. Go to grafana.com -> My Account -> your stack"
  echo "  2. Check Prometheus and Loki 'Details' for correct User/Instance IDs"
  echo "  3. Check Administration -> Service Accounts for token status and scopes"
  echo "     (needs metrics:write and logs:write)"
  exit 1
fi
