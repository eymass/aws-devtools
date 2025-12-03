#!/bin/bash

# Heroku Health Check Script
# Monitors multiple Heroku apps and shows their status
# Usage: ./heroku_health_check.sh app1 app2 app3 app4

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get apps from command line arguments
APPS=("$@")

if [ ${#APPS[@]} -eq 0 ]; then
    echo -e "${RED}Error: No app names provided${NC}"
    echo ""
    echo "Usage: $0 app1 app2 app3 ..."
    echo "Example: $0 my-api my-frontend my-worker my-admin"
    exit 1
fi

print_header() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
}

print_app_header() {
    echo ""
    echo -e "${BLUE}┌─────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BLUE}│  📦 $1${NC}"
    echo -e "${BLUE}└─────────────────────────────────────────────────────────┘${NC}"
}

check_app() {
    local app=$1
    local status="healthy"
    
    print_app_header "$app"
    
    # Check if app exists
    if ! heroku apps:info --app "$app" &> /dev/null; then
        echo -e "  ${RED}✗ App not found or no access${NC}"
        return 1
    fi
    
    # Get dyno status
    echo -e "  ${YELLOW}Dynos:${NC}"
    local dynos=$(heroku ps --app "$app" 2>/dev/null)
    
    if [ -z "$dynos" ]; then
        echo -e "    ${RED}✗ No dynos running${NC}"
        status="unhealthy"
    else
        while IFS= read -r line; do
            if [[ $line == *": up"* ]]; then
                echo -e "    ${GREEN}✓${NC} $line"
            elif [[ $line == *": crashed"* ]] || [[ $line == *": down"* ]]; then
                echo -e "    ${RED}✗${NC} $line"
                status="unhealthy"
            elif [[ $line == *"==="* ]]; then
                echo -e "    $line"
            else
                echo -e "    $line"
            fi
        done <<< "$dynos"
    fi
    
    # Get app URL and test it
    local url=$(heroku apps:info --app "$app" 2>/dev/null | grep "Web URL" | awk '{print $3}')
    if [ ! -z "$url" ]; then
        echo -e "  ${YELLOW}Web URL:${NC} $url"
        
        # Quick HTTP check
        local http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
        if [ "$http_code" = "200" ] || [ "$http_code" = "301" ] || [ "$http_code" = "302" ]; then
            echo -e "  ${YELLOW}HTTP Status:${NC} ${GREEN}✓ $http_code${NC}"
        elif [ "$http_code" = "000" ]; then
            echo -e "  ${YELLOW}HTTP Status:${NC} ${RED}✗ Timeout/Unreachable${NC}"
            status="unhealthy"
        else
            echo -e "  ${YELLOW}HTTP Status:${NC} ${YELLOW}⚠ $http_code${NC}"
        fi
    fi
    
    # Check for recent errors (last 100 lines)
    local errors=$(heroku logs -n 100 --app "$app" 2>/dev/null | grep -i "error\|exception\|crashed" | tail -3)
    if [ ! -z "$errors" ]; then
        echo -e "  ${YELLOW}Recent Errors:${NC}"
        echo "$errors" | while IFS= read -r line; do
            echo -e "    ${RED}! ${line:0:70}...${NC}"
        done
    fi
    
    # Summary
    if [ "$status" = "healthy" ]; then
        echo -e "  ${GREEN}► Status: HEALTHY${NC}"
        return 0
    else
        echo -e "  ${RED}► Status: UNHEALTHY${NC}"
        return 1
    fi
}

show_summary() {
    local healthy=$1
    local unhealthy=$2
    local total=$((healthy + unhealthy))
    
    print_header "SUMMARY"
    echo ""
    echo -e "  Total Apps:    $total"
    echo -e "  ${GREEN}Healthy:       $healthy${NC}"
    echo -e "  ${RED}Unhealthy:     $unhealthy${NC}"
    echo ""
    
    if [ $unhealthy -eq 0 ]; then
        echo -e "  ${GREEN}✓ All systems operational!${NC}"
    else
        echo -e "  ${RED}⚠ Some apps need attention!${NC}"
    fi
    echo ""
}

main() {
    print_header "HEROKU HEALTH CHECK"
    echo -e "  Checking ${#APPS[@]} apps..."
    
    # Check Heroku CLI
    if ! command -v heroku &> /dev/null; then
        echo -e "${RED}Error: Heroku CLI not installed${NC}"
        exit 1
    fi
    
    # Check login
    if ! heroku auth:whoami &> /dev/null; then
        echo -e "${RED}Error: Not logged into Heroku. Run: heroku login${NC}"
        exit 1
    fi
    
    local healthy=0
    local unhealthy=0
    
    for app in "${APPS[@]}"; do
        if check_app "$app"; then
            ((healthy++))
        else
            ((unhealthy++))
        fi
    done
    
    show_summary $healthy $unhealthy
    
    # Exit with error if any unhealthy
    [ $unhealthy -eq 0 ]
}

# Run
main "$@"

