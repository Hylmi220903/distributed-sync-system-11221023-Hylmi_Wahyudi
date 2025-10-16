"""
Example usage of the Distributed Sync System
Demonstrasi penggunaan lock, queue, dan cache
"""

import asyncio
import logging
from src.nodes import LockManagerNode, QueueNode, CacheNode, LockType
from src.nodes.base_node import NodeState

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def lock_example():
    """
    Example: Distributed Lock Usage
    Use case: Database transaction coordination
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 1: Distributed Lock Manager")
    logger.info("=" * 60)
    
    # Create lock manager
    lock_manager = LockManagerNode("node1", "localhost", 8001)
    lock_manager.state = NodeState.LEADER  # Simulate as leader
    
    # Example 1: Exclusive Lock
    logger.info("\n--- Exclusive Lock Example ---")
    
    # Client 1 acquires exclusive lock
    result = await lock_manager.acquire_lock(
        lock_id="database:users",
        requester_id="client1",
        lock_type=LockType.EXCLUSIVE,
        timeout=30.0
    )
    logger.info(f"Client1 acquire result: {result}")
    
    # Client 2 tries to acquire same lock (should wait)
    result = await lock_manager.acquire_lock(
        lock_id="database:users",
        requester_id="client2",
        lock_type=LockType.EXCLUSIVE
    )
    logger.info(f"Client2 acquire result: {result}")
    
    # Client 1 releases lock
    result = await lock_manager.release_lock(
        lock_id="database:users",
        holder_id="client1"
    )
    logger.info(f"Client1 release result: {result}")
    
    # Example 2: Shared Lock
    logger.info("\n--- Shared Lock Example ---")
    
    # Multiple readers can acquire shared lock
    result1 = await lock_manager.acquire_lock(
        lock_id="config:readonly",
        requester_id="reader1",
        lock_type=LockType.SHARED
    )
    logger.info(f"Reader1 acquire: {result1}")
    
    result2 = await lock_manager.acquire_lock(
        lock_id="config:readonly",
        requester_id="reader2",
        lock_type=LockType.SHARED
    )
    logger.info(f"Reader2 acquire: {result2}")
    
    # Get lock status
    status = lock_manager.get_lock_status("config:readonly")
    logger.info(f"Lock status: {status}")
    
    logger.info("\n✓ Lock examples completed\n")


async def queue_example():
    """
    Example: Distributed Queue Usage
    Use case: Task queue for background processing
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 2: Distributed Queue System")
    logger.info("=" * 60)
    
    # Create queue node
    queue_node = QueueNode("node1", "localhost", 8001)
    
    # Create a task queue
    logger.info("\n--- Creating Task Queue ---")
    result = queue_node.create_queue("image_processing")
    logger.info(f"Create queue result: {result}")
    
    # Producer: Enqueue tasks
    logger.info("\n--- Producer: Enqueue Tasks ---")
    
    tasks = [
        {"image": "photo1.jpg", "operation": "resize", "size": "800x600"},
        {"image": "photo2.jpg", "operation": "crop", "coords": [100, 100, 500, 500]},
        {"image": "photo3.jpg", "operation": "filter", "filter": "grayscale"},
        {"image": "photo4.jpg", "operation": "resize", "size": "1920x1080"},
    ]
    
    for i, task in enumerate(tasks):
        result = await queue_node.enqueue(
            queue_name="image_processing",
            message_data=task,
            priority=i % 3  # Different priorities
        )
        logger.info(f"Enqueued task {i+1}: {result['message_id']}")
    
    # Get queue stats
    stats = queue_node.get_queue_stats("image_processing")
    logger.info(f"\nQueue stats: {stats}")
    
    # Consumer: Process tasks
    logger.info("\n--- Consumer: Process Tasks ---")
    
    for i in range(3):
        result = await queue_node.dequeue(
            queue_name="image_processing",
            consumer_id="worker1"
        )
        
        if result['status'] == 'success':
            message = result['message']
            logger.info(f"Worker1 processing: {message['data']}")
            
            # Simulate processing
            await asyncio.sleep(0.5)
            
            # Acknowledge completion
            ack_result = await queue_node.acknowledge(
                message_id=message['message_id'],
                consumer_id="worker1"
            )
            logger.info(f"Task acknowledged: {ack_result['status']}")
    
    logger.info("\n✓ Queue examples completed\n")


