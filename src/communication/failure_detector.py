"""
Failure Detector Implementation
Phi Accrual Failure Detector untuk mendeteksi node failures
"""

import asyncio
import logging
import time
import math
from typing import Dict, List, Optional
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    """Status node dalam cluster"""
    ALIVE = "alive"
    SUSPECTED = "suspected"
    DEAD = "dead"
    UNKNOWN = "unknown"


class PhiAccrualFailureDetector:
    """
    Phi Accrual Failure Detector
    
    Menggunakan distribusi probabilitas untuk mendeteksi failures
    dengan dynamic threshold adjustment
    """
    
    def __init__(self, threshold: float = 8.0, max_sample_size: int = 200):
        """
        Args:
            threshold: Phi threshold untuk menandai node sebagai suspected
            max_sample_size: Maximum number of heartbeat samples to keep
        """
        self.threshold = threshold
        self.max_sample_size = max_sample_size
        
        # Heartbeat intervals history
        self.intervals: deque = deque(maxlen=max_sample_size)
        
        # Statistics
        self.mean = 0.0
        self.variance = 0.0
        self.std_deviation = 0.0
        
        # Last heartbeat time
        self.last_heartbeat = time.time()
    
    def heartbeat(self):
        """Record a heartbeat"""
        current_time = time.time()
        interval = current_time - self.last_heartbeat
        
        if len(self.intervals) > 0:  # Skip first heartbeat
            self.intervals.append(interval)
            self._update_statistics()
        
        self.last_heartbeat = current_time
    
    def _update_statistics(self):
        """Update mean and variance of intervals"""
        if len(self.intervals) < 2:
            return
        
        # Calculate mean
        self.mean = sum(self.intervals) / len(self.intervals)
        
        # Calculate variance
        squared_diffs = [(x - self.mean) ** 2 for x in self.intervals]
        self.variance = sum(squared_diffs) / len(self.intervals)
        
        # Calculate standard deviation
        self.std_deviation = math.sqrt(self.variance)
    
    def phi(self) -> float:
        """
        Calculate phi value (suspicion level)
        
        Returns:
            Phi value (higher = more suspicious)
        """
        if len(self.intervals) < 2:
            return 0.0
        
        elapsed = time.time() - self.last_heartbeat
        
        # Avoid division by zero
        if self.std_deviation < 0.0001:
            return 0.0
        
        # Calculate phi using normal distribution
        # phi = -log10(P(t_now))
        exponent = -((elapsed - self.mean) ** 2) / (2 * self.variance)
        p = math.exp(exponent) / (self.std_deviation * math.sqrt(2 * math.pi))
        
        if p > 0:
            phi_value = -math.log10(p)
        else:
            phi_value = float('inf')
        
        return phi_value
    
    def is_available(self) -> bool:
        """
        Check if node is available
        
        Returns:
            True if phi < threshold
        """
        return self.phi() < self.threshold


