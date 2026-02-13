#!/bin/bash
# Sets GitHub repository secrets from .gh-secrets file.
# Usage: ./scripts/set-gh-secrets.sh

set -euo pipefail

SECRETS_FILE="$(git rev-parse --show-toplevel)/.gh-secrets"

if [ ! -f "$SECRETS_FILE" ]; then
  echo "Error: $SECRETS_FILE not found"
  exit 1
fi

ERRORS=0
while IFS= read -r line; do
  # Skip blank lines and comments
  [[ -z "$line" || "$line" =~ ^# ]] && continue

  key="${line%%=*}"
  value="${line#*=}"

  if [ -z "$value" ]; then
    echo "Warning: $key is empty, skipping"
    ERRORS=1
    continue
  fi

  echo "Setting $key..."
  gh secret set "$key" --body "$value"
done < "$SECRETS_FILE"

if [ "$ERRORS" -ne 0 ]; then
  echo ""
  echo "Some secrets were skipped. Fill in all values in .gh-secrets and re-run."
  exit 1
fi

echo ""
echo "All secrets set. Verify with: gh secret list"