async def cache_example():
    """
    Example: Distributed Cache Usage
    Use case: Application data caching
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 3: Distributed Cache Coherence")
    logger.info("=" * 60)
    
    # Create cache nodes
    cache1 = CacheNode("node1", "localhost", 8001, capacity=100)
    cache2 = CacheNode("node2", "localhost", 8002, capacity=100)
    
    # Example 1: Put and Get
    logger.info("\n--- Basic Cache Operations ---")
    
    # Put user data
    user_data = {
        "id": 123,
        "name": "John Doe",
        "email": "john@example.com",
        "role": "admin"
    }
    
    result = await cache1.put(
        key="user:123",
        value=user_data,
        requester_id="app1"
    )
    logger.info(f"Cache PUT result: {result}")
    
    # Get user data
    result = await cache1.get(
        key="user:123",
        requester_id="app1"
    )
    logger.info(f"Cache GET result: {result}")
    
    # Example 2: Cache Hit/Miss
    logger.info("\n--- Cache Hit/Miss Example ---")
    
    # Cache hit
    result = await cache1.get(key="user:123", requester_id="app1")
    logger.info(f"Cache HIT: {result['status']}")
    
    # Cache miss
    result = await cache1.get(key="user:999", requester_id="app1")
    logger.info(f"Cache MISS: {result['status']}")
    
    # Example 3: Cache Invalidation
    logger.info("\n--- Cache Invalidation Example ---")
    
    # Update data (invalidates other caches)
    updated_data = {**user_data, "email": "john.doe@example.com"}
    result = await cache1.put(
        key="user:123",
        value=updated_data,
        requester_id="app1"
    )
    logger.info(f"Cache UPDATE: {result}")
    
    # Explicitly invalidate
    result = await cache1.invalidate(key="user:123")
    logger.info(f"Cache INVALIDATE: {result}")
    
    # Example 4: Cache Statistics
    logger.info("\n--- Cache Statistics ---")
    
    # Perform multiple operations
    for i in range(10):
        key = f"item:{i}"
        await cache1.put(key, {"value": i}, "app1")
        await cache1.get(key, "app1")
    
    stats = cache1.get_stats()
    logger.info(f"Cache stats: {stats}")
    
    logger.info("\n✓ Cache examples completed\n")


async def workflow_example():
    """
    Example: Combined Workflow
    Use case: Order processing system
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 4: Combined Workflow (Lock + Queue + Cache)")
    logger.info("=" * 60)
    
    # Initialize components
    lock_manager = LockManagerNode("node1", "localhost", 8001)
    lock_manager.state = NodeState.LEADER
    
    queue_node = QueueNode("node1", "localhost", 8101)
    cache_node = CacheNode("node1", "localhost", 8201)
    
    # Workflow: Process order
    logger.info("\n--- Order Processing Workflow ---")
    
    order_id = "order:12345"
    
    # Step 1: Acquire lock on order
    logger.info(f"Step 1: Acquiring lock on {order_id}")
    lock_result = await lock_manager.acquire_lock(
        lock_id=order_id,
        requester_id="order_service",
        lock_type=LockType.EXCLUSIVE
    )
    logger.info(f"Lock acquired: {lock_result['status']}")
    
    if lock_result['status'] == 'acquired':
        # Step 2: Check cache for order data
        logger.info(f"\nStep 2: Checking cache for {order_id}")
        cache_result = await cache_node.get(
            key=order_id,
            requester_id="order_service"
        )
        
        if cache_result['status'] == 'miss':
            # Step 3: Load from database (simulated)
            logger.info("Step 3: Loading order from database")
            order_data = {
                "order_id": order_id,
                "customer": "John Doe",
                "items": [
                    {"product": "Laptop", "qty": 1, "price": 1200},
                    {"product": "Mouse", "qty": 2, "price": 25}
                ],
                "total": 1250,
                "status": "pending"
            }
            
            # Step 4: Update cache
            logger.info("Step 4: Updating cache")
            await cache_node.put(
                key=order_id,
                value=order_data,
                requester_id="order_service"
            )
        else:
            order_data = cache_result['value']
            logger.info("Order loaded from cache")
        
        # Step 5: Update order status
        logger.info("\nStep 5: Processing order")
        order_data['status'] = 'processing'
        await cache_node.put(
            key=order_id,
            value=order_data,
            requester_id="order_service"
        )
        
        # Step 6: Enqueue processing tasks
        logger.info("Step 6: Enqueuing processing tasks")
        
        tasks = [
            {"type": "validate_payment", "order_id": order_id},
            {"type": "check_inventory", "order_id": order_id},
            {"type": "prepare_shipment", "order_id": order_id}
        ]
        
        for task in tasks:
            await queue_node.enqueue(
                queue_name="order_tasks",
                message_data=task,
                priority=1
            )
            logger.info(f"  Enqueued: {task['type']}")
        
        # Step 7: Release lock
        logger.info("\nStep 7: Releasing lock")
        await lock_manager.release_lock(
            lock_id=order_id,
            holder_id="order_service"
        )
        
        logger.info(f"\n✓ Order {order_id} workflow completed")
    
    logger.info("\n✓ Workflow example completed\n")


