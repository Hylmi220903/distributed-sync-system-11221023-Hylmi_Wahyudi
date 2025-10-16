"""
Lock Manager Node with Distributed Lock Implementation
Menggunakan algoritma Raft Consensus untuk distributed locking
Support untuk shared dan exclusive locks dengan deadlock detection
"""

import asyncio
import logging
from typing import Dict, Set, Optional, List
from enum import Enum
from datetime import datetime, timedelta
import json
from .base_node import BaseNode, NodeState

logger = logging.getLogger(__name__)


class LockType(Enum):
    """Tipe lock yang didukung"""
    SHARED = "shared"
    EXCLUSIVE = "exclusive"


class LockStatus(Enum):
    """Status lock"""
    ACQUIRED = "acquired"
    WAITING = "waiting"
    RELEASED = "released"
    TIMEOUT = "timeout"


class Lock:
    """Representasi lock object"""
    
    def __init__(self, lock_id: str, lock_type: LockType, holder_id: str):
        self.lock_id = lock_id
        self.lock_type = lock_type
        self.holders: Set[str] = {holder_id} if lock_type == LockType.SHARED else {holder_id}
        self.waiting_queue: List[dict] = []
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.timeout = 30.0  # Default 30 seconds
    
    def can_acquire(self, requester_id: str, lock_type: LockType) -> bool:
        """Check if lock can be acquired"""
        if not self.holders:
            return True
        
        if lock_type == LockType.SHARED and self.lock_type == LockType.SHARED:
            return True
        
        return False
    
    def acquire(self, holder_id: str, lock_type: LockType) -> bool:
        """Acquire lock"""
        if self.can_acquire(holder_id, lock_type):
            self.holders.add(holder_id)
            self.lock_type = lock_type
            self.last_accessed = datetime.now()
            return True
        return False
    
    def release(self, holder_id: str) -> bool:
        """Release lock"""
        if holder_id in self.holders:
            self.holders.remove(holder_id)
            self.last_accessed = datetime.now()
            return True
        return False
    
    def is_locked(self) -> bool:
        """Check if lock is currently held"""
        return len(self.holders) > 0
    
    def is_expired(self) -> bool:
        """Check if lock has expired"""
        elapsed = (datetime.now() - self.last_accessed).total_seconds()
        return elapsed > self.timeout


