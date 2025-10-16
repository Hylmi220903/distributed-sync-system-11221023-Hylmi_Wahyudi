"""
Base Node Implementation
Node dasar untuk sistem terdistribusi
"""

import asyncio
import logging
from typing import Dict, Set, Optional
from enum import Enum
import time
import os

logger = logging.getLogger(__name__)


class NodeState(Enum):
    """Status node dalam cluster"""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"
    OFFLINE = "offline"


class BaseNode:
    """
    Base node implementation untuk distributed system
    Menggunakan Raft consensus algorithm
    """
    
    def __init__(self, node_id: str, host: str, port: int):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.state = NodeState.FOLLOWER
        
        # Raft state
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = 0
        self.last_applied = 0
        
        # Cluster information
        self.cluster_nodes: Dict[str, dict] = {}
        self.leader_id: Optional[str] = None
        
        # Timing
        self.last_heartbeat = time.time()
        self.election_timeout = float(os.getenv('ELECTION_TIMEOUT_MIN', '3.0'))
        self.heartbeat_interval = float(os.getenv('HEARTBEAT_INTERVAL', '1.0'))
        
        # Network
        self.running = False
        self.server = None
        
        logger.info(f"Node {self.node_id} initialized at {self.host}:{self.port}")
    
    async def start(self):
        """Start the node"""
        self.running = True
        logger.info(f"Starting node {self.node_id}")
        
        # Start election timer
        asyncio.create_task(self.election_timer())
        
        # Start heartbeat (if leader)
        asyncio.create_task(self.heartbeat_sender())
        
        # Start server
        await self.start_server()
    
    async def stop(self):
        """Stop the node"""
        self.running = False
        self.state = NodeState.OFFLINE
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info(f"Node {self.node_id} stopped")
    
    async def start_server(self):
        """Start the node server"""
        self.server = await asyncio.start_server(
            self.handle_connection,
            self.host,
            self.port
        )
        logger.info(f"Node {self.node_id} listening on {self.host}:{self.port}")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def handle_connection(self, reader, writer):
        """Handle incoming connections"""
        try:
            data = await reader.read(4096)
            message = data.decode()
            
            response = await self.process_message(message)
            
            writer.write(response.encode())
            await writer.drain()
        except Exception as e:
            logger.error(f"Error handling connection: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def process_message(self, message: str) -> str:
        """Process incoming message"""
        # To be implemented by subclasses
        return "OK"
    
    async def election_timer(self):
        """Election timeout timer"""
        import random
        
        while self.running:
            if self.state != NodeState.LEADER:
                # Check if election timeout elapsed
                elapsed = time.time() - self.last_heartbeat
                timeout = random.uniform(
                    float(os.getenv('ELECTION_TIMEOUT_MIN', '3.0')),
                    float(os.getenv('ELECTION_TIMEOUT_MAX', '5.0'))
                )
                
                if elapsed > timeout:
                    logger.info(f"Node {self.node_id} election timeout, starting election")
                    await self.start_election()
            
            await asyncio.sleep(0.5)
    
    async def start_election(self):
        """Start leader election"""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.last_heartbeat = time.time()
        
        logger.info(f"Node {self.node_id} starting election for term {self.current_term}")
        
        votes_received = 1  # Vote for self
        votes_needed = (len(self.cluster_nodes) + 1) // 2 + 1
        
        # Request votes from other nodes
        for node_id, node_info in self.cluster_nodes.items():
            if node_id != self.node_id:
                vote_granted = await self.request_vote(node_id, node_info)
                if vote_granted:
                    votes_received += 1
        
        # Check if won election
        if votes_received >= votes_needed:
            await self.become_leader()
        else:
            self.state = NodeState.FOLLOWER
            logger.info(f"Node {self.node_id} lost election")
    
    async def request_vote(self, node_id: str, node_info: dict) -> bool:
        """Request vote from another node"""
        try:
            # Simulate vote request
            # In real implementation, this would send RPC to other node
            logger.debug(f"Requesting vote from {node_id}")
            return True
        except Exception as e:
            logger.error(f"Error requesting vote from {node_id}: {e}")
            return False
    
    async def become_leader(self):
        """Become the cluster leader"""
        self.state = NodeState.LEADER
        self.leader_id = self.node_id
        logger.info(f"Node {self.node_id} became LEADER for term {self.current_term}")
    
    async def heartbeat_sender(self):
        """Send periodic heartbeats (only if leader)"""
        while self.running:
            if self.state == NodeState.LEADER:
                await self.send_heartbeats()
            await asyncio.sleep(self.heartbeat_interval)
    
    async def send_heartbeats(self):
        """Send heartbeat to all followers"""
        for node_id, node_info in self.cluster_nodes.items():
            if node_id != self.node_id:
                try:
                    await self.send_heartbeat(node_id, node_info)
                except Exception as e:
                    logger.error(f"Error sending heartbeat to {node_id}: {e}")
    
    async def send_heartbeat(self, node_id: str, node_info: dict):
        """Send heartbeat to a specific node"""
        # To be implemented
        pass
    
    def receive_heartbeat(self, leader_id: str, term: int):
        """Receive heartbeat from leader"""
        if term >= self.current_term:
            self.current_term = term
            self.state = NodeState.FOLLOWER
            self.leader_id = leader_id
            self.last_heartbeat = time.time()
            logger.debug(f"Node {self.node_id} received heartbeat from {leader_id}")
    
    def add_cluster_node(self, node_id: str, host: str, port: int):
        """Add a node to the cluster"""
        self.cluster_nodes[node_id] = {
            'host': host,
            'port': port,
            'alive': True
        }
        logger.info(f"Added node {node_id} to cluster")
    
    def get_state(self) -> dict:
        """Get current node state"""
        return {
            'node_id': self.node_id,
            'state': self.state.value,
            'term': self.current_term,
            'leader_id': self.leader_id,
            'cluster_size': len(self.cluster_nodes) + 1
        }
