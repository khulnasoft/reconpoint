include docker/.env
.DEFAULT_GOAL:=help

# This for future release of Compose that will use Docker Buildkit, which is much efficient.
COMPOSE_PREFIX_CMD := COMPOSE_DOCKER_CLI_BUILD=1
COMPOSE_ALL_FILES := -f docker/docker-compose.yml

# Check if 'docker compose' command is available, otherwise use 'docker-compose'
DOCKER_COMPOSE := $(shell if command -v docker > /dev/null && docker compose version > /dev/null 2>&1; then echo "docker compose"; else echo "docker-compose"; fi)
$(info Using: $(shell echo "$(DOCKER_COMPOSE)"))

.PHONY: certs

certs: @${COMPOSE_PREFIX_CMD} ${DOCKER_COMPOSE} -f docker/docker-compose.setup.yml run --rm certs
