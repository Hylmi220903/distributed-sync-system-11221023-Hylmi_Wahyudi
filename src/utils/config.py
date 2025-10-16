"""
Configuration Management
Load and manage system configuration from environment variables
"""

import os
import logging
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """System configuration"""
    
    # Node configuration
    node_id: str
    node_host: str
    node_port: int
    
    # Cluster configuration
    cluster_nodes: List[str]
    heartbeat_interval: float
    election_timeout_min: float
    election_timeout_max: float
    
    # Redis configuration
    redis_host: str
    redis_port: int
    redis_db: int
    
    # Cache configuration
    cache_size: int
    cache_policy: str
    cache_protocol: str
    
    # Queue configuration
    queue_persistence: bool
    queue_replication_factor: int
    
    # Monitoring
    metrics_port: int
    enable_prometheus: bool
    
    # Logging
    log_level: str
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None):
        """
        Load configuration from environment variables
        
        Args:
            env_file: Path to .env file (optional)
            
        Returns:
            Config instance
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        # Parse cluster nodes
        cluster_nodes_str = os.getenv('CLUSTER_NODES', '')
        cluster_nodes = [
            node.strip() 
            for node in cluster_nodes_str.split(',')
            if node.strip()
        ]
        
        return cls(
            # Node configuration
            node_id=os.getenv('NODE_ID', 'node1'),
            node_host=os.getenv('NODE_HOST', 'localhost'),
            node_port=int(os.getenv('NODE_PORT', '8001')),
            
            # Cluster configuration
            cluster_nodes=cluster_nodes,
            heartbeat_interval=float(os.getenv('HEARTBEAT_INTERVAL', '1.0')),
            election_timeout_min=float(os.getenv('ELECTION_TIMEOUT_MIN', '3.0')),
            election_timeout_max=float(os.getenv('ELECTION_TIMEOUT_MAX', '5.0')),
            
            # Redis configuration
            redis_host=os.getenv('REDIS_HOST', 'localhost'),
            redis_port=int(os.getenv('REDIS_PORT', '6379')),
            redis_db=int(os.getenv('REDIS_DB', '0')),
            
            # Cache configuration
            cache_size=int(os.getenv('CACHE_SIZE', '1000')),
            cache_policy=os.getenv('CACHE_POLICY', 'LRU'),
            cache_protocol=os.getenv('CACHE_PROTOCOL', 'MESI'),
            
            # Queue configuration
            queue_persistence=os.getenv('QUEUE_PERSISTENCE', 'true').lower() == 'true',
            queue_replication_factor=int(os.getenv('QUEUE_REPLICATION_FACTOR', '2')),
            
            # Monitoring
            metrics_port=int(os.getenv('METRICS_PORT', '9090')),
            enable_prometheus=os.getenv('ENABLE_PROMETHEUS', 'true').lower() == 'true',
            
            # Logging
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            'node': {
                'id': self.node_id,
                'host': self.node_host,
                'port': self.node_port
            },
            'cluster': {
                'nodes': self.cluster_nodes,
                'heartbeat_interval': self.heartbeat_interval,
                'election_timeout': {
                    'min': self.election_timeout_min,
                    'max': self.election_timeout_max
                }
            },
            'redis': {
                'host': self.redis_host,
                'port': self.redis_port,
                'db': self.redis_db
            },
            'cache': {
                'size': self.cache_size,
                'policy': self.cache_policy,
                'protocol': self.cache_protocol
            },
            'queue': {
                'persistence': self.queue_persistence,
                'replication_factor': self.queue_replication_factor
            },
            'monitoring': {
                'metrics_port': self.metrics_port,
                'enable_prometheus': self.enable_prometheus
            },
            'logging': {
                'level': self.log_level
            }
        }


def load_config(env_file: Optional[str] = None) -> Config:
    """
    Load configuration from environment
    
    Args:
        env_file: Path to .env file (optional)
        
    Returns:
        Config instance
    """
    config = Config.from_env(env_file)
    logger.info(f"Configuration loaded for node {config.node_id}")
    return config


def setup_logging(config: Config):
    """
    Setup logging configuration
    
    Args:
        config: System configuration
    """
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger.info(f"Logging configured with level {config.log_level}")
