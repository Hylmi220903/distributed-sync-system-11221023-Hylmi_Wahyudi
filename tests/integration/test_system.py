"""
Integration tests untuk system
"""

import pytest
import asyncio
import time
from src.main import DistributedSyncSystem
from src.utils.config import Config
from src.nodes.base_node import NodeState


@pytest.fixture
def test_config():
    """Create test configuration"""
    return Config(
        node_id="test_node",
        node_host="localhost",
        node_port=9001,
        cluster_nodes=["test_node:9001"],
        heartbeat_interval=1.0,
        election_timeout_min=3.0,
        election_timeout_max=5.0,
        redis_host="localhost",
        redis_port=6379,
        redis_db=0,
        cache_size=100,
        cache_policy="LRU",
        cache_protocol="MESI",
        queue_persistence=False,
        queue_replication_factor=1,
        metrics_port=9090,
        enable_prometheus=False,
        log_level="INFO"
    )


@pytest.mark.asyncio
async def test_system_start_stop(test_config):
    """Test system can start and stop"""
    system = DistributedSyncSystem(test_config)
    
    # Start system (with timeout)
    start_task = asyncio.create_task(system.start())
    
    # Wait a bit for initialization
    await asyncio.sleep(2)
    
    # Stop system
    await system.stop()
    
    # Cancel start task if still running
    if not start_task.done():
        start_task.cancel()
    
    assert system.running == False


@pytest.mark.asyncio
async def test_lock_manager_integration(test_config):
    """Test lock manager in full system"""
    system = DistributedSyncSystem(test_config)
    
    # Setup system
    system.lock_manager.state = NodeState.LEADER
    
    # Test lock operations
    from src.nodes.lock_manager import LockType
    
    result = await system.lock_manager.acquire_lock(
        "test_lock",
        "client1",
        LockType.EXCLUSIVE
    )
    
    assert result['status'] == 'acquired'
    
    result = await system.lock_manager.release_lock(
        "test_lock",
        "client1"
    )
    
    assert result['status'] == 'released'


@pytest.mark.asyncio
async def test_queue_integration(test_config):
    """Test queue in full system"""
    system = DistributedSyncSystem(test_config)
    
    # Test queue operations
    await system.queue_node.enqueue(
        "test_queue",
        {"task": "test"},
        priority=1
    )
    
    result = await system.queue_node.dequeue(
        "test_queue",
        "consumer1"
    )
    
    assert result['status'] == 'success'


@pytest.mark.asyncio
async def test_cache_integration(test_config):
    """Test cache in full system"""
    system = DistributedSyncSystem(test_config)
    
    # Test cache operations
    await system.cache_node.put(
        "test_key",
        {"value": "test"},
        "requester1"
    )
    
    result = await system.cache_node.get(
        "test_key",
        "requester1"
    )
    
    assert result['status'] == 'hit'
    assert result['value'] == {"value": "test"}


@pytest.mark.asyncio
async def test_metrics_collection(test_config):
    """Test metrics are collected"""
    system = DistributedSyncSystem(test_config)
    
    # Perform some operations
    system.metrics.record_request(0.1, success=True)
    system.metrics.record_cache('hit', size=10)
    system.metrics.record_lock('acquired', wait_time=0.05)
    
    # Get metrics summary
    summary = system.metrics.get_summary()
    
    assert summary['node_id'] == 'test_node'
    assert summary['requests']['total'] > 0
    assert summary['cache']['hits'] > 0
    assert summary['locks']['acquired'] > 0


def test_system_status(test_config):
    """Test getting system status"""
    system = DistributedSyncSystem(test_config)
    
    status = system.get_status()
    
    assert 'node_id' in status
    assert 'lock_manager' in status
    assert 'cache' in status
    assert 'metrics' in status


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
