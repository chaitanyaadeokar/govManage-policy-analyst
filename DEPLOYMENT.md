# Deployment Guide - Agentic Governance System

## Production Deployment Guide

This guide covers deploying the Agentic Governance System to production environments.

---

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or Windows Server
- **Python**: 3.9 or higher
- **MongoDB**: 4.4 or higher
- **RAM**: Minimum 4GB, recommended 8GB+
- **CPU**: Minimum 2 cores, recommended 4+ cores
- **Disk**: 20GB+ for application and logs

### External Services
- **Groq API**: Active API key with sufficient quota
- **MongoDB**: Hosted instance or self-hosted cluster
- **Load Balancer** (optional): For multi-instance deployment
- **Monitoring** (optional): Prometheus, Grafana, or similar

---

## Installation Steps

### 1. System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+
sudo apt install python3.9 python3.9-venv python3-pip -y

# Install MongoDB (if self-hosting)
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

### 2. Application Setup

```bash
# Create application directory
sudo mkdir -p /opt/agentic-governance
cd /opt/agentic-governance

# Clone repository
git clone <your-repo-url> .

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Create production environment file
cp .env.example .env.production

# Edit configuration
nano .env.production
```

**Production .env.production:**
```env
# API Configuration
API_PORT=8000
API_HOST=0.0.0.0
WORKERS=4

# Groq API
GROQ_API_KEY=your_production_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

# MongoDB
MONGO_URI=mongodb://username:password@mongodb-host:27017/
MONGO_DB_NAME=govmanage_prod

# Security
API_SECRET_KEY=generate_strong_random_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/agentic-governance/app.log

# Performance
MAX_AGENT_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=60
MEMORY_PERSISTENCE_INTERVAL=300
```

### 4. Database Initialization

```bash
# Connect to MongoDB
mongo mongodb://localhost:27017

# Create database and user
use govmanage_prod
db.createUser({
  user: "govmanage_user",
  pwd: "strong_password_here",
  roles: [
    { role: "readWrite", db: "govmanage_prod" }
  ]
})

# Exit mongo shell
exit

# Run database seeding (creates default data)
source venv/bin/activate
python -c "from database import db; print('Database initialized')"
```

---

## Systemd Service Setup

### Create Service File

```bash
sudo nano /etc/systemd/system/agentic-governance.service
```

**Service Configuration:**
```ini
[Unit]
Description=Agentic Governance API Service
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/agentic-governance
Environment="PATH=/opt/agentic-governance/venv/bin"
EnvironmentFile=/opt/agentic-governance/.env.production
ExecStart=/opt/agentic-governance/venv/bin/uvicorn api:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log \
    --proxy-headers
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
KillSignal=SIGQUIT
TimeoutStopSec=5
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Set permissions
sudo chown -R www-data:www-data /opt/agentic-governance
sudo chmod 755 /opt/agentic-governance

# Create log directory
sudo mkdir -p /var/log/agentic-governance
sudo chown www-data:www-data /var/log/agentic-governance

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable agentic-governance

# Start service
sudo systemctl start agentic-governance

# Check status
sudo systemctl status agentic-governance
```

---

## Nginx Reverse Proxy Setup

### Install Nginx

```bash
sudo apt install nginx -y
```

### Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/agentic-governance
```

**Nginx Configuration:**
```nginx
upstream agentic_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name governance.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name governance.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/governance.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/governance.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logging
    access_log /var/log/nginx/agentic-governance-access.log;
    error_log /var/log/nginx/agentic-governance-error.log;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    # Proxy Settings
    location / {
        proxy_pass http://agentic_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no rate limit)
    location /api/v2/health {
        limit_req off;
        proxy_pass http://agentic_backend;
    }
}
```

### Enable Site

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/agentic-governance /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## SSL Certificate Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d governance.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

---

## Monitoring Setup

### Prometheus Metrics

Add to `api.py`:
```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# Metrics
request_count = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('api_request_duration_seconds', 'Request duration', ['method', 'endpoint'])

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

### Log Rotation

```bash
sudo nano /etc/logrotate.d/agentic-governance
```

```
/var/log/agentic-governance/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload agentic-governance > /dev/null 2>&1 || true
    endscript
}
```

---

## Backup Strategy

### MongoDB Backup Script

```bash
sudo nano /opt/agentic-governance/scripts/backup-mongodb.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/backup/mongodb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MONGO_URI="mongodb://username:password@localhost:27017"
DB_NAME="govmanage_prod"

mkdir -p $BACKUP_DIR

# Dump database
mongodump --uri="$MONGO_URI" --db=$DB_NAME --out=$BACKUP_DIR/$TIMESTAMP

# Compress
tar -czf $BACKUP_DIR/backup_$TIMESTAMP.tar.gz -C $BACKUP_DIR $TIMESTAMP
rm -rf $BACKUP_DIR/$TIMESTAMP

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: backup_$TIMESTAMP.tar.gz"
```

