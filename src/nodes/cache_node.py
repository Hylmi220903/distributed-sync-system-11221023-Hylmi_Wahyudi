"""
Distributed Cache Node Implementation
Cache coherence dengan protokol MESI/MOSI/MOESI
Support multiple cache nodes dengan cache invalidation dan replacement policy
"""

import asyncio
import logging
import json
from typing import Dict, Optional, Set, List
from datetime import datetime, timedelta
from enum import Enum
from collections import OrderedDict
from .base_node import BaseNode, NodeState

logger = logging.getLogger(__name__)


class CacheState(Enum):
    """
    MESI Protocol States
    M - Modified: Data is dirty and exclusive
    E - Exclusive: Data is clean and exclusive
    S - Shared: Data is clean and may exist in other caches
    I - Invalid: Data is not valid
    """
    MODIFIED = "modified"
    EXCLUSIVE = "exclusive"
    SHARED = "shared"
    INVALID = "invalid"


class ReplacementPolicy(Enum):
    """Cache replacement policies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out


class CacheEntry:
    """Representasi entry dalam cache"""
    
    def __init__(self, key: str, value: any, state: CacheState = CacheState.EXCLUSIVE):
        self.key = key
        self.value = value
        self.state = state
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 0
        self.version = 0
    
    def access(self):
        """Mark cache entry as accessed"""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'key': self.key,
            'value': self.value,
            'state': self.state.value,
            'version': self.version,
            'access_count': self.access_count,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat()
        }


class LRUCache:
    """LRU Cache implementation using OrderedDict"""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get entry from cache"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        entry.access()
        return entry
    
    def put(self, key: str, entry: CacheEntry):
        """Put entry in cache"""
        if key in self.cache:
            self.cache.move_to_end(key)
        
        self.cache[key] = entry
        
        # Evict least recently used if over capacity
        if len(self.cache) > self.capacity:
            evicted_key = next(iter(self.cache))
            evicted_entry = self.cache.pop(evicted_key)
            logger.debug(f"Evicted {evicted_key} from LRU cache")
            return evicted_entry
        
        return None
    
    def remove(self, key: str) -> Optional[CacheEntry]:
        """Remove entry from cache"""
        if key in self.cache:
            return self.cache.pop(key)
        return None
    
    def __len__(self):
        return len(self.cache)
    
    def keys(self):
        return self.cache.keys()


class LFUCache:
    """LFU Cache implementation"""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache: Dict[str, CacheEntry] = {}
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get entry from cache"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        entry.access()
        return entry
    
    def put(self, key: str, entry: CacheEntry):
        """Put entry in cache"""
        self.cache[key] = entry
        
        # Evict least frequently used if over capacity
        if len(self.cache) > self.capacity:
            lfu_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].access_count
            )
            evicted_entry = self.cache.pop(lfu_key)
            logger.debug(f"Evicted {lfu_key} from LFU cache")
            return evicted_entry
        
        return None
    
    def remove(self, key: str) -> Optional[CacheEntry]:
        """Remove entry from cache"""
        if key in self.cache:
            return self.cache.pop(key)
        return None
    
    def __len__(self):
        return len(self.cache)
    
    def keys(self):
        return self.cache.keys()


class CacheNode(BaseNode):
    """
    Distributed Cache Node dengan MESI protocol
    Support cache coherence, invalidation, dan replacement policies
    """
    
    def __init__(self, node_id: str, host: str, port: int,
                 capacity: int = 1000, policy: ReplacementPolicy = ReplacementPolicy.LRU):
        super().__init__(node_id, host, port)
        
        # Cache storage
        self.capacity = capacity
        self.policy = policy
        
        if policy == ReplacementPolicy.LRU:
            self.cache = LRUCache(capacity)
        elif policy == ReplacementPolicy.LFU:
            self.cache = LFUCache(capacity)
        else:
            self.cache = LRUCache(capacity)  # Default to LRU
        
        # Cache coherence
        self.cache_directory: Dict[str, Set[str]] = {}  # key -> set of node_ids
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.invalidations = 0
        
        logger.info(f"CacheNode {node_id} initialized with {policy.value} policy")
    
    async def get(self, key: str, requester_id: str) -> dict:
        """
        Get value from cache with MESI protocol
        
        Args:
            key: Cache key
            requester_id: ID of the requester
            
        Returns:
            dict with value and cache state
        """
        entry = self.cache.get(key)
        
        if entry is None or entry.state == CacheState.INVALID:
            self.misses += 1
            logger.debug(f"Cache miss for key {key}")
            
            # Try to fetch from other nodes
            value = await self.fetch_from_peers(key)
            
            if value is not None:
                # Create new entry in SHARED state
                entry = CacheEntry(key, value, CacheState.SHARED)
                self.cache.put(key, entry)
                
                # Update directory
                if key not in self.cache_directory:
                    self.cache_directory[key] = set()
                self.cache_directory[key].add(self.node_id)
                
                return {
                    'status': 'hit',
                    'key': key,
                    'value': value,
                    'state': CacheState.SHARED.value,
                    'source': 'peer'
                }
            
            return {
                'status': 'miss',
                'key': key,
                'message': 'Key not found in cache'
            }
        
        self.hits += 1
        logger.debug(f"Cache hit for key {key} (state: {entry.state.value})")
        
        return {
            'status': 'hit',
            'key': key,
            'value': entry.value,
            'state': entry.state.value,
            'version': entry.version
        }
    
    async def put(self, key: str, value: any, requester_id: str) -> dict:
        """
        Put value in cache with MESI protocol
        
        Args:
            key: Cache key
            value: Value to cache
            requester_id: ID of the requester
            
        Returns:
            dict with status
        """
        # Check if key exists in other caches
        if key in self.cache_directory and len(self.cache_directory[key]) > 1:
            # Invalidate other copies
            await self.invalidate_peers(key, exclude_node=self.node_id)
            state = CacheState.MODIFIED
        else:
            state = CacheState.EXCLUSIVE
        
        # Create or update entry
        entry = self.cache.get(key)
        if entry:
            entry.value = value
            entry.state = state
            entry.version += 1
            entry.access()
        else:
            entry = CacheEntry(key, value, state)
            evicted = self.cache.put(key, entry)
            
            if evicted and evicted.state == CacheState.MODIFIED:
                # Write back evicted modified entry
                await self.write_back(evicted)
        
        # Update directory
        if key not in self.cache_directory:
            self.cache_directory[key] = set()
        self.cache_directory[key] = {self.node_id}
        
        logger.info(f"Cached key {key} in state {state.value}")
        
        return {
            'status': 'success',
            'key': key,
            'state': state.value,
            'version': entry.version
        }
    
    async def invalidate(self, key: str) -> dict:
        """
        Invalidate a cache entry
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            dict with status
        """
        entry = self.cache.get(key)
        
        if entry is None:
            return {
                'status': 'not_found',
                'key': key
            }
        
        # If modified, write back before invalidating
        if entry.state == CacheState.MODIFIED:
            await self.write_back(entry)
        
        # Change state to invalid
        entry.state = CacheState.INVALID
        self.invalidations += 1
        
        # Remove from directory
        if key in self.cache_directory:
            self.cache_directory[key].discard(self.node_id)
            if not self.cache_directory[key]:
                del self.cache_directory[key]
        
        logger.info(f"Invalidated cache entry for key {key}")
        
        return {
            'status': 'invalidated',
            'key': key
        }
    
    async def invalidate_peers(self, key: str, exclude_node: Optional[str] = None):
        """
        Send invalidation to peer caches
        
        Args:
            key: Cache key to invalidate
            exclude_node: Node ID to exclude from invalidation
        """
        if key not in self.cache_directory:
            return
        
        for node_id in list(self.cache_directory[key]):
            if node_id != exclude_node and node_id != self.node_id:
                # In real implementation, send invalidation message to peer
                logger.debug(f"Sending invalidation for {key} to {node_id}")
                
                # Simulate invalidation
                if node_id in self.cluster_nodes:
                    # Would send message to peer node
                    pass
        
        # Update directory
        if exclude_node:
            self.cache_directory[key] = {exclude_node}
        else:
            self.cache_directory[key] = set()
    
    async def fetch_from_peers(self, key: str) -> Optional[any]:
        """
        Fetch value from peer caches
        
        Args:
            key: Cache key to fetch
            
        Returns:
            Value if found, None otherwise
        """
        if key not in self.cache_directory:
            return None
        
        for node_id in self.cache_directory[key]:
            if node_id != self.node_id and node_id in self.cluster_nodes:
                # In real implementation, request value from peer
                logger.debug(f"Fetching {key} from peer {node_id}")
                
                # Simulate fetch
                # Would receive value from peer node
                pass
        
        return None
    
    async def write_back(self, entry: CacheEntry):
        """
        Write back modified cache entry to backing store
        
        Args:
            entry: Cache entry to write back
        """
        if entry.state == CacheState.MODIFIED:
            logger.info(f"Writing back modified entry {entry.key}")
            
            # In real implementation, write to persistent storage or main memory
            # For now, just log it
            entry.state = CacheState.EXCLUSIVE
    
    async def delete(self, key: str) -> dict:
        """
        Delete entry from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            dict with status
        """
        # Invalidate in all caches first
        await self.invalidate_peers(key)
        
        entry = self.cache.remove(key)
        
        if entry is None:
            return {
                'status': 'not_found',
                'key': key
            }
        
        # Write back if modified
        if entry.state == CacheState.MODIFIED:
            await self.write_back(entry)
        
        # Remove from directory
        if key in self.cache_directory:
            del self.cache_directory[key]
        
        logger.info(f"Deleted cache entry for key {key}")
        
        return {
            'status': 'deleted',
            'key': key
        }
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'node_id': self.node_id,
            'policy': self.policy.value,
            'capacity': self.capacity,
            'size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'invalidations': self.invalidations,
            'total_requests': total_requests
        }
    
    def get_cache_state(self) -> List[dict]:
        """Get state of all cache entries"""
        entries = []
        for key in self.cache.keys():
            entry = self.cache.get(key)
            if entry:
                entries.append(entry.to_dict())
        return entries
    
    async def process_message(self, message: str) -> str:
        """Process incoming cache requests"""
        try:
            data = json.loads(message)
            action = data.get('action')
            
            if action == 'get':
                result = await self.get(
                    data['key'],
                    data.get('requester_id', 'unknown')
                )
                return json.dumps(result)
            
            elif action == 'put':
                result = await self.put(
                    data['key'],
                    data['value'],
                    data.get('requester_id', 'unknown')
                )
                return json.dumps(result)
            
            elif action == 'invalidate':
                result = await self.invalidate(data['key'])
                return json.dumps(result)
            
            elif action == 'delete':
                result = await self.delete(data['key'])
                return json.dumps(result)
            
            elif action == 'stats':
                result = self.get_stats()
                return json.dumps(result)
            
            elif action == 'state':
                result = {'entries': self.get_cache_state()}
                return json.dumps(result)
            
            else:
                return json.dumps({'status': 'error', 'message': 'Unknown action'})
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return json.dumps({'status': 'error', 'message': str(e)})
