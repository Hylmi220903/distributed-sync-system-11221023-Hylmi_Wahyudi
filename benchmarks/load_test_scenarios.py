"""
Load Test Scenarios untuk Performance Analysis
Menggunakan Locust untuk load testing
"""

from locust import HttpUser, task, between, events
import random
import json
import time
from datetime import datetime


class LockManagerUser(HttpUser):
    """
    Simulate user yang menggunakan distributed lock
    """
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Setup user"""
        self.user_id = f"user_{random.randint(1, 1000)}"
        self.locks_held = []
    
    @task(3)
    def acquire_exclusive_lock(self):
        """Acquire exclusive lock"""
        lock_id = f"resource_{random.randint(1, 100)}"
        
        start_time = time.time()
        response = self.client.post("/api/locks/acquire", json={
            "lock_id": lock_id,
            "requester_id": self.user_id,
            "lock_type": "exclusive",
            "timeout": 30.0
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'acquired':
                self.locks_held.append(lock_id)
        
        # Record custom metric
        elapsed = time.time() - start_time
        events.request.fire(
            request_type="lock",
            name="acquire_exclusive",
            response_time=elapsed * 1000,
            response_length=len(response.content),
            exception=None if response.status_code == 200 else Exception(f"Status {response.status_code}")
        )
    
    @task(1)
    def acquire_shared_lock(self):
        """Acquire shared lock"""
        lock_id = f"readonly_{random.randint(1, 50)}"
        
        response = self.client.post("/api/locks/acquire", json={
            "lock_id": lock_id,
            "requester_id": self.user_id,
            "lock_type": "shared",
            "timeout": 30.0
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'acquired':
                self.locks_held.append(lock_id)
    
    @task(2)
    def release_lock(self):
        """Release a held lock"""
        if not self.locks_held:
            return
        
        lock_id = self.locks_held.pop(0)
        
        start_time = time.time()
        response = self.client.post("/api/locks/release", json={
            "lock_id": lock_id,
            "holder_id": self.user_id
        })
        
        elapsed = time.time() - start_time
        events.request.fire(
            request_type="lock",
            name="release",
            response_time=elapsed * 1000,
            response_length=len(response.content),
            exception=None if response.status_code == 200 else Exception(f"Status {response.status_code}")
        )
    
    @task(1)
    def get_lock_status(self):
        """Query lock status"""
        lock_id = f"resource_{random.randint(1, 100)}"
        self.client.get(f"/api/locks/{lock_id}")


class QueueUser(HttpUser):
    """
    Simulate producer/consumer menggunakan distributed queue
    """
    wait_time = between(0.05, 0.2)
    
    def on_start(self):
        """Setup user"""
        self.user_id = f"user_{random.randint(1, 1000)}"
        self.queue_name = "benchmark_queue"
        
        # Create queue
        self.client.post("/api/queues/create", json={
            "queue_name": self.queue_name
        })
    
    @task(5)
    def enqueue_message(self):
        """Produce message to queue"""
        message_data = {
            "task": "process",
            "data": f"payload_{random.randint(1, 10000)}",
            "timestamp": datetime.now().isoformat()
        }
        
        start_time = time.time()
        response = self.client.post("/api/queues/enqueue", json={
            "queue_name": self.queue_name,
            "message_data": message_data,
            "priority": random.randint(0, 5)
        })
        
        elapsed = time.time() - start_time
        events.request.fire(
            request_type="queue",
            name="enqueue",
            response_time=elapsed * 1000,
            response_length=len(response.content),
            exception=None if response.status_code == 200 else Exception(f"Status {response.status_code}")
        )
    
    @task(4)
    def dequeue_message(self):
        """Consume message from queue"""
        start_time = time.time()
        response = self.client.post("/api/queues/dequeue", json={
            "queue_name": self.queue_name,
            "consumer_id": self.user_id
        })
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                # Acknowledge message
                message_id = data['message']['message_id']
                self.client.post("/api/queues/ack", json={
                    "message_id": message_id,
                    "consumer_id": self.user_id
                })
        
        events.request.fire(
            request_type="queue",
            name="dequeue",
            response_time=elapsed * 1000,
            response_length=len(response.content),
            exception=None if response.status_code == 200 else Exception(f"Status {response.status_code}")
        )
    
    @task(1)
    def get_queue_stats(self):
        """Query queue statistics"""
        self.client.get(f"/api/queues/{self.queue_name}/stats")


class CacheUser(HttpUser):
    """
    Simulate aplikasi menggunakan distributed cache
    """
    wait_time = between(0.01, 0.1)
    
    def on_start(self):
        """Setup user"""
        self.user_id = f"app_{random.randint(1, 100)}"
        self.keys = [f"key_{i}" for i in range(1000)]
    
    @task(7)
    def cache_get(self):
        """Get from cache"""
        key = random.choice(self.keys)
        
        start_time = time.time()
        response = self.client.get(f"/api/cache/get?key={key}&requester_id={self.user_id}")
        
        elapsed = time.time() - start_time
        
        is_hit = response.status_code == 200 and response.json().get('status') == 'hit'
        
        events.request.fire(
            request_type="cache",
            name="get_hit" if is_hit else "get_miss",
            response_time=elapsed * 1000,
            response_length=len(response.content),
            exception=None
        )
    
    @task(2)
    def cache_put(self):
        """Put to cache"""
        key = random.choice(self.keys)
        value = {
            "data": f"value_{random.randint(1, 10000)}",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"source": self.user_id}
        }
        
        start_time = time.time()
        response = self.client.post("/api/cache/put", json={
            "key": key,
            "value": value,
            "requester_id": self.user_id
        })
        
        elapsed = time.time() - start_time
        events.request.fire(
            request_type="cache",
            name="put",
            response_time=elapsed * 1000,
            response_length=len(response.content),
            exception=None if response.status_code == 200 else Exception(f"Status {response.status_code}")
        )
    
    @task(1)
    def cache_delete(self):
        """Delete from cache"""
        key = random.choice(self.keys)
        
        response = self.client.delete(f"/api/cache/delete?key={key}")
    
    @task(1)
    def get_cache_stats(self):
        """Query cache statistics"""
        self.client.get("/api/cache/stats")


class MixedWorkloadUser(HttpUser):
    """
    Simulate mixed workload (locks + queues + cache)
    """
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Setup user"""
        self.user_id = f"user_{random.randint(1, 1000)}"
    
    @task(3)
    def lock_and_cache_workflow(self):
        """Acquire lock, update cache, release lock"""
        resource_id = f"resource_{random.randint(1, 50)}"
        
        # Acquire lock
        lock_response = self.client.post("/api/locks/acquire", json={
            "lock_id": resource_id,
            "requester_id": self.user_id,
            "lock_type": "exclusive",
            "timeout": 10.0
        })
        
        if lock_response.status_code == 200:
            data = lock_response.json()
            if data.get('status') == 'acquired':
                # Update cache
                self.client.post("/api/cache/put", json={
                    "key": resource_id,
                    "value": {"updated": datetime.now().isoformat()},
                    "requester_id": self.user_id
                })
                
                # Simulate work
                time.sleep(random.uniform(0.01, 0.05))
                
                # Release lock
                self.client.post("/api/locks/release", json={
                    "lock_id": resource_id,
                    "holder_id": self.user_id
                })
    
    @task(2)
    def queue_and_cache_workflow(self):
        """Enqueue task, cache result"""
        queue_name = "task_queue"
        
        # Enqueue
        enqueue_response = self.client.post("/api/queues/enqueue", json={
            "queue_name": queue_name,
            "message_data": {"task": "process", "id": random.randint(1, 1000)},
            "priority": 1
        })
        
        if enqueue_response.status_code == 200:
            data = enqueue_response.json()
            message_id = data.get('message_id')
            
            # Cache message ID
            if message_id:
                self.client.post("/api/cache/put", json={
                    "key": f"msg_{message_id}",
                    "value": {"status": "queued"},
                    "requester_id": self.user_id
                })


