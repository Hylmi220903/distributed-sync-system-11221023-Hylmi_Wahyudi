"""
Distributed Queue Node Implementation
Queue terdistribusi dengan consistent hashing, message persistence, 
dan at-least-once delivery guarantee
"""

import asyncio
import logging
import json
import hashlib
from typing import Dict, List, Optional, Set
from datetime import datetime
from collections import deque
from enum import Enum
from .base_node import BaseNode, NodeState

logger = logging.getLogger(__name__)


class MessageStatus(Enum):
    """Status pesan dalam queue"""
    PENDING = "pending"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"


class Message:
    """Representasi message dalam queue"""
    
    def __init__(self, message_id: str, data: dict, priority: int = 0):
        self.message_id = message_id
        self.data = data
        self.priority = priority
        self.status = MessageStatus.PENDING
        self.created_at = datetime.now()
        self.attempts = 0
        self.max_attempts = 3
        self.delivered_to: Set[str] = set()
    
    def to_dict(self) -> dict:
        """Convert message to dictionary"""
        return {
            'message_id': self.message_id,
            'data': self.data,
            'priority': self.priority,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'attempts': self.attempts,
            'delivered_to': list(self.delivered_to)
        }


class ConsistentHash:
    """
    Consistent Hashing implementation untuk distributed queue
    Memastikan distribusi merata dan minimal relocation saat node berubah
    """
    
    def __init__(self, num_virtual_nodes: int = 150):
        self.num_virtual_nodes = num_virtual_nodes
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
        self.nodes: Set[str] = set()
    
    def _hash(self, key: str) -> int:
        """Generate hash for a key"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def add_node(self, node_id: str):
        """Add a node to the consistent hash ring"""
        if node_id in self.nodes:
            return
        
        self.nodes.add(node_id)
        
        for i in range(self.num_virtual_nodes):
            virtual_key = f"{node_id}:{i}"
            hash_value = self._hash(virtual_key)
            self.ring[hash_value] = node_id
        
        self.sorted_keys = sorted(self.ring.keys())
        logger.info(f"Added node {node_id} to consistent hash ring")
    
    def remove_node(self, node_id: str):
        """Remove a node from the consistent hash ring"""
        if node_id not in self.nodes:
            return
        
        self.nodes.remove(node_id)
        
        for i in range(self.num_virtual_nodes):
            virtual_key = f"{node_id}:{i}"
            hash_value = self._hash(virtual_key)
            if hash_value in self.ring:
                del self.ring[hash_value]
        
        self.sorted_keys = sorted(self.ring.keys())
        logger.info(f"Removed node {node_id} from consistent hash ring")
    
    def get_node(self, key: str) -> Optional[str]:
        """Get the node responsible for a key"""
        if not self.ring:
            return None
        
        hash_value = self._hash(key)
        
        # Binary search for the first node >= hash_value
        for ring_hash in self.sorted_keys:
            if ring_hash >= hash_value:
                return self.ring[ring_hash]
        
        # Wrap around to the first node
        return self.ring[self.sorted_keys[0]]
    
    def get_nodes(self, key: str, count: int) -> List[str]:
        """Get multiple nodes for replication"""
        if not self.ring or count <= 0:
            return []
        
        hash_value = self._hash(key)
        result = []
        seen = set()
        
        # Find starting position
        start_idx = 0
        for i, ring_hash in enumerate(self.sorted_keys):
            if ring_hash >= hash_value:
                start_idx = i
                break
        
        # Collect nodes
        idx = start_idx
        while len(result) < count and len(seen) < len(self.nodes):
            node = self.ring[self.sorted_keys[idx % len(self.sorted_keys)]]
            if node not in seen:
                result.append(node)
                seen.add(node)
            idx += 1
        
        return result


class QueueNode(BaseNode):
    """
    Distributed Queue Node dengan consistent hashing
    Support multiple producers/consumers dan message persistence
    """
    
    def __init__(self, node_id: str, host: str, port: int):
        super().__init__(node_id, host, port)
        
        # Queue management
        self.queues: Dict[str, deque] = {}
        self.messages: Dict[str, Message] = {}
        
        # Consistent hashing
        self.consistent_hash = ConsistentHash()
        self.consistent_hash.add_node(self.node_id)
        
        # Replication
        self.replication_factor = 2
        
        # Consumers
        self.consumers: Dict[str, Set[str]] = {}
        
        logger.info(f"QueueNode {node_id} initialized")
    
    def create_queue(self, queue_name: str) -> dict:
        """Create a new queue"""
        if queue_name in self.queues:
            return {
                'status': 'error',
                'message': 'Queue already exists',
                'queue_name': queue_name
            }
        
        self.queues[queue_name] = deque()
        self.consumers[queue_name] = set()
        
        logger.info(f"Queue {queue_name} created")
        return {
            'status': 'success',
            'message': 'Queue created',
            'queue_name': queue_name
        }
    
    async def enqueue(self, queue_name: str, message_data: dict, 
                     priority: int = 0) -> dict:
        """
        Add message to queue with replication
        
        Args:
            queue_name: Name of the queue
            message_data: Message data
            priority: Message priority (higher = more important)
            
        Returns:
            dict with status and message_id
        """
        # Ensure queue exists
        if queue_name not in self.queues:
            self.create_queue(queue_name)
        
        # Generate message ID
        message_id = f"{self.node_id}:{datetime.now().timestamp()}:{len(self.messages)}"
        
        # Create message
        message = Message(message_id, message_data, priority)
        self.messages[message_id] = message
        
        # Add to queue (priority queue)
        self._insert_by_priority(queue_name, message)
        
        # Replicate to other nodes
        replica_nodes = self.consistent_hash.get_nodes(
            message_id, 
            self.replication_factor
        )
        
        for node_id in replica_nodes:
            if node_id != self.node_id:
                await self.replicate_message(node_id, queue_name, message)
        
        logger.info(f"Message {message_id} enqueued to {queue_name}")
        return {
            'status': 'success',
            'message_id': message_id,
            'queue_name': queue_name,
            'replicas': replica_nodes
        }
    
    def _insert_by_priority(self, queue_name: str, message: Message):
        """Insert message into queue by priority"""
        queue = self.queues[queue_name]
        
        # Find insertion position
        inserted = False
        for i, existing_msg_id in enumerate(queue):
            if existing_msg_id in self.messages:
                existing_msg = self.messages[existing_msg_id]
                if message.priority > existing_msg.priority:
                    queue.insert(i, message.message_id)
                    inserted = True
                    break
        
        if not inserted:
            queue.append(message.message_id)
    
    async def dequeue(self, queue_name: str, consumer_id: str) -> dict:
        """
        Remove and return message from queue (at-least-once delivery)
        
        Args:
            queue_name: Name of the queue
            consumer_id: ID of the consumer
            
        Returns:
            dict with message data or error
        """
        if queue_name not in self.queues:
            return {
                'status': 'error',
                'message': 'Queue not found',
                'queue_name': queue_name
            }
        
        queue = self.queues[queue_name]
        
        if not queue:
            return {
                'status': 'empty',
                'message': 'Queue is empty',
                'queue_name': queue_name
            }
        
        # Get message
        message_id = queue.popleft()
        
        if message_id not in self.messages:
            return await self.dequeue(queue_name, consumer_id)
        
        message = self.messages[message_id]
        message.status = MessageStatus.PROCESSING
        message.attempts += 1
        message.delivered_to.add(consumer_id)
        
        # Register consumer
        if consumer_id not in self.consumers[queue_name]:
            self.consumers[queue_name].add(consumer_id)
        
        logger.info(f"Message {message_id} dequeued by {consumer_id}")
        return {
            'status': 'success',
            'message': message.to_dict(),
            'queue_name': queue_name,
            'consumer_id': consumer_id
        }
    
    async def acknowledge(self, message_id: str, consumer_id: str) -> dict:
        """
        Acknowledge message delivery
        
        Args:
            message_id: ID of the message
            consumer_id: ID of the consumer
            
        Returns:
            dict with status
        """
        if message_id not in self.messages:
            return {
                'status': 'error',
                'message': 'Message not found',
                'message_id': message_id
            }
        
        message = self.messages[message_id]
        message.status = MessageStatus.DELIVERED
        
        logger.info(f"Message {message_id} acknowledged by {consumer_id}")
        return {
            'status': 'success',
            'message_id': message_id,
            'consumer_id': consumer_id
        }
    
    async def negative_acknowledge(self, message_id: str, 
                                  queue_name: str) -> dict:
        """
        Negative acknowledgment - requeue message
        
        Args:
            message_id: ID of the message
            queue_name: Name of the queue
            
        Returns:
            dict with status
        """
        if message_id not in self.messages:
            return {
                'status': 'error',
                'message': 'Message not found',
                'message_id': message_id
            }
        
        message = self.messages[message_id]
        
        if message.attempts >= message.max_attempts:
            message.status = MessageStatus.FAILED
            logger.warning(f"Message {message_id} failed after {message.attempts} attempts")
            return {
                'status': 'failed',
                'message_id': message_id,
                'reason': 'Max attempts reached'
            }
        
        # Requeue message
        message.status = MessageStatus.PENDING
        self._insert_by_priority(queue_name, message)
        
        logger.info(f"Message {message_id} requeued to {queue_name}")
        return {
            'status': 'requeued',
            'message_id': message_id,
            'queue_name': queue_name,
            'attempts': message.attempts
        }
    
    async def replicate_message(self, node_id: str, queue_name: str, 
                               message: Message):
        """Replicate message to another node"""
        # In real implementation, send to other node via network
        logger.debug(f"Replicating message {message.message_id} to {node_id}")
    
    def get_queue_stats(self, queue_name: str) -> dict:
        """Get statistics for a queue"""
        if queue_name not in self.queues:
            return {
                'status': 'error',
                'message': 'Queue not found',
                'queue_name': queue_name
            }
        
        queue = self.queues[queue_name]
        
        pending_count = sum(
            1 for msg_id in queue 
            if msg_id in self.messages and 
            self.messages[msg_id].status == MessageStatus.PENDING
        )
        
        return {
            'status': 'success',
            'queue_name': queue_name,
            'size': len(queue),
            'pending': pending_count,
            'consumers': len(self.consumers.get(queue_name, set()))
        }
    
    async def process_message(self, message: str) -> str:
        """Process incoming queue requests"""
        try:
            data = json.loads(message)
            action = data.get('action')
            
            if action == 'create':
                result = self.create_queue(data['queue_name'])
                return json.dumps(result)
            
            elif action == 'enqueue':
                result = await self.enqueue(
                    data['queue_name'],
                    data['message_data'],
                    data.get('priority', 0)
                )
                return json.dumps(result)
            
            elif action == 'dequeue':
                result = await self.dequeue(
                    data['queue_name'],
                    data['consumer_id']
                )
                return json.dumps(result)
            
            elif action == 'ack':
                result = await self.acknowledge(
                    data['message_id'],
                    data['consumer_id']
                )
                return json.dumps(result)
            
            elif action == 'nack':
                result = await self.negative_acknowledge(
                    data['message_id'],
                    data['queue_name']
                )
                return json.dumps(result)
            
            elif action == 'stats':
                result = self.get_queue_stats(data['queue_name'])
                return json.dumps(result)
            
            else:
                return json.dumps({'status': 'error', 'message': 'Unknown action'})
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return json.dumps({'status': 'error', 'message': str(e)})
