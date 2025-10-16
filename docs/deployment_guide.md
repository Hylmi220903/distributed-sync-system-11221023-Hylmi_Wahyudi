# Deployment Guide

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **Python**: 3.8 or higher
- **Docker**: 20.10+ 
- **Docker Compose**: 1.29+
- **RAM**: Minimum 4GB, recommended 8GB+
- **Disk**: Minimum 10GB free space

### Software Installation

#### Install Docker (Ubuntu/Debian)

```bash
# Update package index
sudo apt-get update

# Install dependencies
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Setup repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

#### Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# atau
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

#### 1. Clone Repository

```bash
git clone <repository-url>
cd distributed-sync-system
```

#### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration (optional)
nano .env
```

#### 3. Build and Start Services

```bash
cd docker
docker-compose up --build
```

#### 4. Verify Deployment

```bash
# Check running containers
docker-compose ps

# Check logs
docker-compose logs -f node1

# Test node connectivity
curl http://localhost:8001/api/health
curl http://localhost:8002/api/health
curl http://localhost:8003/api/health
```

#### 5. Access Services

- **Node 1**: http://localhost:8001
- **Node 2**: http://localhost:8002
- **Node 3**: http://localhost:8003
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### Option 2: Manual Deployment

#### 1. Start Redis

```bash
docker run -d \
  --name distributed-sync-redis \
  -p 6379:6379 \
  redis:7-alpine
```

#### 2. Start Node 1

```bash
# Terminal 1
export NODE_ID=node1
export NODE_HOST=localhost
export NODE_PORT=8001
export CLUSTER_NODES=localhost:8001,localhost:8002,localhost:8003
export REDIS_HOST=localhost
export REDIS_PORT=6379

python -m src.main
```

#### 3. Start Node 2

```bash
# Terminal 2
export NODE_ID=node2
export NODE_HOST=localhost
export NODE_PORT=8002
export CLUSTER_NODES=localhost:8001,localhost:8002,localhost:8003
export REDIS_HOST=localhost
export REDIS_PORT=6379

python -m src.main
```

#### 4. Start Node 3

```bash
# Terminal 3
export NODE_ID=node3
export NODE_HOST=localhost
export NODE_PORT=8003
export CLUSTER_NODES=localhost:8001,localhost:8002,localhost:8003
export REDIS_HOST=localhost
export REDIS_PORT=6379

python -m src.main
```

### Option 3: Kubernetes Deployment

#### 1. Create Namespace

```bash
kubectl create namespace distributed-sync
```

#### 2. Deploy Redis

```yaml
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: distributed-sync
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: distributed-sync
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

```bash
kubectl apply -f redis-deployment.yaml
```

#### 3. Deploy Nodes

```yaml
# nodes-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: sync-node
  namespace: distributed-sync
spec:
  serviceName: "sync-node"
  replicas: 3
  selector:
    matchLabels:
      app: sync-node
  template:
    metadata:
      labels:
        app: sync-node
    spec:
      containers:
      - name: sync-node
        image: distributed-sync:latest
        env:
        - name: NODE_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: REDIS_HOST
          value: "redis"
        ports:
        - containerPort: 8001
        - containerPort: 9090
```

```bash
kubectl apply -f nodes-deployment.yaml
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| NODE_ID | Unique node identifier | node1 |
| NODE_HOST | Node hostname | localhost |
| NODE_PORT | Node port | 8001 |
| CLUSTER_NODES | Comma-separated node addresses | node1:8001,node2:8002,node3:8003 |
| HEARTBEAT_INTERVAL | Heartbeat interval (seconds) | 1.0 |
| ELECTION_TIMEOUT_MIN | Min election timeout (seconds) | 3.0 |
| ELECTION_TIMEOUT_MAX | Max election timeout (seconds) | 5.0 |
| REDIS_HOST | Redis hostname | localhost |
| REDIS_PORT | Redis port | 6379 |
| CACHE_SIZE | Cache capacity | 1000 |
| CACHE_POLICY | Cache replacement policy (LRU/LFU) | LRU |
| LOG_LEVEL | Logging level | INFO |

### Tuning Parameters

#### For High Throughput

```bash
# Increase cache size
CACHE_SIZE=10000

# Reduce heartbeat interval
HEARTBEAT_INTERVAL=0.5

# Increase replication factor
QUEUE_REPLICATION_FACTOR=3
```

#### For Low Latency

```bash
# Shorter election timeout
ELECTION_TIMEOUT_MIN=1.5
ELECTION_TIMEOUT_MAX=3.0

# More aggressive failure detection
PHI_THRESHOLD=6.0
```

#### For Large Clusters

```bash
# Increase heartbeat interval
HEARTBEAT_INTERVAL=2.0

# Longer election timeout
ELECTION_TIMEOUT_MIN=5.0
ELECTION_TIMEOUT_MAX=10.0
```

## Scaling

### Horizontal Scaling with Docker Compose

```bash
# Scale to 5 nodes
docker-compose up --scale node1=2 --scale node2=2 --scale node3=1
```

