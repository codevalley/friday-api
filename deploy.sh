#!/usr/bin/env bash
set -e  # exit on error

DOMAIN=${1:-"api.nyn.me"}
EMAIL=${2:-"admin@nyn.me"}
FETCH_CODE=false
INSTALL_DOCKER=false

# Colors for logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
log()   { echo -e "${GREEN}[LOG]${NC} $1"; }

show_help() {
cat <<EOF
Usage: $0 [domain] [email] [--docker] [--fetch-code]
  domain    : Domain name to serve (default: api.nyn.me)
  email     : Email for Let's Encrypt (default: admin@nyn.me)
  --docker  : Install Docker + Docker Compose if not present
  --fetch-code : Pull latest changes from Git
Example:
  $0 api.nyn.me admin@nyn.me --fetch-code
EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --docker)
      INSTALL_DOCKER=true
      shift
      ;;
    --fetch-code)
      FETCH_CODE=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      # Positional
      if [[ -z "$DOMAIN" ]]; then
        DOMAIN="$1"
      elif [[ -z "$EMAIL" ]]; then
        EMAIL="$1"
      fi
      shift
      ;;
  esac
done

# Check if run as root
if [[ $EUID -ne 0 ]]; then
  error "Please run as root (sudo)."
fi

if [ "$INSTALL_DOCKER" = true ]; then
  log "Installing Docker + Docker Compose if not already installed..."
  if ! command -v docker &>/dev/null; then
    info "Installing Docker..."
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  else
    info "Docker is already installed."
  fi
fi

if [ "$FETCH_CODE" = true ]; then
  if [ -d ".git" ]; then
    log "Pulling latest code from Git..."
    git stash || true
    git pull origin main || true
  else
    warn "No .git folder found, skipping code fetch..."
  fi
fi

log "Configuring domain: $DOMAIN"
log "Email for SSL: $EMAIL"

# Possibly export environment variables for your Docker Compose
export LETSENCRYPT_HOST="$DOMAIN"
export VIRTUAL_HOST="$DOMAIN"
export LETSENCRYPT_EMAIL="$EMAIL"

# Build and start containers
log "Building and starting containers..."
docker compose build
docker compose up -d

log "Verifying containers..."
docker compose ps

log "Deployment finished. Please allow a minute for Let's Encrypt to issue certificates (if using jwilder/nginx-proxy)."
