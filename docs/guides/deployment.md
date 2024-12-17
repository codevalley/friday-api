# Deployment Guide

## Prerequisites

- Python 3.12+
- MySQL 8.0+
- Poetry for dependency management
- Docker (optional)

## Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/friday-api.git
cd friday-api
```

2. Install dependencies:
```bash
poetry install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
mysql -u root -p < scripts/init_database.sql
```

5. Run migrations:
```bash
alembic upgrade head
```

6. Start the development server:
```bash
uvicorn main:app --reload
```

## Environment Variables

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=friday
DB_PASS=your_password
DB_NAME=fridaystore

# JWT
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=60

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

## Database Migrations

### Create a new migration:
```bash
alembic revision -m "description_of_changes"
```

### Apply migrations:
```bash
alembic upgrade head
```

### Rollback migrations:
```bash
alembic downgrade -1  # Rollback one step
alembic downgrade base  # Rollback all
```

## Docker Deployment

1. Build the image:
```bash
docker build -t friday-api .
```

2. Run with Docker:
```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name friday-api \
  friday-api
```

3. Run with Docker Compose:
```bash
docker-compose up -d
```

## Production Deployment

### System Requirements
- 2 CPU cores
- 4GB RAM
- 20GB storage
- Ubuntu 22.04 LTS

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Systemd Service
```ini
[Unit]
Description=Friday API
After=network.target

[Service]
User=friday
WorkingDirectory=/opt/friday-api
Environment=PATH=/opt/friday-api/.venv/bin:$PATH
ExecStart=/opt/friday-api/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### SSL/TLS Setup
1. Install Certbot:
```bash
apt install certbot python3-certbot-nginx
```

2. Obtain certificate:
```bash
certbot --nginx -d api.example.com
```

## Monitoring

### Prometheus Metrics
Available at `/metrics`:
- Request latency
- Error rates
- Active connections
- Resource usage

### Logging
Logs are written to:
- Application: `/var/log/friday-api/app.log`
- Access: `/var/log/friday-api/access.log`
- Error: `/var/log/friday-api/error.log`

### Health Checks
- `/health`: Basic health check
- `/health/live`: Liveness probe
- `/health/ready`: Readiness probe

## Backup and Recovery

### Database Backup
```bash
# Daily backup
mysqldump -u friday -p fridaystore > backup_$(date +%Y%m%d).sql

# Restore from backup
mysql -u friday -p fridaystore < backup_20231214.sql
```

### Automated Backups
```bash
# /etc/cron.daily/friday-backup
#!/bin/bash
mysqldump -u friday -p fridaystore > /backup/friday_$(date +%Y%m%d).sql
find /backup -name "friday_*.sql" -mtime +7 -delete
```

## Security

1. API Authentication:
   - JWT tokens
   - Rate limiting
   - IP whitelisting

2. Database Security:
   - TLS encryption
   - User permissions
   - Query logging

3. Server Security:
   - Firewall rules
   - Regular updates
   - Fail2ban

## Troubleshooting

### Common Issues

1. Database Connection:
```bash
# Check MySQL status
systemctl status mysql

# Check connectivity
mysql -u friday -p -h localhost fridaystore
```

2. API Server:
```bash
# Check logs
tail -f /var/log/friday-api/error.log

# Check process
ps aux | grep uvicorn
```

3. Performance:
```bash
# Monitor resources
top -u friday

# Check slow queries
tail -f /var/log/mysql/slow-query.log
```

### Support

For issues:
1. Check logs
2. Review documentation
3. Open GitHub issue
4. Contact support team
