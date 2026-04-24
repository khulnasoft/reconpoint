#!/bin/bash

# Resolve script and repo paths so this script can be run as: sudo ./scripts/uninstall.sh (from repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Guard: ensure REPO_ROOT is safe and really the reconPoint repo root before any destructive operation
if [[ -z "$REPO_ROOT" || "$REPO_ROOT" == "/" ]]; then
  echo "Error: REPO_ROOT resolved to an invalid path. Aborting." >&2
  exit 1
fi
if [[ ! -f "$REPO_ROOT/Makefile" ]]; then
  echo "Error: $REPO_ROOT does not look like the reconPoint repo root (Makefile missing). Aborting." >&2
  exit 1
fi
if [[ ! -f "$REPO_ROOT/web/reconPoint/version.txt" ]]; then
  echo "Error: $REPO_ROOT does not look like the reconPoint repo root (web/reconPoint/version.txt missing). Aborting." >&2
  exit 1
fi

# Import common functions
source "$SCRIPT_DIR/common_functions.sh"

cat "$REPO_ROOT/web/art/reconPoint.txt"

# Check for root privileges
if [ "$(whoami)" != "root" ]; then
  log ""
  log "Error uninstalling reconPoint: please run this script as root!" $COLOR_RED
  log "Example: sudo ./scripts/uninstall.sh (from repository root)" $COLOR_RED
  exit 1
fi

log ""
log "Uninstalling reconPoint..." $COLOR_CYAN
log ""

tput setaf $COLOR_RED;
read -p "This action will stop and remove all containers, volumes and networks of reconPoint. Do you want to continue? [y/n] " -n 1
log ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
  log ""

  log "Stopping reconPoint..." $COLOR_CYAN
  if (cd "$REPO_ROOT" && make down); then
    log "Stopped reconPoint" $COLOR_GREEN
  else
    log "Failed to stop reconPoint" $COLOR_RED
    exit 1
  fi
  log ""

  log "Removing all volumes related to reconPoint..." $COLOR_CYAN
  if docker volume rm $(docker volume ls -q --filter name=reconpoint_) 2>/dev/null || true; then
    log "Removed all volumes related to reconPoint" $COLOR_GREEN
  else
    log "Warning: Failed to remove some or all volumes" $COLOR_YELLOW
  fi
  log ""

  log "Removing all networks related to reconPoint..." $COLOR_CYAN
  if docker network rm reconpoint_network; then
    log "Removed all networks related to reconPoint" $COLOR_GREEN
  else
    log "Warning: Failed to remove reconpoint_network" $COLOR_YELLOW
  fi
  log ""

  log "Removing static files and secrets from reconPoint..." $COLOR_CYAN

  # Remove web/staticfiles directory
  if [ -d "$REPO_ROOT/web/staticfiles" ]; then
    log "Removing web/staticfiles directory..." $COLOR_CYAN
    if (cd "$REPO_ROOT" && rm -rf web/staticfiles); then
      log "Removed web/staticfiles directory" $COLOR_GREEN
    else
      log "Warning: Failed to remove web/staticfiles directory" $COLOR_YELLOW
    fi
  else
    log "web/staticfiles directory not found, skipping..." $COLOR_YELLOW
  fi

  # Remove docker/secrets directory
  if [ -d "$REPO_ROOT/docker/secrets" ]; then
    log "Removing docker/secrets directory..." $COLOR_CYAN
    if (cd "$REPO_ROOT" && rm -rf docker/secrets); then
      log "Removed docker/secrets directory" $COLOR_GREEN
    else
      log "Warning: Failed to remove docker/secrets directory" $COLOR_YELLOW
    fi
  else
    log "docker/secrets directory not found, skipping..." $COLOR_YELLOW
  fi

  log ""
else
  log ""
  log "Exiting!" $COLOR_DEFAULT
  exit 1
fi

tput setaf $COLOR_RED;
read -p "Do you want to remove Docker images related to reconPoint? [y/n] " -n 1 -r
log ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
  log ""
  log "Removing all Docker images related to reconPoint..." $COLOR_CYAN
  if (cd "$REPO_ROOT" && make remove_images); then
    log "Removed all Docker images" $COLOR_GREEN
  else
    log "Warning: Failed to remove some or all Docker images" $COLOR_YELLOW
  fi
  log ""
else
  log ""
  log "Skipping removal of Docker images" $COLOR_CYAN
fi

tput setaf $COLOR_RED;
read -p "Do you want to remove all Docker-related leftovers? [y/n] " -n 1 -r
log ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
  log ""
  log "Removing all Docker-related leftovers..." $COLOR_CYAN
  if docker system prune -a -f; then
    log "Removed all Docker-related leftovers" $COLOR_GREEN
  else
    log "Warning: Failed to remove some or all Docker-related leftovers" $COLOR_YELLOW
  fi
  log ""
else
  log ""
  log "Skipping removal of Docker-related leftovers..." $COLOR_CYAN
  log ""
fi

log "Finished uninstalling." $COLOR_GREEN