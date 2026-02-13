# Dockerfile — Multi-stage build: RPM build + FreeRADIUS runtime
#
# Stage 1 (builder): Builds RPMs from source on Amazon Linux 2023
# Stage 2 (runtime): Installs the 4 core RPMs into a clean AL2023 image
#
# Usage:
#   docker compose build                    # build via compose
#   docker compose up -d                    # run FreeRADIUS in foreground
#
#   # Extract RPMs only (no runtime image):
#   docker build --target builder -f docker/Dockerfile -t freeradius-builder .
#   docker run --rm -v $(pwd)/output:/output freeradius-builder \
#     sh -c 'mkdir -p /output && cp ~/rpmbuild/RPMS/*/*.rpm /output/'

# ── Stage 1: builder ────────────────────────────────────────────────
FROM amazonlinux:2023 AS builder

COPY rpm/ /build/rpm/

ARG RELEASE_TAG=local
RUN chmod +x /build/rpm/build.sh && \
    /build/rpm/build.sh --release "${RELEASE_TAG}"

# ── Stage 2: runtime ────────────────────────────────────────────────
FROM amazonlinux:2023

COPY --from=builder /root/rpmbuild/RPMS/ /tmp/rpms/

# Install the 4 core packages (matching ansible/roles/freeradius/defaults/main.yml),
# explicitly excluding debuginfo/debugsource RPMs.
# Then install python3 (needed for Ansible docker connection in later phases).
RUN dnf install -y \
        /tmp/rpms/*/freeradius-3.2*.rpm \
        /tmp/rpms/*/freeradius-config-3*.rpm \
        /tmp/rpms/*/freeradius-utils-3*.rpm \
        /tmp/rpms/*/freeradius-sqlite-3*.rpm \
        python3 && \
    dnf clean all && \
    rm -rf /tmp/rpms

# Ensure log directory exists with correct ownership
RUN install -d -m 0750 -o radiusd -g radiusd /var/log/radius

EXPOSE 1812/udp 1813/udp 18121/udp

CMD ["radiusd", "-f"]
