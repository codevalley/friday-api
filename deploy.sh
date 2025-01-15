#!/usr/bin/env bash
set -e  # exit on error

DOMAIN=""
EMAIL=""
FETCH_CODE=false
INSTALL_DOCKER=false
EXTERNAL_DB=true
RESTART_ONLY=true
NO_CACHE=false
USE_STAGING=false

# Colors
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
Usage: $0 --domain DOMAIN --email EMAIL [OPTIONS]
Required:
  --domain DOMAIN : Domain name to serve
  --email EMAIL   : Email for Let's Encrypt
Options:
  --docker        : Install Docker + Docker Compose if not present
  --fetch-code    : Pull latest changes from Git
  --external-db   : Use docker-compose.no-db.yml (skip local MySQL container)
  --restart       : Only restart containers without rebuilding or fetching code
  --no-cache      : Force Docker rebuild without using cache
  --staging       : Use Let's Encrypt staging environment for testing
Example:
  $0 --domain api.acme.me --email admin@acme.me --fetch-code
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --domain)
      DOMAIN="$2"
      shift 2
      ;;
    --email)
      EMAIL="$2"
      shift 2
      ;;
    --docker)
      INSTALL_DOCKER=true
      shift
      ;;
    --fetch-code)
      FETCH_CODE=true
      shift
      ;;
    --external-db)
      EXTERNAL_DB=true
      shift
      ;;
    --restart)
      RESTART_ONLY=true
      shift
      ;;
    --no-cache)
      NO_CACHE=true
      shift
      ;;
    --staging)
      USE_STAGING=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      error "Unknown argument: $1"
      ;;
  esac
done

# Validate required arguments
if [ -z "$DOMAIN" ]; then
  error "Domain is required. Use --domain DOMAIN"
fi

if [ -z "$EMAIL" ]; then
  error "Email is required. Use --email EMAIL"
fi

# Check if run as root or deploy user
if [[ $EUID -eq 0 ]] || [[ $(whoami) == "deploy" ]]; then
  info "Running as $(whoami)"
else
  error "This script must be run as either root or the 'deploy' user."
fi

if [ "$INSTALL_DOCKER" = true ]; then
  log "Installing Docker + Docker Compose if not already installed..."
  if ! command -v docker &>/dev/null; then
    info "Installing Docker..."
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
      gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu \
      \$(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
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

# Possibly set environment variables for the proxy
export LETSENCRYPT_HOST="$DOMAIN"
export VIRTUAL_HOST="$DOMAIN"
export LETSENCRYPT_EMAIL="$EMAIL"

JWT_KEY_LINE=$(grep -E '^JWT_SECRET_KEY=' .env || true)
if [ -z "$JWT_KEY_LINE" ]; then
  # There's no JWT_SECRET_KEY line in .env at all
  NEW_SECRET=$(openssl rand -hex 32)
  echo "JWT_SECRET_KEY=${NEW_SECRET}" >> .env
  log "Created JWT_SECRET_KEY in .env"
else
  # It exists, check if it's empty
  CURRENT_VALUE=$(echo "$JWT_KEY_LINE" | cut -d '=' -f2-)
  if [ -z "$CURRENT_VALUE" ]; then
    # It's blank
    NEW_SECRET=$(openssl rand -hex 32)
    sed -i "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=${NEW_SECRET}|" .env
    log "Replaced empty JWT_SECRET_KEY in .env"
  fi
fi

BUILD_ARGS=""
if [ "$NO_CACHE" = true ]; then
  BUILD_ARGS="--no-cache"
  log "Forcing rebuild without cache..."
fi

# Create a directory for persistent SSL certificates if it doesn't exist
CERT_DIR="/opt/friday-api/certs"
if [ ! -d "$CERT_DIR" ]; then
    if ! sudo mkdir -p "$CERT_DIR"; then
        warn "Failed to create certificate directory. Continuing anyway..."
    else
        log "Created persistent certificate directory: $CERT_DIR"
    fi
fi

# Ensure correct permissions for the certificates directory
if [ "$EUID" -eq 0 ]; then
    # If running as root, directly change ownership
    chown -R deploy:deploy "$CERT_DIR" || warn "Failed to update certificate permissions. Continuing anyway..."
else
    # If running as deploy user, use sudo
    sudo chown -R deploy:deploy "$CERT_DIR" || warn "Failed to update certificate permissions. Continuing anyway..."
fi
log "Certificate directory setup completed"

if [ "$RESTART_ONLY" = true ]; then
  log "Restarting containers without rebuilding..."
  if [ "$EXTERNAL_DB" = true ]; then
    # Stop containers but preserve volumes
    docker compose -f docker-compose.no-db.yml down --remove-orphans
    docker compose -f docker-compose.no-db.yml up -d
  else
    docker compose -f docker-compose.yml down --remove-orphans
    docker compose -f docker-compose.yml up -d
  fi
else
  if [ "$EXTERNAL_DB" = true ]; then
    log "Using the 'no-db' Docker Compose file..."
    # Stop containers but preserve volumes
    docker compose -f docker-compose.no-db.yml down --remove-orphans
    docker compose -f docker-compose.no-db.yml build $BUILD_ARGS
    docker compose -f docker-compose.no-db.yml up -d
  else
    log "Using the default Docker Compose file (with local MySQL)..."
    docker compose -f docker-compose.yml down --remove-orphans
    docker compose -f docker-compose.yml build $BUILD_ARGS
    docker compose -f docker-compose.yml up -d
  fi
fi

log "Verifying containers..."
docker compose ps

log "Deployment finished. SSL certificates are preserved in $CERT_DIR"
