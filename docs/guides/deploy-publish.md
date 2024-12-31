Below is a detailed, step-by-step guide on how to deploy the web app onto a DigitalOcean (DO) droplet using Docker (and Docker Compose). This guide assumes you have a working knowledge of basic Linux commands, Docker, and Git. We’ll make it as “hands-on” as possible:

---
## **1. Droplet Provisioning & Basic System Setup**

### 1.1 Create a new Ubuntu Droplet on DigitalOcean
1. Sign in to your DigitalOcean account.
2. Click **Create** → **Droplets**.
3. Select the **Ubuntu** image (latest LTS version recommended, e.g., Ubuntu 22.04).
4. Choose the Droplet size (at least 1 GB RAM for a small project, scale as needed).
5. Choose a region close to you or your users.
6. Under **Authentication**, either select **SSH keys** (recommended) or set a **root password**.
7. Optionally give it a name (e.g. `my-friday-api`) and tag.
8. Click **Create Droplet**. Wait for the droplet to provision.

### 1.2 Configure SSH access & firewall (ufw)
1. From your local machine, run:
   ```bash
   ssh root@<YOUR_DROPLET_IP>
   ```
2. (Optional) **Update system packages**:
   ```bash
   apt-get update && apt-get upgrade -y
   ```
3. **Enable firewall** (ufw) rules for SSH (port 22), HTTP (80), and HTTPS (443). For example:
   ```bash
   ufw allow OpenSSH
   ufw allow 80
   ufw allow 443
   ufw enable
   ```
   Confirm with `ufw status`.

### 1.3 Create a non-root user (recommended)
1. Inside the Droplet:
   ```bash
   adduser deploy
   usermod -aG sudo deploy
   ```
2. Then logout and re-login as `deploy@<YOUR_DROPLET_IP>` once you set up an SSH key for the `deploy` user or a password.

---

## **2. Install Dependencies on Droplet**

### 2.1 Install Docker
1. For Ubuntu, install using the official Docker docs approach:
   ```bash
   sudo apt-get remove docker docker-engine docker.io containerd runc
   sudo apt-get update
   sudo apt-get install ca-certificates curl gnupg lsb-release
   sudo mkdir -p /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
   echo \
   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt-get update
   sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
   ```
2. **Optional**: Add your deploy user to the `docker` group:
   ```bash
   sudo usermod -aG docker deploy
   ```
   Then logout & re-login for changes to apply.

### 2.2 Install Docker Compose
- If you installed Docker via the method above (Docker Engine + `docker-compose-plugin`), you should have a `docker compose` command available (note that the newer versions use `docker compose` instead of `docker-compose`).
- Confirm with:
  ```bash
  docker compose version
  ```
