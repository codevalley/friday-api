# **Friday API Deployment Guide**

## **1. Provision a DigitalOcean Droplet**

1. Log in to [DigitalOcean](https://cloud.digitalocean.com/).
2. Click **Create → Droplets**.
3. Choose an **Ubuntu** image (e.g., 22.04 LTS).
4. Pick a Droplet size (1GB RAM is fine for minimal workloads).
5. Select a region (closest to you or your users).
6. Under **Authentication**, set an SSH key (recommended) or password.
7. Optionally name/tag the Droplet, then **Create**.

> **Tip**: Wait until the Droplet is fully provisioned. You’ll get a public IP address for it.

---

## **2. SSH & Basic Setup**

1. SSH into the Droplet:
   ```bash
   ssh root@<YOUR_DROPLET_IP>
   ```
2. Update packages:
   ```bash
   apt-get update && apt-get upgrade -y
   ```
3. (Recommended) Create a non-root deploy user:
   ```bash
   adduser deploy
   usermod -aG sudo deploy
   ```
   Then log out and back in as `deploy@<YOUR_DROPLET_IP>` if you prefer to run as a non-root user.

4. Configure UFW (firewall):
   ```bash
   sudo ufw allow OpenSSH
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ufw status
   ```
   This ensures HTTP (80) + HTTPS (443) is open.

---

## **3. Install Docker & Docker Compose**

> If you prefer to let the `deploy.sh` handle Docker installation, skip these steps and run the script with `--docker`. Otherwise, do them manually here.

**Manual approach**:
```bash
# Remove old packages if any
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install Docker using official instructions
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# (Optional) Add your deploy user to the docker group
sudo usermod -aG docker deploy
```
Then logout and back in to apply group membership.

To confirm:
```bash
docker compose version
```
You should see something like `Docker Compose version v2.x`.

---

## **4. Clone Your `friday-api` Repo**

1. On the droplet, move to your desired directory:
   ```bash
   cd ~
   ```
2. Clone your GitHub repo:
   ```bash
   git clone https://github.com/codevalley/friday-api.git
   cd friday-api
   ```
   *(If it’s private, set up SSH keys or use personal access tokens.)*

3. You should see your repo files: `deploy.sh`, `docker-compose.yml`, `Dockerfile`, `.env.sample`, etc.

---

## **5. Environment Variables & Configuration**

1. Within the `friday-api` folder, **create** your `.env` file if not already present. You can copy from `.env.sample`:
   ```bash
   cp .env.sample .env
   ```
2. **Edit** `.env` to set:
   - Domain / email for your SSL config (e.g., `FRIDAY_DOMAIN=api.acme.me`, `LETSENCRYPT_EMAIL=admin@acme.com`).
   - DB credentials if using local MySQL. If using an external DB, set `EXTERNAL_DB=true` and update `DATABASE_HOSTNAME`, `DATABASE_PORT`, etc. accordingly.
   - Customize any secrets (like `JWT_SECRET_KEY`), or let `deploy.sh` generate one if it’s empty.

3. Keep `.env` **private** (it shouldn’t be committed to the repo).

---

## **6. Understanding the `deploy.sh` Script**

Your `deploy.sh` includes flags such as:
- `--docker`: Installs Docker if not found.
- `--fetch-code`: Pulls latest changes from `git`.
- `--external-db`: If you want to skip local MySQL.

A typical usage:
```bash
sudo ./deploy.sh api.acme.me admin@acme.com --docker --fetch-code
```
This will:
1. **Check** if running as root (or sudo).
2. **Install** Docker (if `--docker`).
3. **Pull** latest code from `git` (if `--fetch-code`).
4. **Set** environment variables (like `LETSENCRYPT_HOST`).
5. **Generate** a random `JWT_SECRET_KEY` if it is empty in `.env`.
6. **Build** Docker images and run `docker compose up -d`.
   - If `--external-db`, it uses `docker-compose.no-db.yml` instead.

> If you don’t need local MySQL, you’d pass `--external-db` so the script picks the no-db compose file.

---

## **7. Running the Deployment**

1. Ensure your domain DNS is pointed to the droplet IP:
   - In your domain registrar, set an A record, e.g. `api.acme.me` → `YOUR_DROPLET_IP`.

2. Inside the `friday-api` folder, run the deploy script with your desired flags. For example:
   ```bash
   cd ~/friday-api
   sudo chmod +x deploy.sh
   sudo ./deploy.sh api.acme.me admin@acme.com --docker --fetch-code
   ```
   Explanation:
   - `api.acme.me` = Domain you want to serve on.
   - `admin@acme.com` = Email for Let’s Encrypt certificates.
   - `--docker` = Installs Docker if needed.
   - `--fetch-code` = Stashes local changes and pulls the latest from main branch.

> **Note**: If you do **not** want local MySQL, add `--external-db`.

3. The script will:
   - Possibly install Docker + Compose plugin.
   - Pull or stash + pull your latest code from GitHub if `--fetch-code`.
   - Build your image from the `Dockerfile`.
   - Spin up containers defined in `docker-compose.yml` (or `docker-compose.no-db.yml`) with `-d` (detached mode).
   - Print container statuses.

---

## **8. Verifying the Deployment**

1. After the script finishes, check container statuses:
   ```bash
   docker compose ps
   ```
   or
   ```bash
   docker ps
   ```
2. Check logs if needed:
   ```bash
   docker compose logs -f
   ```
3. Visit your domain in a browser:
   - e.g. `https://api.acme.me`
   - If using the jwilder + letsencrypt approach, it may take a minute or so to issue the certificate.

4. Confirm you can reach `https://<yourdomain>/docs` for the FastAPI docs page.

---

## **9. Making Future Updates**

1. **SSH** into your droplet as `deploy` or root, navigate to `~/friday-api`.
2. Run:
   ```bash
   sudo ./deploy.sh api.acme.me admin@acme.com --fetch-code
   ```
   This will:
   - `git pull` main again,
   - Re-build images,
   - Restart containers,
   - Keep your environment + volumes intact.
3. If you need to re-generate SSL or forcibly renew:
   ```bash
   sudo ./deploy.sh api.acme.me admin@acme.com --setup-ssl --force-ssl
   ```
   (If you have that logic in your script.)

---

## **10. (Optional) Using No-DB or External DB**

- If you don’t need a local MySQL container, you likely have a second compose file (e.g., `docker-compose.no-db.yml`).
- In `.env`, set `EXTERNAL_DB=true`, specify external DB settings.
- Then run:
  ```bash
  sudo ./deploy.sh api.acme.me admin@acme.com --external-db
  ```
  The script references `docker-compose.no-db.yml` instead of the default `docker-compose.yml`.

---

## **Additional Pointers**

- **SSL Renewal**: The jwilder + letsencrypt container automatically renews certificates.
- **Logs**: Your API logs go into the container’s stdout or into a mounted volume (e.g., `./logs:/app/logs`). Check them with `docker compose logs -f api`.
- **Persistence**:
  - Redis data stored in volume `redis_data`.
  - MySQL data in `mysql_data` if you use a local MySQL container.
- **Backing up**:
  - Periodic droplet snapshots on DO.
  - Or if using external DB, rely on DB provider backups.

---

## **Managing queues and workers**

If your system has multiple queues (say note_enrichment, email_notifications, etc.), you can either:

Run a single worker listening on multiple queues:
```yaml
command: >
  rq worker note_enrichment email_notifications --url redis://redis:6379
```

Or define multiple worker services in Docker Compose, each dedicated to a specific queue.
For example:
```yaml
worker-note:
  build: .
  container_name: worker_note
  command: rq worker note_enrichment --url redis://redis:6379
  ...

worker-email:
  build: .
  container_name: worker_email
  command: rq worker email_notifications --url redis://redis:6379
  ...
```
Either approach is fine; it depends on your preference for separation and scaling.

### **Optional: Scaling workers**

If you have heavy queue traffic and need more throughput, you can scale your RQ worker service with multiple replicas:
```yaml
docker compose up -d --scale worker=3
```
This spins up 3 containers of the worker service, all listening to the same queue(s). RQ will distribute jobs among them. But note you need enough CPU/memory to handle that load.

---

## **Wrapping Up**

1. You have a **`deploy.sh`** that automates Docker installation, code pulling, environment injection, and Docker Compose usage.
2. A **`docker-compose.yml`** (plus an optional no-db variant) orchestrates your containers.
3. The **`Dockerfile`** builds your FastAPI image.
4. Domain + SSL are handled by **`jwilder/nginx-proxy`** + **`letsencrypt-nginx-proxy-companion`** automatically.

**In short**:
- **Clone** → **Configure `.env`** → **Run** `sudo ./deploy.sh <domain> <email>` (with or without `--external-db`) → **Success**.

You can now maintain your application by pulling changes and re-running the script. The jwilder proxy + let’s encrypt automatically refreshes certs. Volumes store persistent data. This is a straightforward, reproducible way to run your **Friday API** on a DO droplet!

**Enjoy your newly deployed API!**
