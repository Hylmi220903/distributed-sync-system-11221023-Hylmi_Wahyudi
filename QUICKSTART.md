# Quick Start Guide

Panduan cepat untuk menjalankan Distributed Synchronization System.

---

## 🚀 Quick Start (5 Menit)

### Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd distributed-sync-system
```

### Step 2: Start dengan Docker (RECOMMENDED)

```bash
# Masuk ke folder docker
cd docker

# Start semua services
docker-compose up -d

# Check logs
docker-compose logs -f node1
```

**Services yang berjalan:**
- Node1: http://localhost:8001 (Leader)
- Node2: http://localhost:8002 (Follower)
- Node3: http://localhost:8003 (Follower)
- Redis: localhost:6379
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### Step 3: Test API

```bash
# Check cluster status
curl http://localhost:8001/api/status

# Acquire lock
curl -X POST http://localhost:8001/api/locks/acquire \
  -H "Content-Type: application/json" \
  -d '{"lock_id": "resource1", "requester_id": "client1", "lock_type": "exclusive"}'

# Enqueue message
curl -X POST http://localhost:8001/api/queues/enqueue \
  -H "Content-Type: application/json" \
  -d '{"queue_name": "tasks", "message_data": {"task": "process_image"}}'

# Get from cache
curl http://localhost:8001/api/cache/get/user:123
```

### Step 4: View Monitoring

1. Open Grafana: http://localhost:3000
2. Login: admin / admin
3. Go to Dashboards → Distributed System Metrics

---

## 🐍 Manual Setup (Development)

### Prerequisites

- Python 3.8+
- Redis (optional, untuk development)
- pip

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env dengan configuration Anda
notepad .env  # Windows
nano .env     # Linux/Mac
```

### Running Single Node

```bash
# Set environment
export NODE_ID=node1
export NODE_PORT=8001
export CLUSTER_NODES=node1:8001,node2:8002,node3:8003

# Run node
python -m src.main
```

### Running Multiple Nodes (Manual)

**Terminal 1 - Node 1:**
```bash
python -m src.main --node-id node1 --port 8001
```

**Terminal 2 - Node 2:**
```bash
python -m src.main --node-id node2 --port 8002
```

**Terminal 3 - Node 3:**
```bash
python -m src.main --node-id node3 --port 8003
```

---

## 🧪 Running Tests

### Unit Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html

# Open coverage report
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac
xdg-open htmlcov/index.html  # Linux
```

### Integration Tests

```bash
# Pastikan Docker cluster running
cd docker
docker-compose up -d

# Run integration tests
pytest tests/integration/ -v
```

### Load Testing

```bash
# Install Locust
pip install locust

# Run load test (dengan UI)
locust -f benchmarks/load_test_scenarios.py

# Open http://localhost:8089
# Set users: 100, spawn rate: 10

# Atau headless mode
locust -f benchmarks/load_test_scenarios.py --headless \
       --users 100 --spawn-rate 10 --run-time 60s \
       --host http://localhost:8001
```

---

## 📊 Usage Examples

### 1. Distributed Lock

```python
import asyncio
import aiohttp

async def use_lock():
    async with aiohttp.ClientSession() as session:
        # Acquire lock
        async with session.post(
            'http://localhost:8001/api/locks/acquire',
            json={
                'lock_id': 'database:users',
                'requester_id': 'worker1',
                'lock_type': 'exclusive',
                'timeout': 30.0
            }
        ) as resp:
            result = await resp.json()
            print(f"Lock acquired: {result}")
        
        # Do critical work
        await asyncio.sleep(5)
        
        # Release lock
        async with session.post(
            'http://localhost:8001/api/locks/release',
            json={
                'lock_id': 'database:users',
                'requester_id': 'worker1'
            }
        ) as resp:
            result = await resp.json()
            print(f"Lock released: {result}")

asyncio.run(use_lock())
```

### 2. Distributed Queue

```python
import asyncio
import aiohttp

async def use_queue():
    async with aiohttp.ClientSession() as session:
        # Enqueue messages
        for i in range(10):
            async with session.post(
                'http://localhost:8001/api/queues/enqueue',
                json={
                    'queue_name': 'image_processing',
                    'message_data': {
                        'image_id': f'img_{i}',
                        'operation': 'resize'
                    },
                    'priority': i % 3  # 0=high, 1=medium, 2=low
                }
            ) as resp:
                result = await resp.json()
                print(f"Enqueued: {result['message_id']}")
        
        # Dequeue and process
        for i in range(10):
            async with session.post(
                'http://localhost:8001/api/queues/dequeue',
                json={
                    'queue_name': 'image_processing',
                    'consumer_id': 'worker1'
                }
            ) as resp:
                result = await resp.json()
                if result['status'] == 'success':
                    message = result['message']
                    print(f"Processing: {message['data']}")
                    
                    # Acknowledge successful processing
                    async with session.post(
                        'http://localhost:8001/api/queues/ack',
                        json={'message_id': message['message_id']}
                    ) as ack_resp:
                        print("Message acknowledged")