async def failure_scenario_example():
    """
    Example: Handling Failure Scenarios
    Use case: Graceful degradation and recovery
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 5: Failure Handling")
    logger.info("=" * 60)
    
    lock_manager = LockManagerNode("node1", "localhost", 8001)
    
    # Scenario 1: Lock timeout
    logger.info("\n--- Scenario 1: Lock Timeout ---")
    
    lock_manager.state = NodeState.LEADER
    result = await lock_manager.acquire_lock(
        lock_id="timeout_test",
        requester_id="client1",
        lock_type=LockType.EXCLUSIVE,
        timeout=2.0
    )
    logger.info(f"Lock acquired: {result}")
    
    # Wait for timeout
    logger.info("Waiting for lock timeout...")
    await asyncio.sleep(3)
    
    await lock_manager.check_lock_timeouts()
    logger.info("Lock should be automatically released after timeout")
    
    # Scenario 2: Not a leader
    logger.info("\n--- Scenario 2: Not Leader (Redirect) ---")
    
    lock_manager.state = NodeState.FOLLOWER
    lock_manager.leader_id = "node2"
    
    result = await lock_manager.acquire_lock(
        lock_id="test_lock",
        requester_id="client1",
        lock_type=LockType.EXCLUSIVE
    )
    logger.info(f"Result when not leader: {result}")
    logger.info(f"Client should redirect to: {result.get('leader_id')}")
    
    # Scenario 3: Deadlock detection
    logger.info("\n--- Scenario 3: Deadlock Detection ---")
    
    lock_manager.state = NodeState.LEADER
    
    # Setup circular dependency
    await lock_manager.acquire_lock("lock_A", "client1", LockType.EXCLUSIVE)
    await lock_manager.acquire_lock("lock_B", "client2", LockType.EXCLUSIVE)
    
    # Create wait-for graph
    lock_manager.wait_for_graph['client1'] = {'client2'}
    lock_manager.wait_for_graph['client2'] = set()
    
    # This should detect deadlock
    result = await lock_manager.acquire_lock("lock_A", "client2", LockType.EXCLUSIVE)
    logger.info(f"Deadlock detection result: {result.get('message', 'No deadlock')}")
    
    logger.info("\n✓ Failure scenarios completed\n")


async def main():
    """Run all examples"""
    logger.info("\n" + "=" * 60)
    logger.info("Distributed Synchronization System - Usage Examples")
    logger.info("=" * 60 + "\n")
    
    try:
        # Run examples
        await lock_example()
        await queue_example()
        await cache_example()
        await workflow_example()
        await failure_scenario_example()
        
        logger.info("=" * 60)
        logger.info("All examples completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
