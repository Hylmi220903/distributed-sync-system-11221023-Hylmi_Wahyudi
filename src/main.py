"""
Main entry point untuk Distributed Sync System
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from src.utils.config import load_config, setup_logging
from src.utils.metrics import MetricsCollector
from src.nodes import LockManagerNode, QueueNode, CacheNode, NodeState
from src.communication import FailureDetector
from src.consensus import RaftNode

logger = logging.getLogger(__name__)


class DistributedSyncSystem:
    """
    Main system orchestrator
    """
    
    def __init__(self, config):
        self.config = config
        
        # Initialize metrics
        self.metrics = MetricsCollector(config.node_id)
        
        # Initialize nodes
        self.lock_manager = LockManagerNode(
            config.node_id,
            config.node_host,
            config.node_port
        )
        
        self.queue_node = QueueNode(
            config.node_id,
            config.node_host,
            config.node_port + 100
        )
        
        self.cache_node = CacheNode(
            config.node_id,
            config.node_host,
            config.node_port + 200,
            capacity=config.cache_size
        )
        
        # Initialize consensus
        cluster_node_ids = [node.split(':')[0] for node in config.cluster_nodes]
        self.raft = RaftNode(config.node_id, cluster_node_ids)
        
        # Initialize failure detector
        self.failure_detector = FailureDetector(
            config.node_id,
            config.heartbeat_interval
        )
        
        # Register cluster nodes
        for node_spec in config.cluster_nodes:
            parts = node_spec.split(':')
            if len(parts) == 2:
                node_id, port = parts[0], int(parts[1])
                if node_id != config.node_id:
                    self.failure_detector.register_node(node_id)
                    self.lock_manager.add_cluster_node(node_id, 'localhost', port)
        
        self.running = False
        
        logger.info(f"System initialized: {config.node_id}")
    
    async def start(self):
        """Start all system components"""
        logger.info("Starting Distributed Sync System...")
        self.running = True
        
        try:
            # Start all components concurrently
            await asyncio.gather(
                self.lock_manager.start(),
                self.queue_node.start(),
                self.cache_node.start(),
                self.failure_detector.start(),
                self.metrics_updater(),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"Error starting system: {e}", exc_info=True)
            await self.stop()
    
    async def stop(self):
        """Stop all system components"""
        logger.info("Stopping Distributed Sync System...")
        self.running = False
        
        # Stop all components
        await self.lock_manager.stop()
        await self.queue_node.stop()
        await self.cache_node.stop()
        self.failure_detector.stop()
        
        logger.info("System stopped")
    
    async def metrics_updater(self):
        """Periodically update metrics"""
        while self.running:
            try:
                # Update cluster metrics
                alive_nodes = len(self.failure_detector.get_alive_nodes())
                total_nodes = len(self.failure_detector.nodes)
                self.metrics.record_cluster(total_nodes, alive_nodes)
                
                # Update cache metrics
                cache_stats = self.cache_node.get_stats()
                self.metrics.gauge('cache_size').set(cache_stats['size'])
                
                # Update lock metrics
                active_locks = len([
                    lock for lock in self.lock_manager.locks.values()
                    if lock.is_locked()
                ])
                self.metrics.gauge('locks_active').set(active_locks)
                
                await asyncio.sleep(5.0)
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
    
    def get_status(self) -> dict:
        """Get system status"""
        return {
            'node_id': self.config.node_id,
            'lock_manager': self.lock_manager.get_state(),
            'cache': self.cache_node.get_stats(),
            'raft': self.raft.get_state(),
            'failure_detector': self.failure_detector.get_stats(),
            'metrics': self.metrics.get_summary()
        }


async def main():
    """Main function"""
    # Load configuration
    config = load_config()
    setup_logging(config)
    
    logger.info("=" * 60)
    logger.info("Distributed Synchronization System")
    logger.info("=" * 60)
    logger.info(f"Node ID: {config.node_id}")
    logger.info(f"Host: {config.node_host}:{config.node_port}")
    logger.info(f"Cluster: {config.cluster_nodes}")
    logger.info("=" * 60)
    
    # Create system
    system = DistributedSyncSystem(config)
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(system.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start system
        await system.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await system.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