# Performance test scenarios

class ThroughputTest(HttpUser):
    """
    Throughput test - maximize requests per second
    """
    wait_time = between(0.001, 0.01)
    
    @task
    def high_throughput_requests(self):
        """Rapid fire requests"""
        self.client.get("/api/health")


class LatencyTest(HttpUser):
    """
    Latency test - measure response times under load
    """
    wait_time = between(1, 2)
    
    @task
    def measure_latency(self):
        """Measure operation latency"""
        lock_id = f"latency_test_{random.randint(1, 10)}"
        
        # Measure lock acquire latency
        start = time.time()
        response = self.client.post("/api/locks/acquire", json={
            "lock_id": lock_id,
            "requester_id": "latency_tester",
            "lock_type": "exclusive",
            "timeout": 5.0
        })
        acquire_time = time.time() - start
        
        if response.status_code == 200:
            # Measure lock release latency
            start = time.time()
            self.client.post("/api/locks/release", json={
                "lock_id": lock_id,
                "holder_id": "latency_tester"
            })
            release_time = time.time() - start
            
            print(f"Acquire: {acquire_time*1000:.2f}ms, Release: {release_time*1000:.2f}ms")


# Run with:
# locust -f load_test_scenarios.py --host=http://localhost:8001
# 
# Or for headless mode:
# locust -f load_test_scenarios.py --host=http://localhost:8001 \
#        --users 100 --spawn-rate 10 --run-time 5m --headless
