#!/bin/bash
set -euo pipefail

exec > >(tee /var/log/user-data.log) 2>&1
echo "=== user_data start: $(date -u) ==="

# System update
dnf update -y

# Install debug/admin tools
dnf install -y \
  vim \
  htop \
  jq \
  tree \
  tcpdump \
  bind-utils

# Verify SSM agent is running
systemctl status amazon-ssm-agent || systemctl start amazon-ssm-agent

echo "=== user_data complete: $(date -u) ==="
echo "Instance architecture: ${instance_architecture}"
echo "RPM bucket: ${rpm_bucket_name}"
