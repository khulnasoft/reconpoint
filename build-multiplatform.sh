#!/bin/bash
# Multi-platform build script for reconPoint
# Builds images for AMD64, ARM64, and ARM32 architectures

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="reconpoint"
VERSION="${1:-latest}"
REGISTRY="${REGISTRY:-docker.io/khulnasoft}"

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}reconPoint Multi-Platform Build Script${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Check if buildx is available
if ! docker buildx version &> /dev/null; then
    echo -e "${RED}❌ Docker buildx is not available${NC}"
    echo "Install with: docker buildx install"
    exit 1
fi

echo -e "${YELLOW}📋 Build Configuration:${NC}"
echo "  Image: $REGISTRY/$IMAGE_NAME:$VERSION"
echo "  Platforms: linux/amd64, linux/arm64, linux/arm/v7"
echo ""

# Create builder instance if it doesn't exist
if ! docker buildx ls | grep -q "multiplatform-builder"; then
    echo -e "${YELLOW}🔧 Creating multiplatform builder...${NC}"
    docker buildx create --name multiplatform-builder --use
    docker buildx inspect --bootstrap
else
    echo -e "${GREEN}✅ Using existing multiplatform builder${NC}"
    docker buildx use multiplatform-builder
fi

echo ""
echo -e "${YELLOW}🏗️  Building multi-platform images...${NC}"
echo ""

# Build for all platforms
docker buildx build \
    --platform linux/amd64,linux/arm64,linux/arm/v7 \
    --tag "$REGISTRY/$IMAGE_NAME:$VERSION" \
    --tag "$REGISTRY/$IMAGE_NAME:latest" \
    --file ./web/Dockerfile \
    --build-arg PYTHON_VERSION=3.10 \
    --build-arg GECKOVERSION=0.33.0 \
    --build-arg GOVERSION=1.21.5 \
    --build-arg UBUNTU_VERSION=22.04 \
    --progress=plain \
    ${PUSH:+--push} \
    ./web

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Build Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Images built for:"
echo "  - linux/amd64 (Intel/AMD 64-bit)"
echo "  - linux/arm64 (ARM 64-bit, Raspberry Pi 3/4/5)"
echo "  - linux/arm/v7 (ARM 32-bit, Raspberry Pi 2/3)"
echo ""
echo "To push to registry, run:"
echo "  PUSH=1 ./build-multiplatform.sh $VERSION"
echo ""
echo "To use locally:"
echo "  docker-compose pull"
echo "  docker-compose up -d"
echo ""

# Test images
echo -e "${YELLOW}🧪 Testing images...${NC}"
echo ""

for platform in "linux/amd64" "linux/arm64" "linux/arm/v7"; do
    echo -n "Testing $platform... "
    if docker buildx imagetools inspect "$REGISTRY/$IMAGE_NAME:$VERSION" | grep -q "$platform"; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
    fi
done

echo ""
echo -e "${GREEN}🎉 All done!${NC}"
