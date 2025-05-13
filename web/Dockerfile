# Use ARMv7-specific base image
FROM arm32v7/ubuntu:22.04

ARG GECKOVERSION=0.33.0
ARG GOVERSION=1.21.5

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    DATABASE=postgres \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GOPATH=$HOME/go \
    PATH="${PATH}:${GOPATH}/bin"

# Install Go from official ARMv7 binary
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        wget && \
    # Install Go
    curl -L https://go.dev/dl/go${GOVERSION}.linux-armv6l.tar.gz | tar -xzC /usr/local && \
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set Go environment
ENV GOROOT=/usr/local/go
ENV PATH="${GOROOT}/bin:${PATH}"

# Install system dependencies
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        geoip-bin \
        geoip-database \
        gcc \
        libpq-dev \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libpcap-dev \
        netcat \
        nmap \
        python3.11 \
        python3-dev \
        python3-pip \
        python3-netaddr \
        software-properties-common \
        x11-utils \
        xvfb && \
    add-apt-repository ppa:mozillateam/ppa -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install geckodriver
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "${ARCH}" = "arm64" ]; then \
        GECKOPATH="geckodriver-v${GECKOVERSION}-linux-aarch64.tar.gz"; \
    elif [ "${ARCH}" = "amd64" ]; then \
        GECKOPATH="geckodriver-v${GECKOVERSION}-linux64.tar.gz"; \
    elif [ "${ARCH}" = "armv7l" ] || [ "${ARCH}" = "armhf" ]; then \
        GECKOPATH="geckodriver-v${GECKOVERSION}-linux-armv7l.tar.gz"; \
    else \
        echo "Unsupported architecture: ${ARCH}" && exit 1; \
    fi && \
    wget -q "https://github.com/mozilla/geckodriver/releases/download/v${GECKOVERSION}/${GECKOPATH}" && \
    tar -xzf "${GECKOPATH}" && \
    rm "${GECKOPATH}" && \
    mv geckodriver /usr/bin/ && \
    chmod +x /usr/bin/geckodriver

# Install Rust for orjson
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    rm -rf ~/.cargo/registry && \
    rm -rf ~/.cargo/git

ENV PATH="/root/.cargo/bin:${PATH}"

# Install Python dependencies
RUN pip3 install --no-cache-dir maturin

# Set working directory
WORKDIR /usr/src/app

# Install Go tools
ENV GO111MODULE=on
RUN printf "\
    github.com/jaeles-project/gospider@latest\n\
    github.com/tomnomnom/gf@latest\n\
    github.com/tomnomnom/unfurl@latest\n\
    github.com/tomnomnom/waybackurls@latest\n\
    github.com/projectdiscovery/httpx/cmd/httpx@latest\n\
    github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest\n\
    github.com/projectdiscovery/chaos-client/cmd/chaos@latest\n\
    github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest\n\
    github.com/projectdiscovery/naabu/v2/cmd/naabu@latest\n\
    github.com/hakluke/hakrawler@latest\n\
    github.com/lc/gau/v2/cmd/gau@latest\n\
    github.com/owasp-amass/amass/v3/...@latest\n\
    github.com/ffuf/ffuf@latest\n\
    github.com/projectdiscovery/tlsx/cmd/tlsx@latest\n\
    github.com/hahwul/dalfox/v2@latest\n\
    github.com/projectdiscovery/katana/cmd/katana@latest\n\
    github.com/dwisiswant0/crlfuzz/cmd/crlfuzz@latest\n\
    github.com/sa7mon/s3scanner@latest\n" | xargs -I{} sh -c "go install {} || true"

# Update Nuclei and Nuclei-Templates
RUN nuclei -update-templates

# Update chaos
RUN chaos -update

# Copy requirements and install Python dependencies
COPY ./requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade setuptools==72.1.0
RUN pip3 install -r /tmp/requirements.txt --no-cache-dir

# Install eyewitness dependencies
RUN pip3 install --no-cache-dir \
    fuzzywuzzy \
    selenium==4.9.1 \
    python-Levenshtein \
    pyvirtualdisplay

# Clean up
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set entrypoint
CMD ["/bin/bash"]