class LockManagerNode(BaseNode):
    """
    Distributed Lock Manager dengan Raft Consensus
    Mendukung shared locks, exclusive locks, dan deadlock detection
    """
    
    def __init__(self, node_id: str, host: str, port: int):
        super().__init__(node_id, host, port)
        
        # Lock management
        self.locks: Dict[str, Lock] = {}
        self.lock_requests: Dict[str, dict] = {}
        
        # Deadlock detection
        self.wait_for_graph: Dict[str, Set[str]] = {}
        
        logger.info(f"LockManagerNode {node_id} initialized")
    
    async def acquire_lock(self, lock_id: str, requester_id: str, 
                          lock_type: LockType, timeout: float = 30.0) -> dict:
        """
        Acquire a distributed lock
        
        Args:
            lock_id: Unique identifier for the lock
            requester_id: ID of the node/client requesting the lock
            lock_type: Type of lock (SHARED or EXCLUSIVE)
            timeout: Lock timeout in seconds
            
        Returns:
            dict with status and lock information
        """
        logger.info(f"Lock request: {lock_id} by {requester_id} ({lock_type.value})")
        
        # Only leader can grant locks
        if self.state != NodeState.LEADER:
            return {
                'status': 'error',
                'message': 'Not the leader',
                'leader_id': self.leader_id
            }
        
        # Check for deadlock
        if self.would_cause_deadlock(requester_id, lock_id):
            logger.warning(f"Deadlock detected for {requester_id} requesting {lock_id}")
            return {
                'status': 'error',
                'message': 'Deadlock detected',
                'lock_id': lock_id
            }
        
        # Create lock if doesn't exist
        if lock_id not in self.locks:
            self.locks[lock_id] = Lock(lock_id, lock_type, requester_id)
            self.locks[lock_id].timeout = timeout
            
            logger.info(f"Lock {lock_id} acquired by {requester_id}")
            return {
                'status': 'acquired',
                'lock_id': lock_id,
                'holder_id': requester_id,
                'lock_type': lock_type.value
            }
        
        lock = self.locks[lock_id]
        
        # Try to acquire existing lock
        if lock.acquire(requester_id, lock_type):
            logger.info(f"Lock {lock_id} acquired by {requester_id}")
            return {
                'status': 'acquired',
                'lock_id': lock_id,
                'holder_id': requester_id,
                'lock_type': lock_type.value
            }
        
        # Add to waiting queue
        lock.waiting_queue.append({
            'requester_id': requester_id,
            'lock_type': lock_type,
            'requested_at': datetime.now()
        })
        
        # Update wait-for graph
        if requester_id not in self.wait_for_graph:
            self.wait_for_graph[requester_id] = set()
        self.wait_for_graph[requester_id].update(lock.holders)
        
        logger.info(f"Lock {lock_id} waiting for {requester_id}")
        return {
            'status': 'waiting',
            'lock_id': lock_id,
            'requester_id': requester_id,
            'queue_position': len(lock.waiting_queue)
        }
    
    async def release_lock(self, lock_id: str, holder_id: str) -> dict:
        """
        Release a distributed lock
        
        Args:
            lock_id: Unique identifier for the lock
            holder_id: ID of the current lock holder
            
        Returns:
            dict with status information
        """
        logger.info(f"Lock release: {lock_id} by {holder_id}")
        
        if self.state != NodeState.LEADER:
            return {
                'status': 'error',
                'message': 'Not the leader',
                'leader_id': self.leader_id
            }
        
        if lock_id not in self.locks:
            return {
                'status': 'error',
                'message': 'Lock not found',
                'lock_id': lock_id
            }
        
        lock = self.locks[lock_id]
        
        if not lock.release(holder_id):
            return {
                'status': 'error',
                'message': 'Not a lock holder',
                'lock_id': lock_id
            }
        
        # Remove from wait-for graph
        if holder_id in self.wait_for_graph:
            del self.wait_for_graph[holder_id]
        
        # Process waiting queue
        if not lock.is_locked() and lock.waiting_queue:
            await self.process_waiting_queue(lock_id)
        
        # Clean up if no holders and no waiting
        if not lock.is_locked() and not lock.waiting_queue:
            del self.locks[lock_id]
        
        logger.info(f"Lock {lock_id} released by {holder_id}")
        return {
            'status': 'released',
            'lock_id': lock_id,
            'holder_id': holder_id
        }
    
    async def process_waiting_queue(self, lock_id: str):
        """Process waiting queue for a lock"""
        if lock_id not in self.locks:
            return
        
        lock = self.locks[lock_id]
        
        while lock.waiting_queue and not lock.is_locked():
            waiting = lock.waiting_queue.pop(0)
            requester_id = waiting['requester_id']
            lock_type = waiting['lock_type']
            
            if lock.acquire(requester_id, lock_type):
                logger.info(f"Lock {lock_id} granted to {requester_id} from queue")
                
                # Remove from wait-for graph
                if requester_id in self.wait_for_graph:
                    del self.wait_for_graph[requester_id]
                
                # Notify requester (in real implementation)
                break
    
    def would_cause_deadlock(self, requester_id: str, lock_id: str) -> bool:
        """
        Detect if acquiring lock would cause deadlock using cycle detection
        
        Args:
            requester_id: ID requesting the lock
            lock_id: Lock being requested
            
        Returns:
            True if deadlock would occur
        """
        if lock_id not in self.locks:
            return False
        
        lock = self.locks[lock_id]
        
        # Build temporary graph with new edge
        temp_graph = dict(self.wait_for_graph)
        if requester_id not in temp_graph:
            temp_graph[requester_id] = set()
        
        temp_graph[requester_id] = temp_graph[requester_id].union(lock.holders)
        
        # Check for cycle using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            if node in temp_graph:
                for neighbor in temp_graph[node]:
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
            
            rec_stack.remove(node)
            return False
        
        return has_cycle(requester_id)
    
    async def check_lock_timeouts(self):
        """Check and release expired locks"""
        expired_locks = []
        
        for lock_id, lock in self.locks.items():
            if lock.is_expired():
                expired_locks.append((lock_id, lock.holders.copy()))
        
        for lock_id, holders in expired_locks:
            for holder_id in holders:
                await self.release_lock(lock_id, holder_id)
                logger.warning(f"Lock {lock_id} expired for {holder_id}")
    
    async def start(self):
        """Start the lock manager node"""
        # Start timeout checker
        asyncio.create_task(self.timeout_checker())
        await super().start()
    
    async def timeout_checker(self):
        """Periodically check for lock timeouts"""
        while self.running:
            if self.state == NodeState.LEADER:
                await self.check_lock_timeouts()
            await asyncio.sleep(5.0)
    
    def get_lock_status(self, lock_id: str) -> dict:
        """Get status of a specific lock"""
        if lock_id not in self.locks:
            return {'status': 'not_found', 'lock_id': lock_id}
        
        lock = self.locks[lock_id]
        return {
            'status': 'found',
            'lock_id': lock_id,
            'lock_type': lock.lock_type.value,
            'holders': list(lock.holders),
            'waiting_count': len(lock.waiting_queue),
            'created_at': lock.created_at.isoformat(),
            'last_accessed': lock.last_accessed.isoformat()
        }
    
    def get_all_locks(self) -> List[dict]:
        """Get status of all locks"""
        return [self.get_lock_status(lock_id) for lock_id in self.locks.keys()]
    
    async def process_message(self, message: str) -> str:
        """Process incoming lock requests"""
        try:
            data = json.loads(message)
            action = data.get('action')
            
            if action == 'acquire':
                lock_id = data['lock_id']
                requester_id = data['requester_id']
                lock_type = LockType(data['lock_type'])
                timeout = data.get('timeout', 30.0)
                
                result = await self.acquire_lock(lock_id, requester_id, lock_type, timeout)
                return json.dumps(result)
            
            elif action == 'release':
                lock_id = data['lock_id']
                holder_id = data['holder_id']
                
                result = await self.release_lock(lock_id, holder_id)
                return json.dumps(result)
            
            elif action == 'status':
                lock_id = data.get('lock_id')
                if lock_id:
                    result = self.get_lock_status(lock_id)
                else:
                    result = {'locks': self.get_all_locks()}
                return json.dumps(result)
            
            else:
                return json.dumps({'status': 'error', 'message': 'Unknown action'})
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return json.dumps({'status': 'error', 'message': str(e)})
