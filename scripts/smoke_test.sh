#!/usr/bin/env bash
#
# smoke_test.sh — Quick FreeRADIUS validation via radtest
#
# Runs on the EC2 instance via SSM send-command.
# Exit code 0 = all tests passed, non-zero = failure.
#
set -euo pipefail

PASS=0
FAIL=0

echo "=== FreeRADIUS Smoke Test ==="
echo "Timestamp: $(date -u)"
echo ""

run_test() {
    local name="$1"
    local user="$2"
    local pass="$3"
    local expect="$4" # "Accept" or "Reject"

    echo "--- Test: ${name} ---"
    OUTPUT=$(radtest "$user" "$pass" 127.0.0.1 0 testing123 2>&1) || true
    echo "$OUTPUT"

    if echo "$OUTPUT" | grep -q "Access-${expect}"; then
        echo "RESULT: PASS"
        ((PASS++))
    else
        echo "RESULT: FAIL (expected Access-${expect})"
        ((FAIL++))
    fi
    echo ""
}

# ── Test 1: Valid authentication ──
run_test "Valid user authenticates" "testrunner" "run123" "Accept"

# ── Test 2: Wrong password rejected ──
run_test "Wrong password rejected" "testrunner" "wrongpass" "Reject"

# ── Test 3: Unknown user rejected ──
run_test "Unknown user rejected" "nosuchuser" "anything" "Reject"

# ── Test 4: Ports are listening ──
echo "--- Test: Ports are listening ---"
if ss -ulnp | grep -q ":1812 "; then
    echo "Port 1812 (auth): LISTENING"
    ((PASS++))
else
    echo "Port 1812 (auth): NOT LISTENING"
    ((FAIL++))
fi

if ss -ulnp | grep -q ":1813 "; then
    echo "Port 1813 (acct): LISTENING"
    ((PASS++))
else
    echo "Port 1813 (acct): NOT LISTENING"
    ((FAIL++))
fi
echo ""

# ── Summary ──
echo "=== Smoke Test Summary ==="
echo "Passed: ${PASS}"
echo "Failed: ${FAIL}"
echo "Total:  $((PASS + FAIL))"

if [ "$FAIL" -gt 0 ]; then
    echo "STATUS: FAILED"
    exit 1
fi

echo "STATUS: PASSED"
exit 0