asyncio.run(use_queue())
```

### 3. Distributed Cache

```python
import asyncio
import aiohttp

async def use_cache():
    async with aiohttp.ClientSession() as session:
        # Put data in cache
        async with session.post(
            'http://localhost:8001/api/cache/put',
            json={
                'key': 'user:123',
                'value': {
                    'name': 'John Doe',
                    'email': 'john@example.com'
                },
                'ttl': 3600  # 1 hour
            }
        ) as resp:
            result = await resp.json()
            print(f"Cache put: {result}")
        
        # Get from cache
        async with session.get(
            'http://localhost:8001/api/cache/get/user:123'
        ) as resp:
            result = await resp.json()
            if result['status'] == 'hit':
                print(f"Cache hit: {result['value']}")
            else:
                print("Cache miss")
        
        # Invalidate cache
        async with session.post(
            'http://localhost:8001/api/cache/invalidate',
            json={'key': 'user:123'}
        ) as resp:
            result = await resp.json()
            print(f"Cache invalidated: {result}")

asyncio.run(use_cache())
```

### 4. Complete Workflow

Lihat `examples/usage_examples.py` untuk contoh lengkap yang mencakup:
- Lock acquisition dan release
- Queue operations dengan priority
- Cache operations dengan coherence
- Failure scenarios
- Combined workflows

```bash
python examples/usage_examples.py
```

---

## 🔍 Monitoring & Debugging

### Check Cluster Status

```bash
# Status via API
curl http://localhost:8001/api/status | json_pp

# Docker container status
docker-compose ps

# View logs
docker-compose logs -f node1
docker-compose logs -f node2
docker-compose logs -f node3
```

### Prometheus Metrics

```bash
# Open Prometheus
open http://localhost:9090

# Sample queries:
# - lock_operations_total
# - queue_messages_total
# - cache_requests_total
# - node_leader_changes_total
```

### Grafana Dashboard

```bash
# Open Grafana
open http://localhost:3000

# Login: admin / admin

# Import dashboard:
# 1. Click "+" → Import
# 2. Upload docker/grafana/dashboard.json
# 3. View metrics
```

### Redis Inspection

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# View keys
KEYS *

# Get cluster state
GET cluster:state

# View lock info
HGETALL locks:*
```

---

## 🛠️ Common Operations

### Scale Cluster

```bash
# Add more nodes
docker-compose up -d --scale node=5

# Check new nodes
docker-compose ps
```

### Stop Cluster

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Restart Node

```bash
# Restart single node
docker-compose restart node1

# Restart all nodes
docker-compose restart
```

### View Metrics

```bash
# Prometheus metrics endpoint
curl http://localhost:8001/metrics

# Custom metrics
curl http://localhost:8001/api/metrics
```

### Backup Data

```bash
# Backup Redis data
docker-compose exec redis redis-cli BGSAVE

# Copy backup
docker cp $(docker-compose ps -q redis):/data/dump.rdb ./backup/
```

---

## 🐛 Troubleshooting

### Issue: Port already in use

```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8001 | xargs kill -9
```

### Issue: Docker containers won't start

```bash
# Clean up everything
docker-compose down -v
docker system prune -a

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Module import errors

```bash
# Install in development mode
pip install -e .

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Redis connection failed

```bash
# Check Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis

# Check Redis logs
docker-compose logs redis
```

### Issue: Tests failing

```bash
# Ensure cluster is running
docker-compose up -d

# Wait for cluster to stabilize
sleep 10

# Run tests again
pytest tests/ -v
```

### Issue: Leader election failing

```bash
# Check network connectivity
docker-compose exec node1 ping node2

# Check cluster configuration
curl http://localhost:8001/api/status

# Restart cluster
docker-compose restart
```

---

## 📚 Next Steps

1. **Explore Documentation**
   - Read `docs/architecture.md` untuk understanding system
   - Check `docs/api_spec.yaml` untuk API details
   - Review `docs/deployment_guide.md` untuk production

2. **Run Examples**
   - Execute `examples/usage_examples.py`
   - Modify examples untuk your use case
   - Test failure scenarios

3. **Performance Testing**
   - Run load tests: `locust -f benchmarks/load_test_scenarios.py`
   - Analyze results di `docs/performance_analysis.md`
   - Tune configuration untuk better performance

4. **Production Deployment**
   - Follow `docs/deployment_guide.md`
   - Set up monitoring dan alerting
   - Configure backups
   - Implement security measures

---

## 💡 Tips

- **Start simple:** Begin dengan single node untuk development
- **Use Docker:** Docker compose makes multi-node setup easy
- **Monitor everything:** Use Grafana untuk real-time monitoring
- **Test failures:** Simulate failures untuk ensure resilience
- **Read logs:** Logs are your friend untuk debugging
- **Ask for help:** Check documentation atau reach out

---

## 📞 Support

Jika ada masalah:

1. Check logs: `docker-compose logs -f`
2. Read documentation di `docs/`
3. Check GitHub issues
4. Contact maintainer

---

**Happy coding! 🚀**

Untuk detailed guide, lihat `README.md` dan `docs/` directory.
