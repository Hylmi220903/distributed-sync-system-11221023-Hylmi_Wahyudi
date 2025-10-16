"""
Metrics Collection for Performance Monitoring
Collect dan expose metrics untuk Prometheus
"""

import logging
import time
from typing import Dict, List, Optional
from enum import Enum
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Tipe metrik yang didukung"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class Metric:
    """Base metric class"""
    
    def __init__(self, name: str, description: str, metric_type: MetricType):
        self.name = name
        self.description = description
        self.metric_type = metric_type
        self.labels: Dict[str, str] = {}
        self.created_at = datetime.now()


class Counter(Metric):
    """Counter metric - monotonically increasing value"""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description, MetricType.COUNTER)
        self.value = 0
    
    def inc(self, amount: float = 1.0):
        """Increment counter"""
        self.value += amount
    
    def get(self) -> float:
        """Get current value"""
        return self.value


class Gauge(Metric):
    """Gauge metric - value that can go up and down"""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description, MetricType.GAUGE)
        self.value = 0.0
    
    def set(self, value: float):
        """Set gauge value"""
        self.value = value
    
    def inc(self, amount: float = 1.0):
        """Increment gauge"""
        self.value += amount
    
    def dec(self, amount: float = 1.0):
        """Decrement gauge"""
        self.value -= amount
    
    def get(self) -> float:
        """Get current value"""
        return self.value


class Histogram(Metric):
    """Histogram metric - distribution of values"""
    
    def __init__(self, name: str, description: str, buckets: Optional[List[float]] = None):
        super().__init__(name, description, MetricType.HISTOGRAM)
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        self.observations: List[float] = []
        self.sum = 0.0
        self.count = 0
    
    def observe(self, value: float):
        """Observe a value"""
        self.observations.append(value)
        self.sum += value
        self.count += 1
    
    def get_buckets(self) -> Dict[float, int]:
        """Get bucket counts"""
        bucket_counts = {}
        for bucket in self.buckets:
            bucket_counts[bucket] = sum(1 for v in self.observations if v <= bucket)
        return bucket_counts
    
    def get_stats(self) -> dict:
        """Get histogram statistics"""
        if not self.observations:
            return {
                'count': 0,
                'sum': 0,
                'avg': 0,
                'min': 0,
                'max': 0
            }
        
        return {
            'count': self.count,
            'sum': self.sum,
            'avg': self.sum / self.count,
            'min': min(self.observations),
            'max': max(self.observations)
        }


