# syntax=docker/dockerfile:1.4

# Build arguments for versioning
ARG PYTHON_VERSION=3.11
ARG GECKOVERSION=0.33.0
ARG GOVERSION=1.21.5
ARG UBUNTU_VERSION=22.04

# Base stage with shared system dependencies
FROM --platform=$TARGETPLATFORM ubuntu:${UBUNTU_VERSION} AS base

# Build-time platform arguments
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Metadata labels following OCI standards
LABEL org.opencontainers.image.title="ReconPoint Web"
LABEL org.opencontainers.image.description="Multi-architecture security reconnaissance platform"
LABEL org.opencontainers.image.source="https://github.com/your-org/reconpoint"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    DATABASE=postgres \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GOPATH=/root/go \
    PATH="/root/.cargo/bin:/root/go/bin:/usr/local/go/bin:${PATH}" \
    GO111MODULE=on \
    PORT=8000

# Base security updates and common dependencies
RUN set -eux; \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        wget \
        gnupg \
        apt-transport-https \
        software-properties-common && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Architecture detection stage
FROM base AS arch-detect

# Enhanced architecture detection with better error handling
RUN set -eux; \
    case "${TARGETPLATFORM:-linux/$(dpkg --print-architecture)}" in \
        "linux/amd64")  echo "ARCH=amd64;GO_ARCH=amd64;GECKO_ARCH=linux64" ;; \
        "linux/arm64")  echo "ARCH=arm64;GO_ARCH=arm64;GECKO_ARCH=linux-aarch64" ;; \
        "linux/arm/v7") echo "ARCH=armv7l;GO_ARCH=armv6l;GECKO_ARCH=linux-armv7l" ;; \
        *) \
            ARCH=$(dpkg --print-architecture); \
            case "${ARCH}" in \
                "armhf"|"armv7l") echo "ARCH=${ARCH};GO_ARCH=armv6l;GECKO_ARCH=linux-armv7l" ;; \
                "amd64")          echo "ARCH=amd64;GO_ARCH=amd64;GECKO_ARCH=linux64" ;; \
                "arm64")          echo "ARCH=arm64;GO_ARCH=arm64;GECKO_ARCH=linux-aarch64" ;; \
                *) echo "Unsupported architecture: ${ARCH}" >&2; exit 1 ;; \
            esac \
    esac > /etc/arch-env

# Builder stage for Go tools
FROM base AS go-builder
COPY --from=arch-detect /etc/arch-env /etc/arch-env

# Install Go with proper error handling
RUN set -eux; \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        wget \
        git && \
    . /etc/arch-env && \
    curl -fsSL "https://go.dev/dl/go${GOVERSION}.linux-${GO_ARCH}.tar.gz" | tar -xzC /usr/local && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Go tools efficiently
COPY go-tools.txt /tmp/
RUN set -eux; \
    mkdir -p /root/go/bin && \
    cd /tmp && \
    cat go-tools.txt | while read tool; do \
        go install "${tool}@latest" || echo "Failed to install: ${tool}"; \
    done

# Builder stage for Python dependencies
FROM base AS python-builder

# Install Python build dependencies
RUN set -eux; \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python${PYTHON_VERSION} \
        python3-pip \
        python3-dev \
        build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages with proper caching
COPY requirements.txt /tmp/
RUN pip3 install --upgrade pip setuptools==72.1.0 && \
    pip3 install -r /tmp/requirements.txt --no-cache-dir

# Install additional Python packages
RUN pip3 install --no-cache-dir fuzzywuzzy \
    selenium==4.9.1 \
    python-Levenshtein \
    pyvirtualdisplay \
    netaddr \
    maturin

# Final stage
FROM base

# Copy built artifacts from previous stages
COPY --from=go-builder /usr/local/go /usr/local/go
COPY --from=go-builder /root/go/bin /root/go/bin
COPY --from=python-builder /usr/local/lib/python${PYTHON_VERSION} /usr/local/lib/python${PYTHON_VERSION}
COPY --from=python-builder /usr/local/bin /usr/local/bin
COPY --from=arch-detect /etc/arch-env /etc/arch-env

# Install runtime dependencies
RUN set -eux; \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python${PYTHON_VERSION} \
        python3-pip \
        python3-netaddr \
        software-properties-common \
        geoip-bin \
        geoip-database \
        libpq-dev \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libpcap-dev \
        netcat \
        nmap \
        x11-utils \
        xvfb \
        git \
        wget \
        curl \
        nikto \
        sqlmap && \
    add-apt-repository ppa:mozillateam/ppa && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Geckodriver with proper error handling
RUN set -eux; \
    . /etc/arch-env && \
    GECKOPATH="geckodriver-v${GECKOVERSION}-${GECKO_ARCH}.tar.gz" && \
    curl -fsSL "https://github.com/mozilla/geckodriver/releases/download/v${GECKOVERSION}/${GECKOPATH}" -o /tmp/geckodriver.tar.gz && \
    tar -xzf /tmp/geckodriver.tar.gz -C /tmp && \
    mv /tmp/geckodriver /usr/bin/ && \
    chmod +x /usr/bin/geckodriver && \
    rm -rf /tmp/*

# Install Rust with minimal footprint - FIXED
RUN set -eux; \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal && \
    rm -rf ~/.cargo/registry ~/.cargo/git ~/.rustup/toolchains/*/share/

# Set working directory
WORKDIR /usr/src/app

# Copy application code
COPY . .

# Update security tools and templates
RUN set -eux; \
    nuclei -update-templates || true && \
    chaos -update || true && \
    chmod +x /usr/src/app/docker-entrypoint.sh

# Create non-root user for security
RUN useradd -m -s /bin/bash -u 1000 reconpoint && \
    chown -R reconpoint:reconpoint /usr/src/app

# Switch to non-root user
USER reconpoint

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Entrypoint and CMD
ENTRYPOINT ["/usr/src/app/docker-entrypoint.sh"]
CMD ["python3", "manage.py", "runserver", "0.0.0.0:${PORT}"]
