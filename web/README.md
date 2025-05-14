# Multi-Architecture Docker Build Guide

## Prerequisites
- Docker Desktop ≥ 4.8 (with BuildX support)
- Docker Registry account (Docker Hub, GitHub Container Registry, etc.)
- Docker CLI logged in to your registry

## Build Instructions

1. Create and use a new builder instance with multi-architecture support:
```bash
docker buildx create --name reconpoint-builder --use
docker buildx inspect --bootstrap
```

2. Build and push the multi-architecture image:
```bash
# Replace 'yourregistry' with your actual registry (e.g., Docker Hub username)
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag yourregistry/reconpoint-web:latest \
  --push \
  .
```

3. Verify the multi-architecture support:
```bash
docker buildx imagetools inspect yourregistry/reconpoint-web:latest
```

## Supported Architectures
- linux/amd64 (Intel/AMD 64-bit)
- linux/arm64 (ARM 64-bit, e.g., Apple Silicon, AWS Graviton)
- linux/arm/v7 (ARM 32-bit v7, e.g., Raspberry Pi 3/4)

## Architecture-Specific Components
The Dockerfile automatically handles different architectures for:
- Go installation (correct architecture-specific binary)
- Geckodriver installation (correct platform binary)
- System dependencies and tools

## Local Testing
To test a specific architecture locally:
```bash
docker buildx build --platform linux/arm64 --load -t reconpoint-web:arm64-test .
docker run --rm -it reconpoint-web:arm64-test uname -m
```

## Notes
- The build process requires pushing to a registry due to multi-arch limitations
- Local builds with `--load` flag can only target your host architecture
- For development without pushing, use `--platform` to match your local architecture

