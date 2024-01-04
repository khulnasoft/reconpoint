#!/bin/bash

cat ../web/art/reconPoint.txt
echo "Uninstalling reconPoint"

if [ "$EUID" -ne 0 ]
  then
  echo "Error uninstalling reconPoint, Please run this script as root!"
  echo "Example: sudo ./uninstall.sh"
  exit
fi

echo "Stopping reconPoint"
docker stop reconpoint_web_1 reconpoint_db_1 reconpoint_celery_1 reconpoint_celery-beat_1 reconpoint_redis_1 reconpoint_tor_1 reconpoint_proxy_1

if [[ $REPLY =~ ^[Yy]$ ]]
then
  echo "Stopping reconPoint"
  docker stop reconpoint-web-1 reconpoint-db-1 reconpoint-celery-1 reconpoint-celery-beat-1 reconpoint-redis-1 reconpoint-tor-1 reconpoint-proxy-1
  echo "Stopped reconPoint"

  echo "Removing all containers related to reconPoint"
  docker rm reconpoint-web-1 reconpoint-db-1 reconpoint-celery-1 reconpoint-celery-beat-1 reconpoint-redis-1 reconpoint-tor-1 reconpoint-proxy-1
  echo "Removed all containers related to reconPoint"

  echo "Removing all volumes related to reconPoint"
  docker volume rm reconpoint_gf_patterns reconpoint_github_repos reconpoint_nuclei_templates reconpoint_postgres_data reconpoint_scan_results reconpoint_tool_config reconpoint_static_volume reconpoint_wordlist
  echo "Removed all volumes related to reconPoint"

  echo "Removing all networks related to reconPoint"
  docker network rm reconpoint_reconpoint_network reconpoint_default
  echo "Removed all networks related to reconPoint"
else
  exit 1
fi

echo "Finished Uninstalling."
