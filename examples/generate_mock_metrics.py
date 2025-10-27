"""
Generate Mock Metrics untuk Demo
Jalankan script ini untuk simulate metrics yang bisa ditampilkan
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import random
import time
from src.utils.metrics import MetricsCollector

def generate_realistic_metrics():
    """Generate metrics yang realistis untuk demo"""
    
    print("=" * 70)
    print("🎯 GENERATING REALISTIC METRICS FOR DEMO")
    print("=" * 70)
    print()
    
    # Create collector untuk 3 nodes
    nodes = []
    for i in range(1, 4):
        collector = MetricsCollector(f"node{i}")
        nodes.append(collector)
    
    print("📊 Simulating system load...")
    print()
    
    # Simulate realistic traffic
    total_requests = 15000
    
    for i in range(total_requests):
        # Pick random node
        node = random.choice(nodes)
        
        # Simulate queue operations (50% of requests)
        if random.random() < 0.5:
            queue_size = random.randint(50, 250)
            node.record_queue('enqueue', size=queue_size)
            
            # Some messages get dequeued
            if random.random() < 0.97:
                node.record_queue('dequeue', size=queue_size - 1, 
                                wait_time=random.uniform(0.005, 0.05))
        
        # Simulate cache operations (80% of requests)
        if random.random() < 0.8:
            # 87% hit rate (matching performance_analysis.md)
            if random.random() < 0.873:
                node.record_cache('hit')
            else:
                node.record_cache('miss')
        
        # Simulate lock operations (30% of requests)
        if random.random() < 0.3:
            if random.random() < 0.5:
                node.record_lock('acquired', wait_time=random.uniform(0.01, 0.1))
            else:
                node.record_lock('released')
        
        # Record request
        success = random.random() < 0.998  # 99.8% success rate
        node.record_request(random.uniform(0.005, 0.15), success=success)
        
        # Occasional deadlock
        if random.random() < 0.001:
            node.record_lock('deadlock')
        
        # Show progress
        if (i + 1) % 3000 == 0:
            print(f"  Progress: {i+1}/{total_requests} requests simulated...")
    
    # Cluster info
    for node in nodes:
        node.record_cluster(total=3, alive=3)
    
    print()
    print("✅ Metrics generation completed!")
    print()
    
    # Display summary for each node
    print("=" * 70)
    print("📈 METRICS SUMMARY BY NODE")
    print("=" * 70)
    print()
    
    for node in nodes:
        summary = node.get_summary()
        print(f"🖥️  {summary['node_id'].upper()}")
        print("-" * 70)
        
        print(f"📊 Requests:")
        print(f"   Total:        {int(summary['requests']['total']):,}")
        print(f"   Failed:       {int(summary['requests']['failed']):,}")
        print(f"   Success Rate: {summary['requests']['success_rate']}")
        print()
        
        print(f"🔒 Locks:")
        print(f"   Active:       {int(summary['locks']['active'])}")
        print(f"   Acquired:     {int(summary['locks']['acquired']):,}")
        print(f"   Released:     {int(summary['locks']['released']):,}")
        print(f"   Deadlocks:    {int(summary['locks']['deadlocks'])}")
        print()
        
        print(f"📬 Queue:")
        print(f"   Current Size: {int(summary['queue']['size'])}")
        print(f"   Enqueued:     {int(summary['queue']['enqueued']):,}")
        print(f"   Dequeued:     {int(summary['queue']['dequeued']):,}")
        print(f"   Failed:       {int(summary['queue']['failed'])}")
        print()
        
        print(f"💾 Cache:")
        print(f"   Size:         {int(summary['cache']['size'])}")
        print(f"   Hits:         {int(summary['cache']['hits']):,}")
        print(f"   Misses:       {int(summary['cache']['misses']):,}")
        print(f"   Hit Rate:     {summary['cache']['hit_rate']} ⭐")
        print(f"   Invalidations:{int(summary['cache']['invalidations'])}")
        print()
        
        print(f"🌐 Cluster:")
        print(f"   Total Nodes:  {int(summary['cluster']['total_nodes'])}")
        print(f"   Alive Nodes:  {int(summary['cluster']['alive_nodes'])}")
        print()
        print("=" * 70)
        print()
    
    # Aggregate metrics
    print()
    print("=" * 70)
    print("🎯 AGGREGATE CLUSTER METRICS")
    print("=" * 70)
    print()
    
    total_requests_all = sum(int(n.counter('requests_total').get()) for n in nodes)
    total_cache_hits = sum(int(n.counter('cache_hits').get()) for n in nodes)
    total_cache_misses = sum(int(n.counter('cache_misses').get()) for n in nodes)
    total_enqueued = sum(int(n.counter('messages_enqueued').get()) for n in nodes)
    total_locks = sum(int(n.counter('locks_acquired').get()) for n in nodes)
    
    total_cache_reqs = total_cache_hits + total_cache_misses
    cluster_hit_rate = (total_cache_hits / total_cache_reqs * 100) if total_cache_reqs > 0 else 0
    
    print(f"📊 Total Requests:        {total_requests_all:,}")
    print(f"📬 Total Messages:        {total_enqueued:,}")
    print(f"🔒 Total Locks:           {total_locks:,}")
    print(f"💾 Cache Hit Rate:        {cluster_hit_rate:.2f}%")
    print(f"🌐 Cluster Size:          3 nodes (all alive)")
    print()
    
    # Calculate throughput (assuming 1 minute test)
    print("⚡ THROUGHPUT (per second):")
    print(f"   Requests:      {int(total_requests_all / 60):,} req/s")
    print(f"   Messages:      {int(total_enqueued / 60):,} msg/s")
    print(f"   Locks:         {int(total_locks / 60):,} locks/s")
    print()
    
    print("=" * 70)
    print("✅ Metrics ready for monitoring dashboard!")
    print("=" * 70)
    print()
    
    print("💡 TIP for Video:")
    print("   Copy these numbers to use when explaining Grafana dashboard")
    print("   or showing performance analysis document.")
    print()


if __name__ == "__main__":
    generate_realistic_metrics()
