#!/bin/bash

cat ../web/art/reconPoint.txt
echo "Uninstalling reconPoint"

if [ "$EUID" -ne 0 ]
  then
  echo -e "\e[31mError uninstalling reconPoint, Please run this script as root!\e[0m"
  echo -e "\e[31mExample: sudo ./uninstall.sh\e[0m"
  exit
fi

DANGER='\e[31m'
SUCCESS='\e[32m'
WARNING='\e[33m'
INFO='\e[34m'
RESET='\e[0m'

print_status() {
    echo -e "${INFO}--------------------------------------------------${RESET}"
    echo -e "${INFO}$1${RESET}"
    echo -e "${INFO}--------------------------------------------------${RESET}"
}

print_status "WARNING: You are about to uninstall reconpoint"
echo -e "${DANGER}This action is not reversible. All containers, volumes, networks, and scan results will be removed.${RESET}"
echo -e "${DANGER}There is no going back after this point.${RESET}"
read -p "$(echo -e ${WARNING}"Are you sure you want to proceed? (y/Y/yes/YES to confirm): "${RESET})" -r CONFIRM

# change answer to lowecase for comparison
ANSWER_LC=$(echo "$CONFIRM" | tr '[:upper:]' '[:lower:]')

if [[ "$ANSWER_LC" != "y" && "$ANSWER_LC" != "yes" ]]; then
    print_status "${YELLOW}Uninstall aborted by user.${RESET}"
    exit 0
fi

print_status "${INFO}Proceeding with uninstalling reconPoint${RESET}"

print_status "Stopping all containers related to reconPoint..."
docker stop $(docker ps -a -q --filter name=reconpoint-) 2>/dev/null

print_status "Removing all containers related to reconPoint..."
docker rm $(docker ps -a -q --filter name=reconpoint-) 2>/dev/null

print_status "Removing all volumes related to reconPoint..."
docker volume rm $(docker volume ls -q --filter name=reconpoint-) 2>/dev/null

print_status "Removing all networks related to reconPoint..."
docker network rm $(docker network ls -q --filter name=reconpoint-) 2>/dev/null

print_status "Removing all images related to reconPoint..."
docker rmi $(docker images -q --filter reference=reconpoint-) 2>/dev/null

print_status "Performing final cleanup"
docker system prune -f --volumes --filter "label=com.docker.compose.project=reconpoint"

print_status "${SUCCESS}reconPoint uninstall process has been completed.${RESET}"
