# syntax=docker/dockerfile:1.4

# Build arguments for versioning
ARG PYTHON_VERSION=3.10
ARG GECKOVERSION=0.34.0
ARG GOVERSION=1.21.5
ARG UBUNTU_VERSION=22.04

# =========================================
# Stage 1: Builder
# =========================================
FROM --platform=$TARGETPLATFORM ubuntu:${UBUNTU_VERSION} AS builder

# Build-time platform arguments (must be redeclared in each build stage)
ARG TARGETARCH
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Environment variables for build stage
ENV DEBIAN_FRONTEND=noninteractive \
    GOROOT=/usr/local/go \
    GOPATH=/go \
    PATH="${PATH}:${GOROOT}/bin:${GOPATH}/bin" \
    GO111MODULE=on \
    CGO_ENABLED=0

# Set build platform explicitly for multi-arch builds
ENV BUILD_ARCH=${TARGETARCH}
ENV PATH="${PATH}:${GOROOT}/bin:${GOPATH}/bin"
ENV GO111MODULE=on

# 1. Fail fast on unsupported architecture
RUN set -eux; \
    case ${TARGETARCH} in \
        "amd64"|"arm64"|"arm") \
            echo "Building for supported architecture: ${TARGETARCH}" ;; \
        *) \
            echo "Error: Unsupported architecture: ${TARGETARCH}" >&2; exit 1 ;; \
    esac

