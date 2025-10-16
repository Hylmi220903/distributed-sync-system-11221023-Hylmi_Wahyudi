"""
Raft Consensus Algorithm Implementation
Implementasi lengkap algoritma Raft untuk distributed consensus
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Entry dalam Raft log"""
    term: int
    command: dict
    index: int
    
    def to_dict(self) -> dict:
        return {
            'term': self.term,
            'command': self.command,
            'index': self.index
        }


class RaftState(Enum):
    """Status node dalam Raft"""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


class RaftNode:
    """
    Implementasi Raft Consensus Algorithm
    
    Raft memastikan konsensus terdistribusi dengan:
    - Leader Election: Pemilihan leader otomatis
    - Log Replication: Replikasi log ke semua node
    - Safety: Konsistensi data dijamin
    """
    
    def __init__(self, node_id: str, cluster_nodes: List[str]):
        self.node_id = node_id
        self.cluster_nodes = cluster_nodes
        self.cluster_size = len(cluster_nodes)
        
        # Persistent state
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log: List[LogEntry] = []
        
        # Volatile state
        self.commit_index = 0
        self.last_applied = 0
        self.state = RaftState.FOLLOWER
        
        # Leader state (reinitialized after election)
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}
        
        # Timing
        self.last_heartbeat = time.time()
        self.election_timeout = 3.0
        self.heartbeat_interval = 1.0
        
        # Current leader
        self.leader_id: Optional[str] = None
        
        logger.info(f"RaftNode {node_id} initialized")
    
    def reset_election_timer(self):
        """Reset election timer"""
        import random
        self.last_heartbeat = time.time()
        self.election_timeout = random.uniform(3.0, 5.0)
    
    def is_election_timeout(self) -> bool:
        """Check if election timeout has occurred"""
        elapsed = time.time() - self.last_heartbeat
        return elapsed > self.election_timeout
    
    async def start_election(self) -> bool:
        """
        Start leader election
        
        Returns:
            True if won election, False otherwise
        """
        self.state = RaftState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.reset_election_timer()
        
        logger.info(f"Node {self.node_id} starting election for term {self.current_term}")
        
        votes_received = 1  # Vote for self
        votes_needed = (self.cluster_size // 2) + 1
        
        # Request votes from all other nodes
        vote_requests = []
        for node_id in self.cluster_nodes:
            if node_id != self.node_id:
                vote_requests.append(
                    self.request_vote_rpc(node_id)
                )
        
        # Gather votes
        if vote_requests:
            results = await asyncio.gather(*vote_requests, return_exceptions=True)
            for result in results:
                if isinstance(result, dict) and result.get('vote_granted'):
                    votes_received += 1
        
        # Check if won election
        if votes_received >= votes_needed:
            await self.become_leader()
            return True
        else:
            self.state = RaftState.FOLLOWER
            self.voted_for = None
            logger.info(f"Node {self.node_id} lost election (votes: {votes_received}/{votes_needed})")
            return False
    
    async def request_vote_rpc(self, target_node: str) -> dict:
        """
        Request vote from another node
        
        Args:
            target_node: Node ID to request vote from
            
        Returns:
            dict with vote result
        """
        last_log_index = len(self.log) - 1
        last_log_term = self.log[-1].term if self.log else 0
        
        request = {
            'type': 'RequestVote',
            'term': self.current_term,
            'candidate_id': self.node_id,
            'last_log_index': last_log_index,
            'last_log_term': last_log_term
        }
        
        # In real implementation, send RPC to target node
        # For now, simulate response
        logger.debug(f"Requesting vote from {target_node}")
        
        # Simulate response (would be actual RPC call)
        return {
            'term': self.current_term,
            'vote_granted': True
        }
    
    def handle_request_vote(self, request: dict) -> dict:
        """
        Handle RequestVote RPC
        
        Args:
            request: Vote request from candidate
            
        Returns:
            dict with vote response
        """
        term = request['term']
        candidate_id = request['candidate_id']
        last_log_index = request['last_log_index']
        last_log_term = request['last_log_term']
        
        # Update term if necessary
        if term > self.current_term:
            self.current_term = term
            self.state = RaftState.FOLLOWER
            self.voted_for = None
        
        vote_granted = False
        
        # Grant vote if:
        # 1. Haven't voted in this term OR already voted for this candidate
        # 2. Candidate's log is at least as up-to-date as ours
        if term >= self.current_term:
            if (self.voted_for is None or self.voted_for == candidate_id):
                # Check if candidate's log is up-to-date
                our_last_index = len(self.log) - 1
                our_last_term = self.log[-1].term if self.log else 0
                
                log_is_up_to_date = (
                    last_log_term > our_last_term or
                    (last_log_term == our_last_term and last_log_index >= our_last_index)
                )
                
                if log_is_up_to_date:
                    vote_granted = True
                    self.voted_for = candidate_id
                    self.reset_election_timer()
                    logger.info(f"Node {self.node_id} voted for {candidate_id} in term {term}")
        
        return {
            'term': self.current_term,
            'vote_granted': vote_granted
        }
    
    async def become_leader(self):
        """Become the cluster leader"""
        self.state = RaftState.LEADER
        self.leader_id = self.node_id
        
        # Initialize leader state
        for node_id in self.cluster_nodes:
            if node_id != self.node_id:
                self.next_index[node_id] = len(self.log)
                self.match_index[node_id] = 0
        
        logger.info(f"Node {self.node_id} became LEADER for term {self.current_term}")
        
        # Send initial heartbeat
        await self.send_heartbeats()
    
    async def send_heartbeats(self):
        """Send heartbeat (empty AppendEntries) to all followers"""
        if self.state != RaftState.LEADER:
            return
        
        heartbeat_tasks = []
        for node_id in self.cluster_nodes:
            if node_id != self.node_id:
                heartbeat_tasks.append(
                    self.send_append_entries_rpc(node_id, is_heartbeat=True)
                )
        
        if heartbeat_tasks:
            await asyncio.gather(*heartbeat_tasks, return_exceptions=True)
    
    async def send_append_entries_rpc(self, target_node: str, 
                                     is_heartbeat: bool = False) -> dict:
        """
        Send AppendEntries RPC to follower
        
        Args:
            target_node: Target node ID
            is_heartbeat: Whether this is a heartbeat (empty entries)
            
        Returns:
            dict with response
        """
        prev_log_index = self.next_index.get(target_node, len(self.log)) - 1
        prev_log_term = self.log[prev_log_index].term if prev_log_index >= 0 and self.log else 0
        
        entries = []
        if not is_heartbeat and len(self.log) > prev_log_index + 1:
            # Send new log entries
            entries = [
                entry.to_dict() 
                for entry in self.log[prev_log_index + 1:]
            ]
        
        request = {
            'type': 'AppendEntries',
            'term': self.current_term,
            'leader_id': self.node_id,
            'prev_log_index': prev_log_index,
            'prev_log_term': prev_log_term,
            'entries': entries,
            'leader_commit': self.commit_index
        }
        
        # In real implementation, send RPC to target node
        logger.debug(f"Sending AppendEntries to {target_node} (heartbeat={is_heartbeat})")
        
        # Simulate response
        return {
            'term': self.current_term,
            'success': True,
            'match_index': prev_log_index + len(entries)
        }
    
    def handle_append_entries(self, request: dict) -> dict:
        """
        Handle AppendEntries RPC
        
        Args:
            request: AppendEntries request from leader
            
        Returns:
            dict with response
        """
        term = request['term']
        leader_id = request['leader_id']
        prev_log_index = request['prev_log_index']
        prev_log_term = request['prev_log_term']
        entries = request['entries']
        leader_commit = request['leader_commit']
        
        # Update term if necessary
        if term > self.current_term:
            self.current_term = term
            self.state = RaftState.FOLLOWER
            self.voted_for = None
        
        # Reset election timer (received message from leader)
        if term >= self.current_term:
            self.reset_election_timer()
            self.leader_id = leader_id
            self.state = RaftState.FOLLOWER
        
        success = False
        
        # Check if term is current
        if term >= self.current_term:
            # Check if log matches at prev_log_index
            if prev_log_index < 0 or (
                prev_log_index < len(self.log) and
                self.log[prev_log_index].term == prev_log_term
            ):
                success = True
                
                # Append new entries
                if entries:
                    # Remove conflicting entries
                    insert_index = prev_log_index + 1
                    if insert_index < len(self.log):
                        self.log = self.log[:insert_index]
                    
                    # Append new entries
                    for entry_dict in entries:
                        entry = LogEntry(
                            term=entry_dict['term'],
                            command=entry_dict['command'],
                            index=entry_dict['index']
                        )
                        self.log.append(entry)
                
                # Update commit index
                if leader_commit > self.commit_index:
                    self.commit_index = min(leader_commit, len(self.log) - 1)
                    # Apply committed entries
                    asyncio.create_task(self.apply_committed_entries())
        
        return {
            'term': self.current_term,
            'success': success,
            'match_index': len(self.log) - 1 if success else -1
        }
    
    async def apply_committed_entries(self):
        """Apply committed log entries to state machine"""
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            entry = self.log[self.last_applied]
            
            # Apply command to state machine
            logger.info(f"Applying log entry {self.last_applied}: {entry.command}")
            
            # In real implementation, apply command to actual state machine
    
    async def replicate_command(self, command: dict) -> bool:
        """
        Replicate command to cluster (leader only)
        
        Args:
            command: Command to replicate
            
        Returns:
            True if successfully replicated to majority
        """
        if self.state != RaftState.LEADER:
            logger.warning(f"Node {self.node_id} is not leader, cannot replicate")
            return False
        
        # Append to local log
        entry = LogEntry(
            term=self.current_term,
            command=command,
            index=len(self.log)
        )
        self.log.append(entry)
        
        logger.info(f"Leader {self.node_id} appended command to log at index {entry.index}")
        
        # Replicate to followers
        replication_tasks = []
        for node_id in self.cluster_nodes:
            if node_id != self.node_id:
                replication_tasks.append(
                    self.send_append_entries_rpc(node_id, is_heartbeat=False)
                )
        
        # Wait for majority to acknowledge
        if replication_tasks:
            results = await asyncio.gather(*replication_tasks, return_exceptions=True)
            
            # Count successful replications
            successful = 1  # Count self
            for result in results:
                if isinstance(result, dict) and result.get('success'):
                    successful += 1
                    # Update match_index
                    node_id = self.cluster_nodes[results.index(result)]
                    if node_id in self.match_index:
                        self.match_index[node_id] = result.get('match_index', 0)
            
            # Check if majority replicated
            majority = (self.cluster_size // 2) + 1
            if successful >= majority:
                # Update commit index
                self.commit_index = entry.index
                logger.info(f"Command committed at index {entry.index}")
                
                # Apply to state machine
                await self.apply_committed_entries()
                
                return True
        
        return False
    
    def get_state(self) -> dict:
        """Get current Raft state"""
        return {
            'node_id': self.node_id,
            'state': self.state.value,
            'term': self.current_term,
            'leader_id': self.leader_id,
            'log_size': len(self.log),
            'commit_index': self.commit_index,
            'last_applied': self.last_applied
        }