### Adding New Nodes

1. Update `.env` with new node configuration
2. Start new node with unique NODE_ID
3. Node akan otomatis join cluster

```bash
export NODE_ID=node4
export NODE_PORT=8004
export CLUSTER_NODES=localhost:8001,localhost:8002,localhost:8003,localhost:8004
python -m src.main
```

## Monitoring

### Prometheus Setup

1. Access Prometheus UI: http://localhost:9090
2. Check targets: Status → Targets
3. Create queries:

```promql
# Request rate
rate(requests_total[5m])

# Cache hit rate
cache_hits / (cache_hits + cache_misses) * 100

# Active locks
locks_active
```

### Grafana Setup

1. Access Grafana: http://localhost:3000
2. Login: admin/admin
3. Add Prometheus data source:
   - URL: http://prometheus:9090
4. Import dashboard or create custom

### Log Aggregation

```bash
# View logs from all nodes
docker-compose logs -f

# Filter by service
docker-compose logs -f node1

# Follow last 100 lines
docker-compose logs --tail=100 -f
```

## Backup and Recovery

### Backup Redis Data

```bash
# Manual backup
docker exec distributed-sync-redis redis-cli BGSAVE

# Automated backup with cron
0 2 * * * docker exec distributed-sync-redis redis-cli BGSAVE
```

### Restore from Backup

```bash
# Stop services
docker-compose down

# Restore Redis data
docker cp backup/dump.rdb distributed-sync-redis:/data/dump.rdb

# Start services
docker-compose up -d
```

### Node Recovery

```bash
# Restart failed node
docker-compose restart node1

# Check node status
curl http://localhost:8001/api/status
```

## Security Hardening

### Network Security

```yaml
# docker-compose.yml
networks:
  sync-network:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: sync-net
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### TLS Encryption

```bash
# Generate certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Update configuration
TLS_CERT=/path/to/cert.pem
TLS_KEY=/path/to/key.pem
```

### Authentication

```bash
# Set authentication token
AUTH_TOKEN=your-secure-token

# Update .env
echo "AUTH_TOKEN=${AUTH_TOKEN}" >> .env
```

## Troubleshooting

### Issue: Containers not starting

```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Rebuild images
docker-compose build --no-cache
docker-compose up
```

### Issue: Redis connection failed

```bash
# Check Redis is running
docker ps | grep redis

# Test Redis connection
docker exec -it distributed-sync-redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

### Issue: Nodes can't form cluster

```bash
# Verify network connectivity
docker network inspect distributed-sync_sync-network

# Check firewall rules
sudo ufw status

# Verify CLUSTER_NODES configuration
docker-compose exec node1 env | grep CLUSTER_NODES
```

### Issue: High memory usage

```bash
# Check memory usage
docker stats

# Reduce cache size
CACHE_SIZE=500

# Restart services
docker-compose restart
```

## Performance Optimization

### Docker Resource Limits

```yaml
# docker-compose.yml
services:
  node1:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Kernel Tuning (Linux)

```bash
# Increase file descriptors
echo "fs.file-max = 65536" | sudo tee -a /etc/sysctl.conf

# Increase TCP buffer sizes
echo "net.core.rmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" | sudo tee -a /etc/sysctl.conf

# Apply changes
sudo sysctl -p
```

## Health Checks

### Automated Health Monitoring

```bash
#!/bin/bash
# health-check.sh

NODES=("http://localhost:8001" "http://localhost:8002" "http://localhost:8003")

for node in "${NODES[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" $node/api/health)
    if [ $response -eq 200 ]; then
        echo "$node is healthy"
    else
        echo "$node is unhealthy (HTTP $response)"
        # Send alert
    fi
done
```

### Continuous Health Check

```bash
# Add to crontab
*/5 * * * * /path/to/health-check.sh
```

## Maintenance

### Rolling Updates

```bash
# Update one node at a time
docker-compose stop node1
docker-compose build node1
docker-compose up -d node1

# Wait for node to rejoin
sleep 30

# Continue with next node
docker-compose stop node2
# ... repeat
```

### Database Maintenance

```bash
# Compact Redis
docker exec distributed-sync-redis redis-cli BGREWRITEAOF

# Check database size
docker exec distributed-sync-redis redis-cli INFO | grep used_memory_human
```

## Production Checklist

- [ ] Environment variables properly configured
- [ ] TLS certificates installed
- [ ] Authentication enabled
- [ ] Monitoring configured (Prometheus + Grafana)
- [ ] Log aggregation setup
- [ ] Backup automation configured
- [ ] Health checks enabled
- [ ] Resource limits set
- [ ] Network security configured
- [ ] Documentation updated
- [ ] Disaster recovery plan in place
- [ ] Team trained on operations

## Support

Untuk pertanyaan atau issues:
1. Check logs: `docker-compose logs -f`
2. Verify configuration: `.env` file
3. Check documentation: `/docs`
4. Contact system administrator
