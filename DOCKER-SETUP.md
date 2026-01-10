# Docker Setup Guide

Run the entire Soulfra blog network with Docker - Flask app + Ollama + Nginx.

## Quick Start

### 1. Install Docker

**Mac:**
```bash
brew install --cask docker
# Open Docker Desktop and start it
```

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. Setup Environment Variables

Create `.env` file:

```bash
cat > .env << 'EOF'
SECRET_KEY=your-secret-key-here-change-this
ANTHROPIC_API_KEY=sk-ant-your-key-here
FLASK_ENV=production
EOF
```

Generate secret key:
```bash
python3 -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')" >> .env
```

### 3. Build and Run

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

Services will be available at:
- Flask app: http://localhost:5001
- Ollama: http://localhost:11434
- Nginx (if enabled): http://localhost:80

### 4. Setup Ollama Models

Pull the models you need:

```bash
# Pull llama3.2 (recommended)
docker-compose exec ollama ollama pull llama3.2

# Pull other models
docker-compose exec ollama ollama pull llama2
docker-compose exec ollama ollama pull codellama

# List installed models
docker-compose exec ollama ollama list
```

### 5. Initialize Database

```bash
# Run database migration
docker-compose exec web python3 migrate_blog_network.py

# Create first admin user (optional)
docker-compose exec web python3 -c "
from db_helpers import create_user
from admin_system import AdminSystem
user_id = create_user('admin', 'admin@soulfra.com', 'changeme')
admin = AdminSystem()
admin.set_user_role(user_id, 'owner', user_id)
print(f'Created admin user with ID: {user_id}')
"
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Nginx (Port 80)                │
│        Reverse Proxy + SSL + Cache          │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│         Flask App (Port 5001)               │
│   - Domain Manager                          │
│   - Admin Dashboard                         │
│   - Workflows                                │
│   - User Management                         │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│           Ollama (Port 11434)               │
│   - LLM Models (llama3.2, etc.)            │
│   - Chat API                                │
│   - Code Generation                         │
└─────────────────────────────────────────────┘
```

---

## Container Management

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart web

# Rebuild after code changes
docker-compose up -d --build web
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f ollama

# Last 100 lines
docker-compose logs --tail=100 web
```

### Shell Access

```bash
# Access Flask container
docker-compose exec web bash

# Access Ollama container
docker-compose exec ollama sh

# Run Python scripts
docker-compose exec web python3 automation_workflows.py auto-syndicate 24
```

---

## Data Persistence

### Volumes

Docker volumes persist data between restarts:

- `./data` - SQLite database
- `./domains` - Domain files
- `ollama-data` - Ollama models and cache

### Backup Database

```bash
# Backup
docker-compose exec web cp /app/data/soulfra.db /app/data/soulfra-backup-$(date +%Y%m%d).db

# Or from host
cp data/soulfra.db data/soulfra-backup-$(date +%Y%m%d).db
```

### Restore Database

```bash
# Copy backup into container
docker cp soulfra-backup.db soulfra-web:/app/data/soulfra.db

# Restart app
docker-compose restart web
```

---

## Production Deployment

### 1. Setup SSL with Let's Encrypt

```bash
# Install certbot
docker run -it --rm --name certbot \
  -v "/etc/letsencrypt:/etc/letsencrypt" \
  -v "/var/lib/letsencrypt:/var/lib/letsencrypt" \
  certbot/certbot certonly --standalone \
  -d soulfra.com -d www.soulfra.com

# Copy certificates
mkdir -p ssl
cp /etc/letsencrypt/live/soulfra.com/fullchain.pem ssl/
cp /etc/letsencrypt/live/soulfra.com/privkey.pem ssl/

# Uncomment HTTPS server in nginx.conf
# Restart nginx
docker-compose restart nginx
```

### 2. Auto-Renewal

Add to crontab:

```bash
0 3 * * * docker run --rm -v "/etc/letsencrypt:/etc/letsencrypt" certbot/certbot renew --quiet && docker-compose restart nginx
```

### 3. Environment Security

Never commit `.env` to git:

```bash
echo ".env" >> .gitignore
```

### 4. Resource Limits

Update `docker-compose.yml` to add limits:

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          memory: 512M

  ollama:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          memory: 2G
```

---

## GPU Support for Ollama

If you have an NVIDIA GPU:

### 1. Install NVIDIA Container Toolkit

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 2. Enable GPU in docker-compose.yml

Uncomment the GPU section:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### 3. Verify GPU Access

```bash
docker-compose exec ollama nvidia-smi
```

---

## Monitoring

### Health Checks

```bash
# Check if services are healthy
docker-compose ps

# Web app health
curl http://localhost:5001/

# Ollama health
curl http://localhost:11434/api/tags
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

### Logging to File

```bash
# Export logs
docker-compose logs > logs-$(date +%Y%m%d).txt

# Setup log rotation
cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

sudo systemctl restart docker
```

---

## Development with Docker

### Hot Reload for Development

Update `docker-compose.yml`:

```yaml
web:
  build: .
  volumes:
    - .:/app  # Mount current directory
  environment:
    - FLASK_ENV=development
  command: flask run --host=0.0.0.0 --port=5001 --reload
```

### Run Tests

```bash
docker-compose exec web python3 -m pytest
```

### Interactive Python Shell

```bash
docker-compose exec web python3
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :5001

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "5002:5001"
```

### Ollama Not Responding

```bash
# Check logs
docker-compose logs ollama

# Restart Ollama
docker-compose restart ollama

# Pull model again
docker-compose exec ollama ollama pull llama3.2
```

### Database Locked

```bash
# Stop all services
docker-compose down

# Remove lock
rm data/.soulfra.db-journal

# Restart
docker-compose up -d
```

### Out of Disk Space

```bash
# Clean up Docker
docker system prune -a

# Remove unused volumes
docker volume prune
```

---

## Updating

### Pull Latest Images

```bash
# Update Ollama
docker-compose pull ollama

# Rebuild Flask app
docker-compose build web

# Restart with new images
docker-compose up -d
```

### Update Code

```bash
# If mounting volume for development
git pull
docker-compose restart web

# If not mounting volume
git pull
docker-compose up -d --build web
```

---

## Multi-Domain Setup

To run multiple domains as separate containers:

```yaml
services:
  soulfra:
    build: .
    environment:
      - DOMAIN=soulfra.com
    ports:
      - "5001:5001"

  calriven:
    build: .
    environment:
      - DOMAIN=calriven.com
    ports:
      - "5002:5001"

  deathtodata:
    build: .
    environment:
      - DOMAIN=deathtodata.com
    ports:
      - "5003:5001"
```

Update Nginx to route based on domain name.

---

## Next Steps

1. ✅ Services running on Docker
2. ⬜ Configure SSL certificates
3. ⬜ Setup automated backups
4. ⬜ Configure monitoring/alerts
5. ⬜ Deploy to cloud (DigitalOcean, AWS)

For cloud deployment, see `DEPLOYMENT-GUIDE.md`.
