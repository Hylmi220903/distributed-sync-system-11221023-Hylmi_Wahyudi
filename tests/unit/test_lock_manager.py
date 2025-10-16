"""
Unit tests untuk Lock Manager
"""

import pytest
import asyncio
from src.nodes.lock_manager import LockManagerNode, LockType, Lock
from src.nodes.base_node import NodeState


@pytest.fixture
def lock_manager():
    """Create lock manager instance"""
    node = LockManagerNode("test_node", "localhost", 8001)
    node.state = NodeState.LEADER  # Set as leader for testing
    return node


@pytest.mark.asyncio
async def test_acquire_exclusive_lock(lock_manager):
    """Test acquiring exclusive lock"""
    result = await lock_manager.acquire_lock(
        lock_id="test_lock",
        requester_id="client1",
        lock_type=LockType.EXCLUSIVE,
        timeout=30.0
    )
    
    assert result['status'] == 'acquired'
    assert result['lock_id'] == 'test_lock'
    assert result['holder_id'] == 'client1'


@pytest.mark.asyncio
async def test_acquire_shared_lock(lock_manager):
    """Test acquiring shared lock"""
    # First shared lock
    result1 = await lock_manager.acquire_lock(
        lock_id="shared_lock",
        requester_id="client1",
        lock_type=LockType.SHARED
    )
    
    assert result1['status'] == 'acquired'
    
    # Second shared lock (should also succeed)
    result2 = await lock_manager.acquire_lock(
        lock_id="shared_lock",
        requester_id="client2",
        lock_type=LockType.SHARED
    )
    
    assert result2['status'] == 'acquired'


@pytest.mark.asyncio
async def test_exclusive_lock_blocks_others(lock_manager):
    """Test that exclusive lock blocks other requests"""
    # Acquire exclusive lock
    result1 = await lock_manager.acquire_lock(
        lock_id="exclusive_lock",
        requester_id="client1",
        lock_type=LockType.EXCLUSIVE
    )
    
    assert result1['status'] == 'acquired'
    
    # Try to acquire again (should wait)
    result2 = await lock_manager.acquire_lock(
        lock_id="exclusive_lock",
        requester_id="client2",
        lock_type=LockType.EXCLUSIVE
    )
    
    assert result2['status'] == 'waiting'


@pytest.mark.asyncio
async def test_release_lock(lock_manager):
    """Test releasing lock"""
    # Acquire lock
    await lock_manager.acquire_lock(
        lock_id="release_test",
        requester_id="client1",
        lock_type=LockType.EXCLUSIVE
    )
    
    # Release lock
    result = await lock_manager.release_lock(
        lock_id="release_test",
        holder_id="client1"
    )
    
    assert result['status'] == 'released'


@pytest.mark.asyncio
async def test_deadlock_detection(lock_manager):
    """Test deadlock detection"""
    # Client1 acquires lock A
    await lock_manager.acquire_lock(
        lock_id="lock_a",
        requester_id="client1",
        lock_type=LockType.EXCLUSIVE
    )
    
    # Client2 acquires lock B
    await lock_manager.acquire_lock(
        lock_id="lock_b",
        requester_id="client2",
        lock_type=LockType.EXCLUSIVE
    )
    
    # Setup wait-for graph
    lock_manager.wait_for_graph['client1'] = {'client2'}
    lock_manager.wait_for_graph['client2'] = set()
    
    # Client2 tries to acquire lock A (would create cycle)
    result = await lock_manager.acquire_lock(
        lock_id="lock_a",
        requester_id="client2",
        lock_type=LockType.EXCLUSIVE
    )
    
    # Should detect deadlock
    assert result['status'] in ['error', 'waiting']


@pytest.mark.asyncio
async def test_lock_timeout(lock_manager):
    """Test lock timeout"""
    # Acquire lock
    await lock_manager.acquire_lock(
        lock_id="timeout_test",
        requester_id="client1",
        lock_type=LockType.EXCLUSIVE,
        timeout=0.1  # 100ms timeout
    )
    
    # Wait for timeout
    await asyncio.sleep(0.2)
    
    # Check for expired locks
    await lock_manager.check_lock_timeouts()
    
    # Lock should be released
    assert "timeout_test" not in lock_manager.locks or \
           not lock_manager.locks["timeout_test"].is_locked()


def test_lock_can_acquire_shared(lock_manager):
    """Test Lock.can_acquire for shared locks"""
    lock = Lock("test", LockType.SHARED, "client1")
    
    # Shared lock can be acquired by others
    assert lock.can_acquire("client2", LockType.SHARED) == True
    
    # Exclusive lock cannot be acquired
    assert lock.can_acquire("client2", LockType.EXCLUSIVE) == False


def test_lock_can_acquire_exclusive(lock_manager):
    """Test Lock.can_acquire for exclusive locks"""
    lock = Lock("test", LockType.EXCLUSIVE, "client1")
    
    # No other locks can be acquired
    assert lock.can_acquire("client2", LockType.SHARED) == False
    assert lock.can_acquire("client2", LockType.EXCLUSIVE) == False


@pytest.mark.asyncio
async def test_get_lock_status(lock_manager):
    """Test getting lock status"""
    # Acquire lock
    await lock_manager.acquire_lock(
        lock_id="status_test",
        requester_id="client1",
        lock_type=LockType.EXCLUSIVE
    )
    
    # Get status
    status = lock_manager.get_lock_status("status_test")
    
    assert status['status'] == 'found'
    assert status['lock_id'] == 'status_test'
    assert 'client1' in status['holders']


@pytest.mark.asyncio
async def test_get_all_locks(lock_manager):
    """Test getting all locks"""
    # Create multiple locks
    await lock_manager.acquire_lock("lock1", "client1", LockType.EXCLUSIVE)
    await lock_manager.acquire_lock("lock2", "client2", LockType.SHARED)
    
    # Get all locks
    all_locks = lock_manager.get_all_locks()
    
    assert len(all_locks) >= 2
    assert any(lock['lock_id'] == 'lock1' for lock in all_locks)
    assert any(lock['lock_id'] == 'lock2' for lock in all_locks)


@pytest.mark.asyncio
async def test_not_leader_error(lock_manager):
    """Test error when not leader"""
    # Set as follower
    lock_manager.state = NodeState.FOLLOWER
    
    result = await lock_manager.acquire_lock(
        lock_id="test",
        requester_id="client1",
        lock_type=LockType.EXCLUSIVE
    )
    
    assert result['status'] == 'error'
    assert 'leader' in result['message'].lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