class MetricsCollector:
    """
    Central metrics collector
    Collect dan expose metrics untuk monitoring
    """
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        
        # Metric storage
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
        
        # Initialize standard metrics
        self._init_standard_metrics()
        
        logger.info(f"MetricsCollector initialized for node {node_id}")
    
    def _init_standard_metrics(self):
        """Initialize standard system metrics"""
        # Request metrics
        self.counter('requests_total', 'Total number of requests')
        self.counter('requests_failed', 'Total number of failed requests')
        
        # Lock metrics
        self.gauge('locks_active', 'Number of active locks')
        self.counter('locks_acquired', 'Total locks acquired')
        self.counter('locks_released', 'Total locks released')
        self.counter('deadlocks_detected', 'Total deadlocks detected')
        
        # Queue metrics
        self.gauge('queue_size', 'Current queue size')
        self.counter('messages_enqueued', 'Total messages enqueued')
        self.counter('messages_dequeued', 'Total messages dequeued')
        self.counter('messages_failed', 'Total failed messages')
        
        # Cache metrics
        self.gauge('cache_size', 'Current cache size')
        self.counter('cache_hits', 'Total cache hits')
        self.counter('cache_misses', 'Total cache misses')
        self.counter('cache_invalidations', 'Total cache invalidations')
        
        # Node metrics
        self.gauge('cluster_size', 'Number of nodes in cluster')
        self.gauge('alive_nodes', 'Number of alive nodes')
        
        # Latency metrics
        self.histogram('request_duration', 'Request duration in seconds')
        self.histogram('lock_wait_time', 'Lock wait time in seconds')
        self.histogram('queue_wait_time', 'Queue message wait time in seconds')
    
    def counter(self, name: str, description: str = '') -> Counter:
        """Get or create counter"""
        if name not in self.counters:
            self.counters[name] = Counter(name, description)
        return self.counters[name]
    
    def gauge(self, name: str, description: str = '') -> Gauge:
        """Get or create gauge"""
        if name not in self.gauges:
            self.gauges[name] = Gauge(name, description)
        return self.gauges[name]
    
    def histogram(self, name: str, description: str = '', 
                  buckets: Optional[List[float]] = None) -> Histogram:
        """Get or create histogram"""
        if name not in self.histograms:
            self.histograms[name] = Histogram(name, description, buckets)
        return self.histograms[name]
    
    def record_request(self, duration: float, success: bool = True):
        """Record request metrics"""
        self.counter('requests_total').inc()
        if not success:
            self.counter('requests_failed').inc()
        self.histogram('request_duration').observe(duration)
    
    def record_lock(self, action: str, wait_time: Optional[float] = None):
        """Record lock metrics"""
        if action == 'acquired':
            self.counter('locks_acquired').inc()
            self.gauge('locks_active').inc()
            if wait_time is not None:
                self.histogram('lock_wait_time').observe(wait_time)
        elif action == 'released':
            self.counter('locks_released').inc()
            self.gauge('locks_active').dec()
        elif action == 'deadlock':
            self.counter('deadlocks_detected').inc()
    
    def record_queue(self, action: str, size: Optional[int] = None, 
                    wait_time: Optional[float] = None):
        """Record queue metrics"""
        if action == 'enqueue':
            self.counter('messages_enqueued').inc()
            if size is not None:
                self.gauge('queue_size').set(size)
        elif action == 'dequeue':
            self.counter('messages_dequeued').inc()
            if size is not None:
                self.gauge('queue_size').set(size)
            if wait_time is not None:
                self.histogram('queue_wait_time').observe(wait_time)
        elif action == 'failed':
            self.counter('messages_failed').inc()
    
    def record_cache(self, action: str, size: Optional[int] = None):
        """Record cache metrics"""
        if action == 'hit':
            self.counter('cache_hits').inc()
        elif action == 'miss':
            self.counter('cache_misses').inc()
        elif action == 'invalidation':
            self.counter('cache_invalidations').inc()
        
        if size is not None:
            self.gauge('cache_size').set(size)
    
    def record_cluster(self, total: int, alive: int):
        """Record cluster metrics"""
        self.gauge('cluster_size').set(total)
        self.gauge('alive_nodes').set(alive)
    
    def get_all_metrics(self) -> dict:
        """Get all collected metrics"""
        metrics = {
            'node_id': self.node_id,
            'counters': {},
            'gauges': {},
            'histograms': {}
        }
        
        # Collect counters
        for name, counter in self.counters.items():
            metrics['counters'][name] = {
                'value': counter.get(),
                'description': counter.description
            }
        
        # Collect gauges
        for name, gauge in self.gauges.items():
            metrics['gauges'][name] = {
                'value': gauge.get(),
                'description': gauge.description
            }
        
        # Collect histograms
        for name, histogram in self.histograms.items():
            metrics['histograms'][name] = {
                'stats': histogram.get_stats(),
                'description': histogram.description
            }
        
        return metrics
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format
        
        Returns:
            Metrics in Prometheus text format
        """
        lines = []
        
        # Export counters
        for name, counter in self.counters.items():
            lines.append(f"# HELP {name} {counter.description}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f'{name}{{node="{self.node_id}"}} {counter.get()}')
        
        # Export gauges
        for name, gauge in self.gauges.items():
            lines.append(f"# HELP {name} {gauge.description}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f'{name}{{node="{self.node_id}"}} {gauge.get()}')
        
        # Export histograms
        for name, histogram in self.histograms.items():
            lines.append(f"# HELP {name} {histogram.description}")
            lines.append(f"# TYPE {name} histogram")
            
            stats = histogram.get_stats()
            lines.append(f'{name}_count{{node="{self.node_id}"}} {stats["count"]}')
            lines.append(f'{name}_sum{{node="{self.node_id}"}} {stats["sum"]}')
            
            buckets = histogram.get_buckets()
            for bucket, count in buckets.items():
                lines.append(f'{name}_bucket{{node="{self.node_id}",le="{bucket}"}} {count}')
        
        return '\n'.join(lines)
    
    def get_summary(self) -> dict:
        """Get summary of key metrics"""
        cache_hits = self.counter('cache_hits').get()
        cache_misses = self.counter('cache_misses').get()
        total_cache_requests = cache_hits + cache_misses
        hit_rate = (cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0
        
        requests_total = self.counter('requests_total').get()
        requests_failed = self.counter('requests_failed').get()
        success_rate = ((requests_total - requests_failed) / requests_total * 100) if requests_total > 0 else 0
        
        return {
            'node_id': self.node_id,
            'requests': {
                'total': requests_total,
                'failed': requests_failed,
                'success_rate': f"{success_rate:.2f}%"
            },
            'locks': {
                'active': self.gauge('locks_active').get(),
                'acquired': self.counter('locks_acquired').get(),
                'released': self.counter('locks_released').get(),
                'deadlocks': self.counter('deadlocks_detected').get()
            },
            'queue': {
                'size': self.gauge('queue_size').get(),
                'enqueued': self.counter('messages_enqueued').get(),
                'dequeued': self.counter('messages_dequeued').get(),
                'failed': self.counter('messages_failed').get()
            },
            'cache': {
                'size': self.gauge('cache_size').get(),
                'hits': cache_hits,
                'misses': cache_misses,
                'hit_rate': f"{hit_rate:.2f}%",
                'invalidations': self.counter('cache_invalidations').get()
            },
            'cluster': {
                'total_nodes': self.gauge('cluster_size').get(),
                'alive_nodes': self.gauge('alive_nodes').get()
            }
        }
