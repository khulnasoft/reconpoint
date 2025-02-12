# Base image
FROM ubuntu:22.04

# Arguments for versioning
ARG GECKOVERSION=0.33.0
ARG GOVERSION=1.21.5

# Set environment variables
ENV DEBIAN_FRONTEND="noninteractive"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV GOROOT="/usr/local/go"
ENV GOPATH=$HOME/go
ENV PATH="${PATH}:${GOROOT}/bin:${GOPATH}/bin:/root/.cargo/bin"

# Labels and Credits
LABEL name="reconPoint" \
      author="KhulnaSoft Ltd <security@khulnasoft.com>" \
      description="reconPoint is an automated pipeline for the recon process, useful for information gathering during web application penetration testing."

# Install Python and essential packages
RUN apt update -y && \
    apt install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    gcc \
    geoip-bin \
    geoip-database \
    git \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpcap-dev \
    libpq-dev \
    netcat \
    nmap \
    python3-dev \
    python3-netaddr \
    python3-pip \
    python3.10 \
    software-properties-common \
    wget \
    x11-utils \
    xvfb && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Add Mozilla PPA and install Geckodriver
RUN add-apt-repository ppa:mozillateam/ppa && \
    ARCH=$(dpkg --print-architecture) && \
    if [ "${ARCH}" = "arm64" ]; then \
      GECKOPATH="geckodriver-v${GECKOVERSION}-linux-aarch64.tar.gz"; \
    elif [ "${ARCH}" = "amd64" ]; then \
      GECKOPATH="geckodriver-v${GECKOVERSION}-linux64.tar.gz"; \
    else \
      echo "reconPoint not supported, encountered unknown architecture: ${ARCH}" && exit 1; \
    fi && \
    wget https://github.com/mozilla/geckodriver/releases/download/v${GECKOVERSION}/${GECKOPATH} && \
    tar -xvf ${GECKOPATH} && \
    rm ${GECKOPATH} && \
    mv geckodriver /usr/bin

# Install Go
RUN ARCH=$(dpkg --print-architecture) && \
    curl -L https://go.dev/dl/go${GOVERSION}.linux-${ARCH}.tar.gz | tar -xzC /usr/local

# Install Rust for orjson and maturin
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    pip3 install maturin

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
    github.com/sa7mon/s3scanner@latest\n" | \
    xargs -L1 go install -ldflags="-s -w" -v && \
    rm -rf /go/pkg/* /root/.cache/go-build

# Update Nuclei and Nuclei-Templates
RUN nuclei -update-templates

# Update chaos
RUN chaos -update

# Copy and install Python requirements
COPY ./requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade setuptools==72.1.0 && \
    pip3 install -r /tmp/requirements.txt --no-cache-dir && \
    pip3 install --no-cache-dir fuzzywuzzy selenium==4.9.1 python-Levenshtein pyvirtualdisplay netaddr

# Copy source code
COPY . /usr/src/app/