class FailureDetector:
    """
    Failure Detector untuk monitoring cluster nodes
    Menggunakan Phi Accrual untuk adaptive failure detection
    """
    
    def __init__(self, node_id: str, heartbeat_interval: float = 1.0,
                 phi_threshold: float = 8.0):
        """
        Args:
            node_id: ID of this node
            heartbeat_interval: Interval untuk mengirim heartbeat (seconds)
            phi_threshold: Threshold untuk failure detection
        """
        self.node_id = node_id
        self.heartbeat_interval = heartbeat_interval
        self.phi_threshold = phi_threshold
        
        # Node tracking
        self.nodes: Dict[str, PhiAccrualFailureDetector] = {}
        self.node_status: Dict[str, NodeStatus] = {}
        
        # Callbacks
        self.on_node_suspected = None
        self.on_node_recovered = None
        self.on_node_dead = None
        
        # Running state
        self.running = False
        
        logger.info(f"FailureDetector initialized for node {node_id}")
    
    def register_node(self, node_id: str):
        """
        Register a node for monitoring
        
        Args:
            node_id: Node ID to monitor
        """
        if node_id not in self.nodes:
            self.nodes[node_id] = PhiAccrualFailureDetector(
                threshold=self.phi_threshold
            )
            self.node_status[node_id] = NodeStatus.UNKNOWN
            logger.info(f"Registered node {node_id} for monitoring")
    
    def unregister_node(self, node_id: str):
        """
        Unregister a node
        
        Args:
            node_id: Node ID to unregister
        """
        if node_id in self.nodes:
            del self.nodes[node_id]
            del self.node_status[node_id]
            logger.info(f"Unregistered node {node_id}")
    
    def record_heartbeat(self, node_id: str):
        """
        Record heartbeat from a node
        
        Args:
            node_id: Node ID that sent heartbeat
        """
        if node_id not in self.nodes:
            self.register_node(node_id)
        
        detector = self.nodes[node_id]
        detector.heartbeat()
        
        # Update status
        old_status = self.node_status[node_id]
        
        if detector.is_available():
            self.node_status[node_id] = NodeStatus.ALIVE
            
            # Check if node recovered
            if old_status in [NodeStatus.SUSPECTED, NodeStatus.DEAD]:
                logger.info(f"Node {node_id} recovered")
                if self.on_node_recovered:
                    asyncio.create_task(self.on_node_recovered(node_id))
        
        logger.debug(f"Heartbeat from {node_id}, phi={detector.phi():.2f}")
    
    async def monitor_nodes(self):
        """Monitor all registered nodes periodically"""
        while self.running:
            for node_id, detector in self.nodes.items():
                old_status = self.node_status[node_id]
                phi = detector.phi()
                
                # Check if node should be suspected
                if not detector.is_available():
                    if old_status == NodeStatus.ALIVE:
                        self.node_status[node_id] = NodeStatus.SUSPECTED
                        logger.warning(f"Node {node_id} suspected (phi={phi:.2f})")
                        
                        if self.on_node_suspected:
                            await self.on_node_suspected(node_id)
                    
                    # If suspected for too long, mark as dead
                    elif old_status == NodeStatus.SUSPECTED and phi > self.phi_threshold * 2:
                        self.node_status[node_id] = NodeStatus.DEAD
                        logger.error(f"Node {node_id} marked as DEAD (phi={phi:.2f})")
                        
                        if self.on_node_dead:
                            await self.on_node_dead(node_id)
            
            await asyncio.sleep(self.heartbeat_interval)
    
    async def start(self):
        """Start failure detector"""
        self.running = True
        logger.info("FailureDetector started")
        await self.monitor_nodes()
    
    def stop(self):
        """Stop failure detector"""
        self.running = False
        logger.info("FailureDetector stopped")
    
    def get_node_status(self, node_id: str) -> NodeStatus:
        """
        Get status of a node
        
        Args:
            node_id: Node ID
            
        Returns:
            Node status
        """
        return self.node_status.get(node_id, NodeStatus.UNKNOWN)
    
    def get_alive_nodes(self) -> List[str]:
        """Get list of alive nodes"""
        return [
            node_id for node_id, status in self.node_status.items()
            if status == NodeStatus.ALIVE
        ]
    
    def get_dead_nodes(self) -> List[str]:
        """Get list of dead nodes"""
        return [
            node_id for node_id, status in self.node_status.items()
            if status == NodeStatus.DEAD
        ]
    
    def get_suspected_nodes(self) -> List[str]:
        """Get list of suspected nodes"""
        return [
            node_id for node_id, status in self.node_status.items()
            if status == NodeStatus.SUSPECTED
        ]
    
    def get_stats(self) -> dict:
        """Get failure detector statistics"""
        node_details = {}
        for node_id, detector in self.nodes.items():
            node_details[node_id] = {
                'status': self.node_status[node_id].value,
                'phi': detector.phi(),
                'mean_interval': detector.mean,
                'std_deviation': detector.std_deviation
            }
        
        return {
            'node_id': self.node_id,
            'monitored_nodes': len(self.nodes),
            'alive': len(self.get_alive_nodes()),
            'suspected': len(self.get_suspected_nodes()),
            'dead': len(self.get_dead_nodes()),
            'nodes': node_details
        }