### Schedule Backups

```bash
# Make executable
sudo chmod +x /opt/agentic-governance/scripts/backup-mongodb.sh

# Add to crontab
sudo crontab -e

# Add line (daily at 2 AM)
0 2 * * * /opt/agentic-governance/scripts/backup-mongodb.sh >> /var/log/mongodb-backup.log 2>&1
```

---

## Health Checks

### Application Health Check

```bash
# Check API health
curl https://governance.yourdomain.com/api/v2/health

# Expected response:
{
  "status": "healthy",
  "components": {
    "api": "healthy",
    "database": "healthy",
    "agents": "healthy"
  },
  "timestamp": "2026-04-08T10:30:00"
}
```

### Service Status

```bash
# Check service status
sudo systemctl status agentic-governance

# Check logs
sudo journalctl -u agentic-governance -f

# Check Nginx
sudo systemctl status nginx

# Check MongoDB
sudo systemctl status mongod
```

---

## Scaling Strategies

### Vertical Scaling

```bash
# Increase workers in service file
sudo nano /etc/systemd/system/agentic-governance.service

# Change --workers parameter
ExecStart=/opt/agentic-governance/venv/bin/uvicorn api:app \
    --workers 8  # Increase from 4 to 8

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart agentic-governance
```

### Horizontal Scaling

Deploy multiple instances behind a load balancer:

```
┌─────────────┐
│Load Balancer│
└──────┬──────┘
       │
   ┌───┴───┬───────┬───────┐
   │       │       │       │
   ▼       ▼       ▼       ▼
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│Inst1│ │Inst2│ │Inst3│ │Inst4│
└──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
   │       │       │       │
   └───────┴───┬───┴───────┘
               │
          ┌────▼────┐
          │ MongoDB │
          │ Cluster │
          └─────────┘
```

---

## Security Hardening

### Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow MongoDB (only from app servers)
sudo ufw allow from <app-server-ip> to any port 27017

# Enable firewall
sudo ufw enable
```

### Application Security

1. **API Authentication**: Implement JWT tokens
2. **Rate Limiting**: Configure in Nginx (already done above)
3. **Input Validation**: Pydantic models handle this
4. **SQL Injection**: Not applicable (using MongoDB)
5. **XSS Protection**: Headers configured in Nginx

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u agentic-governance -n 50

# Check permissions
ls -la /opt/agentic-governance

# Check Python environment
source /opt/agentic-governance/venv/bin/activate
python -c "import fastapi; print('OK')"
```

### High Memory Usage

```bash
# Check memory
free -h

# Check process memory
ps aux | grep uvicorn

# Reduce workers if needed
sudo nano /etc/systemd/system/agentic-governance.service
```

### Slow Response Times

```bash
# Check MongoDB performance
mongo --eval "db.serverStatus().connections"

# Check agent iterations
# Review logs for excessive tool calls

# Consider caching frequently accessed data
```

---

## Rollback Procedure

```bash
# Stop service
sudo systemctl stop agentic-governance

# Restore previous version
cd /opt/agentic-governance
git checkout <previous-commit-hash>

# Restore database backup if needed
mongorestore --uri="mongodb://..." --db=govmanage_prod /backup/mongodb/backup_TIMESTAMP

# Restart service
sudo systemctl start agentic-governance

# Verify
curl https://governance.yourdomain.com/api/v2/health
```

---

## Maintenance Windows

### Planned Maintenance

1. Announce maintenance window
2. Set API to read-only mode (if supported)
3. Perform updates
4. Run smoke tests
5. Resume normal operations
6. Monitor for issues

### Zero-Downtime Deployment

1. Deploy to new instances
2. Run health checks
3. Add to load balancer
4. Remove old instances
5. Monitor metrics

---

## Support & Monitoring

### Key Metrics to Monitor

- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (%)
- Agent reasoning iterations
- Memory usage
- CPU usage
- Database connections
- Decision distribution (Approve/Block/Review)

### Alerting Thresholds

- Error rate > 5%
- Response time p95 > 30s
- Memory usage > 80%
- CPU usage > 80%
- Block rate > 30%
- Database connection failures

---

## Compliance & Audit

### Audit Log Retention

```bash
# Configure retention in MongoDB
mongo govmanage_prod

db.audit_logs.createIndex(
  { "timestamp": 1 },
  { expireAfterSeconds: 7776000 }  // 90 days
)
```

### Compliance Reports

Generate monthly compliance reports:
```bash
python scripts/generate_compliance_report.py --month 2026-04
```

---

**Deployment Checklist**: ✅ Complete  
**Last Updated**: April 8, 2026  
**Next Review**: July 8, 2026