- If you prefer the old `docker-compose` binary, follow the [official instructions](https://docs.docker.com/compose/install/) to install a stable release, but the plugin is typically enough.

### 2.3 (Optional) Install Git / Set up CI/CD
- If you plan to clone directly from GitHub:
  ```bash
  sudo apt-get install git -y
  ```
- Alternatively, plan a CI/CD strategy (e.g., GitHub Actions → push to registry → droplet pulls images).
- For this guide, we assume we’ll do a direct `git clone` on the droplet.

---

## **3. Prepare the Application for Containerization**

### 3.1 Write a Dockerfile for the FastAPI application
Inside your project root, create a `Dockerfile` (example):
```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.10-slim

# Create a working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy rest of the code
COPY . /app

# Expose port (FastAPI default)
EXPOSE 8000

# Env var to run in production mode if needed
ENV ENV=production

# Start the app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
Adjust as needed depending on your structure (pydantic 2.0, or additional dependencies, etc.).

### 3.2 Write a Docker Compose file that includes the services
Create a `docker-compose.yml` in the project root. Example:
```yaml
version: "3.9"

services:
  api:
    build: .
    container_name: friday_api
    restart: always
    env_file:
      - .env
    depends_on:
      - db
      - redis
    ports:
      - "80:8000"
    volumes:
      - ./logs:/app/logs

  db:
    image: mysql:8.0
    container_name: friday_db
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: "${DB_ROOT_PASSWORD}"
      MYSQL_DATABASE: "${DATABASE_NAME}"
      MYSQL_USER: "${DATABASE_USERNAME}"
      MYSQL_PASSWORD: "${DATABASE_PASSWORD}"
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:6.2-alpine
    container_name: friday_redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```
**Notes**:
- The `api` service builds from the local Dockerfile.
- The environment variables are loaded from a `.env` file.
- We mount a `logs` folder for the API logs.
- For MySQL and Redis, we define named volumes (`mysql_data`, `redis_data`) that persist data.

### 3.3 Configure persistent volumes for MySQL & Redis
- As shown above, `mysql_data` and `redis_data` volumes ensure data persists if containers restart.
- For major updates or droplet re-creations, consider DO Block Storage or manual snapshot backups.

---

## **4. Configure Environment Variables & Secrets**

### 4.1 Use a `.env` file
Create a `.env` file in your project root, e.g.:
```
# .env

DB_ROOT_PASSWORD=rootpass123
DATABASE_NAME=fridaydb
DATABASE_USERNAME=fridayuser
DATABASE_PASSWORD=fridaypass
REDIS_HOST=redis
REDIS_PORT=6379
ENV=production
```
- Add any additional secrets (like `JWT_SECRET_KEY` or API keys).
- **Never commit the `.env` file to public repos**. If needed, add `.env` to `.gitignore`.

### 4.2 Protect secrets
- On production servers, store this `.env` file carefully or pass environment variables via the droplet environment or Docker Secrets approach if desired.

---

## **5. Setup the Deployment Process**

### 5.1 Clone the repository onto the droplet
From your droplet:
```bash
cd ~  # or /var/www, depends on your structure
git clone https://github.com/<your_username>/<your_repo>.git
cd <your_repo>
```
*(If your code is private, set up SSH key access or personal token.)*

### 5.2 Build and run the Docker Compose stack
1. Build & start services:
   ```bash
   docker compose build
   docker compose up -d
   ```
2. Check containers:
   ```bash
   docker compose ps
   docker logs friday_api --follow
   ```
   or
   ```bash
   docker logs friday_api
   docker logs friday_db
   docker logs friday_redis
   ```

### 5.3 Create a script to automate pulling latest code & restarting containers
**deploy.sh** (example):
```bash
#!/usr/bin/env bash
set -e

# 1. Pull latest code
echo "Pulling latest code..."
git pull origin main

# 2. Build images
echo "Building docker images..."
docker compose build

# 3. Run migrations if needed
# e.g. docker compose run api alembic upgrade head

# 4. Restart containers
echo "Restarting containers..."
docker compose up -d

echo "Deployment complete."
```
Give it execute permission: `chmod +x deploy.sh`.

Then you can do:
```bash
./deploy.sh
```
*(Ensure you’re on the correct branch—e.g., `git checkout main`—before running.)*

### 5.4 Handle zero-downtime or minimal downtime
- If you need zero downtime, consider a more advanced approach (Docker swarm, load balancer, or a separate container that hot-swaps).
- For many small projects, a few seconds of downtime is acceptable.

---

## **6. Logging & Monitoring**

### 6.1 Configure logging in Docker Compose
- We used a volume `./logs:/app/logs` in the `api` service. Inside the app, ensure logs are written to `/app/logs/app.log`.
- Alternatively, configure Docker’s logging drivers or syslog:
  ```yaml
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
  ```

### 6.2 External logging or monitoring
- For more advanced setups, push logs to ELK, Datadog, or a DO Logging solution.
- Keep an eye on disk usage for logs.

---

## **7. Domain & SSL Setup**

### 7.1 Acquire a domain & point DNS to the Droplet’s IP
- In your domain registrar’s DNS settings, create an A-record pointing to `<DROPLET_PUBLIC_IP>`.
- e.g. `mydomain.com` → `123.123.123.123`.

### 7.2 Use an Nginx reverse proxy container with Let’s Encrypt
One approach is to have an additional `nginx` container that listens on 80/443 and forwards requests to the `api` service (on port 8000 internally). Something like [jwilder/nginx-proxy + jrcs/letsencrypt-nginx-proxy-companion](https://github.com/nginx-proxy/docker-letsencrypt-nginx-proxy-companion) can automate SSL certificates. Example `docker-compose.yml` snippet might be:

```yaml
services:
  nginx-proxy:
    image: jwilder/nginx-proxy:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - nginx_certs:/etc/nginx/certs:rw
    depends_on:
      - api
    restart: always

  nginx-proxy-letsencrypt:
    image: jrcs/letsencrypt-nginx-proxy-companion
    depends_on:
      - nginx-proxy
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - nginx_certs:/etc/nginx/certs:rw
    environment:
      NGINX_PROXY_CONTAINER: nginx-proxy
    restart: always

  api:
    # build your app container
    environment:
      - VIRTUAL_HOST=mydomain.com
      - LETSENCRYPT_HOST=mydomain.com
      - LETSENCRYPT_EMAIL=admin@mydomain.com
```
Then the `nginx-proxy` + `letsencrypt` containers automatically request a certificate and route traffic.

### 7.3 Use a separate approach
- You could install Nginx directly on the droplet, Certbot, etc. If so, you’d do `sudo apt-get install nginx`, place a reverse proxy config for your FastAPI container, and run `certbot --nginx`.
- But the containerized approach keeps everything in Docker.

### 7.4 Validate HTTPS
- Visit `https://mydomain.com`, confirm the SSL certificate.

---

## **8. Persistence & Data Backups**

### 8.1 Persist MySQL data
- As we did with the `mysql_data` volume in Docker Compose, your DB files are stored under `/var/lib/docker/volumes/<project>_mysql_data`.
- For robust backups, consider:
  ```bash
  docker compose exec db mysqldump -u root -p$DB_ROOT_PASSWORD $DATABASE_NAME > backup.sql
  ```
  Or a scheduled cron job.

### 8.2 Redis data
- Similarly, `redis_data` volume persists. However, many prefer Redis ephemeral usage. If you do want persistent, ensure that your `redis.conf` has `appendonly yes` or so.

### 8.3 Droplet Snapshots
- DigitalOcean has a droplet snapshot feature. You can snapshot the entire server as a fallback.

---

## **9. CI/CD or Manual Updates**

### 9.1 Manual approach
- SSH in, `git pull`, `docker compose build`, `docker compose up -d`.

### 9.2 Automate with GitHub Actions
- A popular approach is to push to main → GitHub Actions builds Docker image → push to Docker Hub or GitHub Container Registry → droplet pulls updated image → restarts container.

### 9.3 Consistent environment
- Keep your `.env` file consistent. For staging vs production, you might have separate `.env` or environment variable overrides.

---

## **10. Ongoing Maintenance**

### 10.1 Security patches
- `sudo apt-get update && sudo apt-get upgrade` regularly.
- Keep Docker images updated: `docker compose pull` or rebuild images with updated base images.

### 10.2 Monitor usage
- Tools like `htop`, `docker stats`, or DO’s monitoring tab.

### 10.3 Scaling
- If usage grows, resize the droplet or horizontally scale with multiple droplets behind a DO Load Balancer.

---

## **Conclusion**

With these detailed steps, you should be able to:

1. Create an Ubuntu-based DigitalOcean droplet.
2. Install Docker + Docker Compose.
3. Clone your FastAPI-based repository.
4. Containerize the app, MySQL, and Redis.
5. Configure environment variables & volumes for persistent data.
6. Launch via `docker compose up -d`.
7. Add a domain, set up SSL (via container or Nginx directly).
8. Keep the droplet & images updated.

By following the script-based approach (like `deploy.sh`) or a Git-based CI/CD pipeline, you can seamlessly pull new code and rebuild your stack with minimal downtime. Logging is handled by standard Docker logs or by mounting volumes. Persistent volumes store MySQL/Redis data. For better resilience, schedule backups or snapshots in DigitalOcean.

**Done!** Now you have a robust, Dockerized, repeatable deployment process for your web app on DigitalOcean.
