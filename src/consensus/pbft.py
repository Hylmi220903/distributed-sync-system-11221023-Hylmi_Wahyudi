"""
PBFT (Practical Byzantine Fault Tolerance) Implementation
Optional bonus feature untuk advanced consensus
"""

import asyncio
import logging
import hashlib
import json
from typing import Dict, List, Set, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class PBFTState(Enum):
    """PBFT node states"""
    IDLE = "idle"
    PRE_PREPARED = "pre_prepared"
    PREPARED = "prepared"
    COMMITTED = "committed"


@dataclass
class PBFTRequest:
    """Client request in PBFT"""
    operation: dict
    timestamp: float
    client_id: str
    
    def digest(self) -> str:
        """Calculate request digest"""
        data = json.dumps({
            'operation': self.operation,
            'timestamp': self.timestamp,
            'client_id': self.client_id
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class PBFTMessage:
    """PBFT protocol message"""
    message_type: str  # PRE-PREPARE, PREPARE, COMMIT
    view: int
    sequence: int
    digest: str
    replica_id: str


class PBFTNode:
    """
    Practical Byzantine Fault Tolerance Implementation
    
    PBFT dapat menangani Byzantine failures (malicious nodes) sampai f failures
    dengan minimal 3f + 1 nodes.
    
    Phases:
    1. Pre-Prepare: Primary broadcasts request
    2. Prepare: Replicas agree on order
    3. Commit: Execute after 2f + 1 agrees
    """
    
    def __init__(self, node_id: str, cluster_nodes: List[str], is_primary: bool = False):
        self.node_id = node_id
        self.cluster_nodes = cluster_nodes
        self.cluster_size = len(cluster_nodes)
        
        # Byzantine fault tolerance: can handle f failures
        self.f = (self.cluster_size - 1) // 3
        self.quorum_size = 2 * self.f + 1
        
        # View and sequence numbers
        self.view = 0
        self.sequence = 0
        self.is_primary = is_primary
        
        # Message logs
        self.pre_prepare_log: Dict[int, PBFTMessage] = {}
        self.prepare_log: Dict[int, Set[str]] = {}  # seq -> set of replica_ids
        self.commit_log: Dict[int, Set[str]] = {}
        
        # Request tracking
        self.executed_requests: Set[str] = set()
        
        logger.info(f"PBFTNode {node_id} initialized (primary={is_primary}, f={self.f})")
    
    async def handle_client_request(self, request: PBFTRequest) -> dict:
        """
        Handle client request (primary only)
        
        Args:
            request: Client request
            
        Returns:
            dict with result
        """
        if not self.is_primary:
            return {
                'status': 'error',
                'message': 'Not the primary'
            }
        
        request_digest = request.digest()
        
        # Check if already executed
        if request_digest in self.executed_requests:
            return {
                'status': 'already_executed',
                'digest': request_digest
            }
        
        # Assign sequence number
        self.sequence += 1
        seq = self.sequence
        
        # Create PRE-PREPARE message
        pre_prepare_msg = PBFTMessage(
            message_type='PRE-PREPARE',
            view=self.view,
            sequence=seq,
            digest=request_digest,
            replica_id=self.node_id
        )
        
        # Store in log
        self.pre_prepare_log[seq] = pre_prepare_msg
        
        # Broadcast to all replicas
        logger.info(f"Primary sending PRE-PREPARE for seq {seq}")
        await self.broadcast_pre_prepare(pre_prepare_msg, request)
        
        return {
            'status': 'pre_prepared',
            'sequence': seq,
            'digest': request_digest
        }
    
    async def broadcast_pre_prepare(self, message: PBFTMessage, request: PBFTRequest):
        """Broadcast PRE-PREPARE to all replicas"""
        tasks = []
        for node_id in self.cluster_nodes:
            if node_id != self.node_id:
                tasks.append(
                    self.send_message(node_id, 'PRE-PREPARE', {
                        'message': message.__dict__,
                        'request': request.__dict__
                    })
                )
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handle_pre_prepare(self, message: PBFTMessage, request: PBFTRequest):
        """
        Handle PRE-PREPARE message (replicas)
        
        Args:
            message: PRE-PREPARE message
            request: Associated request
        """
        seq = message.sequence
        view = message.view
        digest = message.digest
        
        # Validate PRE-PREPARE
        if view != self.view:
            logger.warning(f"Wrong view: expected {self.view}, got {view}")
            return
        
        if seq in self.pre_prepare_log:
            logger.warning(f"Already have PRE-PREPARE for seq {seq}")
            return
        
        # Verify digest matches request
        if request.digest() != digest:
            logger.warning(f"Digest mismatch for seq {seq}")
            return
        
        # Accept PRE-PREPARE
        self.pre_prepare_log[seq] = message
        
        logger.info(f"Replica accepted PRE-PREPARE for seq {seq}")
        
        # Send PREPARE
        prepare_msg = PBFTMessage(
            message_type='PREPARE',
            view=self.view,
            sequence=seq,
            digest=digest,
            replica_id=self.node_id
        )
        
        await self.broadcast_prepare(prepare_msg)
    
    async def broadcast_prepare(self, message: PBFTMessage):
        """Broadcast PREPARE to all replicas"""
        tasks = []
        for node_id in self.cluster_nodes:
            if node_id != self.node_id:
                tasks.append(
                    self.send_message(node_id, 'PREPARE', {
                        'message': message.__dict__
                    })
                )
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handle_prepare(self, message: PBFTMessage):
        """
        Handle PREPARE message
        
        Args:
            message: PREPARE message
        """
        seq = message.sequence
        replica_id = message.replica_id
        
        # Track PREPARE messages
        if seq not in self.prepare_log:
            self.prepare_log[seq] = set()
        
        self.prepare_log[seq].add(replica_id)
        
        # Check if we have 2f PREPARE messages (including ours)
        if len(self.prepare_log[seq]) >= 2 * self.f:
            logger.info(f"Node {self.node_id} prepared for seq {seq}")
            
            # Send COMMIT
            commit_msg = PBFTMessage(
                message_type='COMMIT',
                view=self.view,
                sequence=seq,
                digest=message.digest,
                replica_id=self.node_id
            )
            
            await self.broadcast_commit(commit_msg)
    
    async def broadcast_commit(self, message: PBFTMessage):
        """Broadcast COMMIT to all replicas"""
        tasks = []
        for node_id in self.cluster_nodes:
            if node_id != self.node_id:
                tasks.append(
                    self.send_message(node_id, 'COMMIT', {
                        'message': message.__dict__
                    })
                )
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handle_commit(self, message: PBFTMessage):
        """
        Handle COMMIT message
        
        Args:
            message: COMMIT message
        """
        seq = message.sequence
        replica_id = message.replica_id
        digest = message.digest
        
        # Track COMMIT messages
        if seq not in self.commit_log:
            self.commit_log[seq] = set()
        
        self.commit_log[seq].add(replica_id)
        
        # Check if we have 2f + 1 COMMIT messages
        if len(self.commit_log[seq]) >= self.quorum_size:
            logger.info(f"Node {self.node_id} committing seq {seq}")
            
            # Execute request
            await self.execute_request(seq, digest)
    
    async def execute_request(self, sequence: int, digest: str):
        """
        Execute committed request
        
        Args:
            sequence: Sequence number
            digest: Request digest
        """
        if digest in self.executed_requests:
            logger.info(f"Request {digest} already executed")
            return
        
        # Mark as executed
        self.executed_requests.add(digest)
        
        logger.info(f"Executed request seq {sequence}, digest {digest}")
        
        # In real implementation, apply to state machine
    
    async def send_message(self, target_node: str, msg_type: str, data: dict):
        """Send message to another node"""
        # In real implementation, send via network
        logger.debug(f"Sending {msg_type} to {target_node}")
    
    async def view_change(self, new_view: int):
        """
        Initiate view change (when primary is suspected faulty)
        
        Args:
            new_view: New view number
        """
        logger.info(f"Node {self.node_id} initiating view change to view {new_view}")
        
        self.view = new_view
        
        # Determine new primary
        primary_index = new_view % self.cluster_size
        new_primary = self.cluster_nodes[primary_index]
        
        self.is_primary = (new_primary == self.node_id)
        
        logger.info(f"New primary is {new_primary}")
    
    def get_state(self) -> dict:
        """Get current PBFT state"""
        return {
            'node_id': self.node_id,
            'is_primary': self.is_primary,
            'view': self.view,
            'sequence': self.sequence,
            'f': self.f,
            'quorum_size': self.quorum_size,
            'executed_count': len(self.executed_requests)
        }