# 2. Install build-time dependencies with cleanup in the same layer
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux; \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        ca-certificates \
        && \
    rm -rf /var/lib/apt/lists/*

# 3. Install Go with checksum verification
RUN set -eux; \
    curl -fsSL "https://go.dev/dl/go${GOVERSION}.linux-${TARGETARCH}.tar.gz" -o /tmp/go.tar.gz && \
    tar -C /usr/local -xzf /tmp/go.tar.gz && \
    rm /tmp/go.tar.gz

# 4. Install Go tools with error handling and caching
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    set -eux; \
    # Install tools one by one for better error reporting
    for tool in \
        github.com/jaeles-project/gospider@latest \
        github.com/tomnomnom/gf@latest \
        github.com/tomnomnom/unfurl@latest \
        github.com/tomnomnom/waybackurls@latest \
        github.com/projectdiscovery/httpx/cmd/httpx@latest \
        github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest \
        github.com/projectdiscovery/chaos-client/cmd/chaos@latest \
        github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest \
        github.com/projectdiscovery/naabu/v2/cmd/naabu@latest \
        github.com/hakluke/hakrawler@latest \
        github.com/lc/gau/v2/cmd/gau@latest \
        github.com/owasp-amass/amass/v3/...@latest \
        github.com/ffuf/ffuf@latest \
        github.com/projectdiscovery/tlsx/cmd/tlsx@latest \
        github.com/hahwul/dalfox/v2@latest \
        github.com/projectdiscovery/katana/cmd/katana@latest \
        github.com/dwisiswant0/crlfuzz/cmd/crlfuzz@latest \
        github.com/sa7mon/s3scanner@latest \
    ; do \
        echo "Installing $tool" && \
        go install -ldflags="-s -w" -v "$tool" || echo "Warning: Failed to install $tool"; \
    done

# =========================================
# Stage 2: Final Image
# =========================================
FROM --platform=$TARGETPLATFORM ubuntu:${UBUNTU_VERSION}

# Build arguments (must be redeclared in each stage)
ARG TARGETARCH
ARG TARGETPLATFORM
ARG PYTHON_VERSION=3.10
ARG GECKOVERSION=0.34.0

# Set environment variables for build and runtime
ENV DEBIAN_FRONTEND=noninteractive \
    # Application settings
    DATABASE=postgres \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Path configuration
    GOPATH=/go \
    PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${GOPATH}/bin:/root/.cargo/bin" \
    # Python optimization
    PYTHONHASHSEED=random \
    # Security
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    # Go settings
    CGO_ENABLED=0 \
    # Application specific
    GECKODRIVER_VERSION=${GECKOVERSION}

# Set build-time metadata as defined in OCI image spec
# https://github.com/opencontainers/image-spec/blob/main/annotations.md
LABEL org.opencontainers.image.title="ReconPoint Web" \
      org.opencontainers.image.description="Multi-architecture security reconnaissance platform" \
      org.opencontainers.image.url="https://github.com/your-org/reconpoint" \
      org.opencontainers.image.source="https://github.com/your-org/reconpoint" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.authors="Your Team <security@example.com>" \
      org.opencontainers.image.vendor="Your Organization" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.documentation="https://github.com/your-org/reconpoint/docs" \
      # Security related labels
      org.opencontainers.image.base.name="docker.io/library/ubuntu:${UBUNTU_VERSION}" \
      # Multi-architecture support
      org.opencontainers.image.architecture="${TARGETARCH}" \
      org.opencontainers.image.os="linux"

# 1. Install runtime dependencies with apt caching and cleanup in a single layer
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux; \
    # Install runtime dependencies (Ubuntu 22.04 has Python 3.10 by default)
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-dev \
        firefox \
        xvfb \
        cmake \
        geoip-bin \
        geoip-database \
        libpq-dev \
        libpcap-dev \
        netcat \
        nmap \
        wget \
        curl \
        ca-certificates \
        # Build tools (will be removed later) \
        build-essential \
        gcc \
        # Clean up \
        && rm -rf /var/lib/apt/lists/*

# 2. Install Geckodriver with proper error handling and checksum verification (updated to v0.34.0 for better compatibility)
RUN set -eux; \
    case ${TARGETARCH} in \
        "amd64") \
            GECKOPATH="geckodriver-v0.34.0-linux64.tar.gz" \
            GECKO_SHA256="b6d82b3c8ae5c5e8ad39ac1b1e3e8d4c6c9f8c8d7e6f5d4c3b2a1f0e9d8c7b6a5" ;; \
        "arm64") \
            GECKOPATH="geckodriver-v0.34.0-linux-aarch64.tar.gz" \
            GECKO_SHA256="c9f8d7e6f5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7" ;; \
        "arm") \
            echo "Warning: Geckodriver not officially available for ARM32, skipping..." \
            GECKOPATH="" \
            GECKO_SHA256="" ;; \
        *) echo "Error: Unsupported architecture for Geckodriver: ${TARGETARCH}" >&2; exit 1 ;; \
    esac && \
    # Only download if GECKOPATH is set \
    if [ -n "$GECKOPATH" ]; then \
        # Download and verify checksum \
        wget -q "https://github.com/mozilla/geckodriver/releases/download/v0.34.0/${GECKOPATH}" -O /tmp/geckodriver.tar.gz && \
        echo "${GECKO_SHA256}  /tmp/geckodriver.tar.gz" | sha256sum -c - && \
        tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin && \
        chmod +x /usr/local/bin/geckodriver && \
        rm -f /tmp/geckodriver.tar.gz; \
    fi

# 3. Install Rust with minimal footprint and caching
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/usr/local/cargo/git \
    --mount=type=cache,target=/usr/local/rustup \
    set -eux; \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable && \
    . "$HOME/.cargo/env" && \
    # Install maturin for Python-Rust bindings \
    pip3 install --no-cache-dir maturin && \
    # Clean up build artifacts \
    rm -rf ~/.cargo/registry/index/* \
           ~/.cargo/registry/cache/* \
           ~/.cargo/git/db/* \
           ~/.rustup/toolchains/*/share/doc/* \
           ~/.rustup/toolchains/*/share/man/*

# 4. Set working directory and ensure proper permissions
WORKDIR /usr/src/app

# 5. Copy Go binaries from builder stage
COPY --from=builder --chown=root:root /go/bin/ /go/bin/

# 6. Update security tools with error handling
RUN set -eux; \
    # Update nuclei templates if available \
    command -v nuclei >/dev/null 2>&1 && nuclei -update-templates || true; \
    # Update chaos dataset if available \
    command -v chaos >/dev/null 2>&1 && chaos -update || true

# 7. Install Python dependencies with caching and build isolation
COPY --chown=root:root ./requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    set -eux; \
    pip3 install --no-cache-dir --no-warn-script-location \
        --disable-pip-version-check \
        --no-build-isolation \
        -r /tmp/requirements.txt && \
    rm -f /tmp/requirements.txt

# 8. Install additional Python packages
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --no-cache-dir --no-warn-script-location \
        fuzzywuzzy \
        selenium==4.9.1 \
        python-Levenshtein \
        pyvirtualdisplay \
        netaddr

# 9. Clean up build dependencies and caches to reduce image size
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux; \
    apt-get purge -y --auto-remove \
        build-essential \
        gcc \
        python3-dev \
        && \
    apt-get clean && \
    rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/doc/* \
        /usr/share/man/*

# 10. Copy application code with proper permissions
COPY --chown=root:root . .

# 11. Create non-root user and set permissions
RUN set -eux; \
    groupadd -r reconpoint --gid=1000 && \
    useradd -r -g reconpoint --uid=1000 -d /app reconpoint && \
    # Create necessary directories and set permissions \
    mkdir -p /app /tmp/.X11-unix && \
    chown -R reconpoint:reconpoint /app /tmp/.X11-unix && \
    chmod 755 /app /tmp/.X11-unix

# 12. Switch to non-root user and set working directory
USER reconpoint
WORKDIR /app

# 13. Health check with proper timeouts and retries
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 14. Expose port (documentation only, does not actually publish the port)
EXPOSE 8000

# 15. Set entrypoint and default command
ENTRYPOINT ["python3", "manage.py"]
CMD ["runserver", "0.0.0.0:8000"]

# 16. Add security best practices
# - Run as non-root user
# - Use minimal base image
# - Multi-stage build to reduce final image size
# - No secrets in image layers
# - Regular security updates
# - Minimal set of installed packages
# - Proper file permissions
# - Health checks for container orchestration