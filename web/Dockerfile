# Base image
FROM ubuntu:22.04

# Arguments
ARG GECKOVERSION=0.33.0
ARG GOVERSION=1.21.5

# Labels and Credits
LABEL \
    name="reconPoint" \
    author="KhulnaSoft DevOps <security@khulnasoft.com>" \
    description="ReconPoint is an automated pipeline of recon process, useful for information gathering during web application penetration testing."

# Environment Variables
ENV DEBIAN_FRONTEND="noninteractive" \
    DATABASE="postgres" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GOROOT="/usr/local/go" \
    GOPATH=$HOME/go \
    PATH="${PATH}:${GOROOT}/bin:${GOPATH}/bin"

# Install essential packages
RUN apt update -y && \
    apt install -y \
    python3.10 \
    python3-dev \
    python3-pip \
    build-essential \
    cmake \
    geoip-bin \
    geoip-database \
    gcc \
    git \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpcap-dev \
    netcat \
    nmap \
    x11-utils \
    xvfb \
    wget \
    curl \
    python3-netaddr \
    software-properties-common && \
    add-apt-repository ppa:mozillateam/ppa && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Download and install Go
RUN ARCH=$(dpkg --print-architecture) && \
    case "${ARCH}" in \
      arm64) GOFILE="go${GOVERSION}.linux-arm64.tar.gz" ;; \
      amd64) GOFILE="go${GOVERSION}.linux-amd64.tar.gz" ;; \
      armhf) GOFILE="go${GOVERSION}.linux-armv6l.tar.gz" ;; \
      *) echo "Unknown architecture: ${ARCH}" && exit 1 ;; \
    esac && \
    wget https://go.dev/dl/${GOFILE} && \
    tar -xvf ${GOFILE} -C /usr/local && \
    rm ${GOFILE} && \
    echo "Go installed at:" && ls -la /usr/local/go/bin && \
    go version

# Download and install Geckodriver
RUN ARCH=$(dpkg --print-architecture) && \
    case "${ARCH}" in \
      arm64) GECKOPATH="geckodriver-v${GECKOVERSION}-linux-aarch64.tar.gz" ;; \
      amd64) GECKOPATH="geckodriver-v${GECKOVERSION}-linux64.tar.gz" ;; \
      armhf) GECKOPATH="geckodriver-v${GECKOVERSION}-linux-aarch64.tar.gz" ;; \
      *) echo "Unknown architecture: ${ARCH}" && exit 1 ;; \
    esac && \
    wget https://github.com/mozilla/geckodriver/releases/download/v${GECKOVERSION}/${GECKOPATH} && \
    tar -xvf ${GECKOPATH} && \
    rm ${GECKOPATH} && \
    mv geckodriver /usr/bin

# Install Rust and maturin
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    export PATH="/root/.cargo/bin:${PATH}" && \
    pip3 install maturin

# Make directory for app
WORKDIR /usr/src/app

# Install Go tools
RUN printf "\
    github.com/jaeles-project/gospider@latest\n\
    github.com/tomnomnom/gf@latest\n\
    github.com/tomnomnom/unfurl@latest\n\
    github.com/tomnomnom/waybackurls@latest\n\
    github.com/projectdiscovery/httpx/cmd/httpx@latest\n\
    github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest\n\
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
    github.com/sa7mon/s3scanner@latest\n" | \
    xargs -L1 go install -ldflags="-s -w" -v && \
    rm -rf /go/pkg/* && rm -rf /root/.cache/go-build

# Update Nuclei and Nuclei-Templates
RUN nuclei -update-templates

# Copy requirements and install Python packages
COPY ./requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade setuptools==72.1.0 && \
    pip3 install -r /tmp/requirements.txt --no-cache-dir && \
    pip3 install --no-cache-dir fuzzywuzzy \
    selenium==4.9.1 \
    python-Levenshtein \
    pyvirtualdisplay \
    netaddr

# Copy source code
COPY . /usr/src/app/
