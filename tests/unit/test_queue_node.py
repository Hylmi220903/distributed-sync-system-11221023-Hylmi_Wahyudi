"""
Unit tests untuk Queue Node
"""

import pytest
import asyncio
from src.nodes.queue_node import QueueNode, Message, MessageStatus, ConsistentHash


@pytest.fixture
def queue_node():
    """Create queue node instance"""
    return QueueNode("test_node", "localhost", 8001)


@pytest.mark.asyncio
async def test_create_queue(queue_node):
    """Test queue creation"""
    result = queue_node.create_queue("test_queue")
    
    assert result['status'] == 'success'
    assert 'test_queue' in queue_node.queues


@pytest.mark.asyncio
async def test_enqueue_message(queue_node):
    """Test enqueueing message"""
    result = await queue_node.enqueue(
        queue_name="test_queue",
        message_data={"task": "process"},
        priority=1
    )
    
    assert result['status'] == 'success'
    assert 'message_id' in result
    assert queue_node.queues['test_queue']


@pytest.mark.asyncio
async def test_dequeue_message(queue_node):
    """Test dequeueing message"""
    # First enqueue
    enqueue_result = await queue_node.enqueue(
        queue_name="test_queue",
        message_data={"task": "process"},
        priority=1
    )
    
    message_id = enqueue_result['message_id']
    
    # Then dequeue
    dequeue_result = await queue_node.dequeue(
        queue_name="test_queue",
        consumer_id="consumer1"
    )
    
    assert dequeue_result['status'] == 'success'
    assert dequeue_result['message']['message_id'] == message_id


@pytest.mark.asyncio
async def test_dequeue_empty_queue(queue_node):
    """Test dequeueing from empty queue"""
    queue_node.create_queue("empty_queue")
    
    result = await queue_node.dequeue(
        queue_name="empty_queue",
        consumer_id="consumer1"
    )
    
    assert result['status'] == 'empty'


@pytest.mark.asyncio
async def test_message_priority(queue_node):
    """Test message priority ordering"""
    # Enqueue with different priorities
    await queue_node.enqueue("priority_queue", {"msg": "low"}, priority=1)
    await queue_node.enqueue("priority_queue", {"msg": "high"}, priority=5)
    await queue_node.enqueue("priority_queue", {"msg": "medium"}, priority=3)
    
    # Dequeue should return highest priority first
    result1 = await queue_node.dequeue("priority_queue", "consumer1")
    assert result1['message']['data']['msg'] == 'high'
    
    result2 = await queue_node.dequeue("priority_queue", "consumer1")
    assert result2['message']['data']['msg'] == 'medium'
    
    result3 = await queue_node.dequeue("priority_queue", "consumer1")
    assert result3['message']['data']['msg'] == 'low'


@pytest.mark.asyncio
async def test_acknowledge_message(queue_node):
    """Test message acknowledgment"""
    # Enqueue and dequeue
    enqueue_result = await queue_node.enqueue(
        queue_name="ack_queue",
        message_data={"task": "test"}
    )
    
    message_id = enqueue_result['message_id']
    
    await queue_node.dequeue("ack_queue", "consumer1")
    
    # Acknowledge
    result = await queue_node.acknowledge(message_id, "consumer1")
    
    assert result['status'] == 'success'
    assert queue_node.messages[message_id].status == MessageStatus.DELIVERED


@pytest.mark.asyncio
async def test_negative_acknowledge(queue_node):
    """Test negative acknowledgment (requeue)"""
    # Enqueue and dequeue
    enqueue_result = await queue_node.enqueue(
        queue_name="nack_queue",
        message_data={"task": "test"}
    )
    
    message_id = enqueue_result['message_id']
    
    await queue_node.dequeue("nack_queue", "consumer1")
    
    # NACK - should requeue
    result = await queue_node.negative_acknowledge(message_id, "nack_queue")
    
    assert result['status'] == 'requeued'
    assert message_id in queue_node.queues['nack_queue']


@pytest.mark.asyncio
async def test_message_max_attempts(queue_node):
    """Test message fails after max attempts"""
    # Enqueue message
    enqueue_result = await queue_node.enqueue(
        queue_name="retry_queue",
        message_data={"task": "test"}
    )
    
    message_id = enqueue_result['message_id']
    message = queue_node.messages[message_id]
    message.max_attempts = 2
    
    # Try and fail multiple times
    await queue_node.dequeue("retry_queue", "consumer1")
    await queue_node.negative_acknowledge(message_id, "retry_queue")
    
    await queue_node.dequeue("retry_queue", "consumer1")
    result = await queue_node.negative_acknowledge(message_id, "retry_queue")
    
    assert result['status'] == 'failed'
    assert message.status == MessageStatus.FAILED


def test_consistent_hash_add_node():
    """Test adding node to consistent hash"""
    ch = ConsistentHash()
    
    ch.add_node("node1")
    ch.add_node("node2")
    
    assert "node1" in ch.nodes
    assert "node2" in ch.nodes
    assert len(ch.sorted_keys) > 0


def test_consistent_hash_get_node():
    """Test getting node from consistent hash"""
    ch = ConsistentHash()
    ch.add_node("node1")
    ch.add_node("node2")
    ch.add_node("node3")
    
    # Get node for key
    node = ch.get_node("test_key")
    
    assert node in ["node1", "node2", "node3"]
    
    # Same key should always return same node
    assert ch.get_node("test_key") == node


def test_consistent_hash_remove_node():
    """Test removing node from consistent hash"""
    ch = ConsistentHash()
    ch.add_node("node1")
    ch.add_node("node2")
    
    ch.remove_node("node1")
    
    assert "node1" not in ch.nodes
    assert "node2" in ch.nodes


def test_consistent_hash_replication():
    """Test getting multiple nodes for replication"""
    ch = ConsistentHash()
    ch.add_node("node1")
    ch.add_node("node2")
    ch.add_node("node3")
    
    nodes = ch.get_nodes("test_key", 2)
    
    assert len(nodes) == 2
    assert len(set(nodes)) == 2  # All unique


@pytest.mark.asyncio
async def test_get_queue_stats(queue_node):
    """Test getting queue statistics"""
    # Create and populate queue
    await queue_node.enqueue("stats_queue", {"msg": "1"})
    await queue_node.enqueue("stats_queue", {"msg": "2"})
    await queue_node.dequeue("stats_queue", "consumer1")
    
    stats = queue_node.get_queue_stats("stats_queue")
    
    assert stats['status'] == 'success'
    assert stats['queue_name'] == 'stats_queue'
    assert 'size' in stats
    assert 'pending' in stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
