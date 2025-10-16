# distributed-sync-system
Pengerjaan tugas 2 Individu berdasarkan panduan tugas yang telah ada di LMS mata kuliah Sistem Paralel dan Terdistribusi.

Nama: Hylmi Wahyudi
Kelas: Sistem Paralel dan Terdistribusi B
NIM : 11221023

# System Architecture

## Overview

Distributed Synchronization System adalah sistem yang mengimplementasikan berbagai mekanisme sinkronisasi dalam distributed computing menggunakan Raft consensus algorithm.

## High-Level Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                        Client Layer                            │
│  (Applications using distributed locks, queues, cache)         │
└────────────────────────┬──────────────────────────────────────┘
                         │
┌────────────────────────┴──────────────────────────────────────┐
│                      API Gateway                               │
│  (Request routing, load balancing, authentication)             │
└────────────────────────┬──────────────────────────────────────┘
                         │
┌────────────────────────┴──────────────────────────────────────┐
│                   Service Layer                                │
├────────────────┬─────────────────┬────────────────────────────┤
│ Lock Manager   │  Queue Manager  │   Cache Manager            │
│ - Raft Based   │  - Consistent   │   - MESI Protocol          │
│ - Deadlock     │    Hashing      │   - LRU/LFU Policy         │
│   Detection    │  - Persistence  │   - Invalidation           │
└────────────────┴─────────────────┴────────────────────────────┘
                         │
┌────────────────────────┴──────────────────────────────────────┐
│                  Consensus Layer                               │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              Raft Consensus Algorithm                │     │
│  │  - Leader Election                                   │     │
│  │  - Log Replication                                   │     │
│  │  - Safety Guarantees                                 │     │
│  └──────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────┐     │
│  │         PBFT (Optional Bonus)                        │     │
│  │  - Byzantine Fault Tolerance                         │     │
│  │  - 3f + 1 nodes for f failures                       │     │
│  └──────────────────────────────────────────────────────┘     │
└────────────────────────┬──────────────────────────────────────┘
                         │
┌────────────────────────┴──────────────────────────────────────┐
│               Communication Layer                              │
│  ┌──────────────────────────────────────────────────────┐     │
│  │           Message Passing System                     │     │
│  │  - Reliable delivery with retry                      │     │
│  │  - Acknowledgment mechanism                          │     │
│  │  - Message ordering                                  │     │
│  └──────────────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────────────┐     │
│  │        Failure Detection (Phi Accrual)               │     │
│  │  - Adaptive failure detection                        │     │
│  │  - Heartbeat monitoring                              │     │
│  │  - Network partition handling                        │     │
│  └──────────────────────────────────────────────────────┘     │
└────────────────────────┬──────────────────────────────────────┘
                         │
┌────────────────────────┴──────────────────────────────────────┐
│                  Storage Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │    Redis     │  │  Local State │  │  Persistent  │        │
│  │  (Shared)    │  │   (Memory)   │  │    Store     │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└───────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Base Node

**Purpose**: Foundation untuk semua node types

**Key Features**:
- Node state management (Follower, Candidate, Leader)
- Election timer and heartbeat mechanism
- Cluster membership tracking
- Basic RPC handling

**State Transitions**:
```
    ┌─────────┐
    │ FOLLOWER│◄────┐
    └────┬────┘     │
         │ timeout  │ receives heartbeat
         │          │ from leader
    ┌────▼────┐     │
    │CANDIDATE│     │
    └────┬────┘     │
         │ wins     │
         │ election │
    ┌────▼────┐     │
    │  LEADER │─────┘
    └─────────┘
```

### 2. Lock Manager Node

**Purpose**: Distributed mutual exclusion

**Algorithm**: Raft Consensus

**Lock Types**:
- **Shared Lock**: Multiple readers dapat acquire
- **Exclusive Lock**: Hanya satu writer dapat acquire

**Deadlock Detection**:
- Wait-for graph construction
- Cycle detection using DFS
- Automatic deadlock resolution

**State Management**:
```python
Lock State = {
    'lock_id': string,
    'lock_type': SHARED | EXCLUSIVE,
    'holders': set<node_id>,
    'waiting_queue': list<request>,
    'timeout': float
}
```

### 3. Queue Node

**Purpose**: Distributed message queue

**Key Features**:
- Consistent hashing untuk distribusi
- Message persistence
- At-least-once delivery
- Priority queue support

**Consistent Hashing**:
```
Hash Ring (0-2^32):
┌──────────────────────────────────────────┐
│  Node1   Node2   Node3   Node1   Node2   │
│  (v1)    (v1)    (v1)    (v2)    (v2)    │
└──────────────────────────────────────────┘
       │      │      │      │      │
     Virtual Nodes for load balancing
```

### 4. Cache Node

**Purpose**: Distributed cache dengan coherence

**Protocol**: MESI (Modified, Exclusive, Shared, Invalid)

**State Transitions**:
```
    ┌─────────┐ read miss ┌──────────┐
    │ INVALID │──────────►│ SHARED   │
    └────┬────┘            └─────┬────┘
         │                       │
         │ write                 │ write
         │                       │
    ┌────▼────┐            ┌─────▼────┐
    │EXCLUSIVE│───────────►│ MODIFIED │
    └─────────┘   modify   └──────────┘
```

**Replacement Policies**:
- **LRU** (Least Recently Used): Default
- **LFU** (Least Frequently Used): Optional

### 5. Raft Consensus

**Purpose**: Distributed consensus and replication

**Phases**:

1. **Leader Election**:
   - Random election timeout (3-5s)
   - Request votes from peers
   - Majority wins election

2. **Log Replication**:
   - Leader appends to local log
   - Replicate to followers
   - Commit when majority acknowledges

3. **Safety**:
   - Election Safety: At most one leader per term
   - Leader Append-Only: Leader never overwrites log
   - Log Matching: Logs are consistent across nodes
   - State Machine Safety: Applied entries are identical

**Log Structure**:
```
Index:  0    1    2    3    4
Term:  [1]  [1]  [2]  [2]  [3]
Cmd:   [x=1][y=2][x=3][z=4][y=5]
       └─committed─┘    └─uncommitted─┘
```

### 6. Communication Layer

**Message Passing**:
- Reliable delivery with retries
- Acknowledgment mechanism
- Message ordering guarantees
- Timeout handling

**Failure Detection**:
- Phi Accrual algorithm
- Adaptive thresholds
- Heartbeat-based monitoring
- Network partition detection

## Data Flow

### Lock Acquisition Flow

```
Client ─1─► Node1 (Follower)
              │
              2 (redirect)
              ▼
         Node2 (Leader)
              │
              3 (check deadlock)
              │
              4 (acquire if safe)
              │
         ┌────┴────┐
         5         5
         ▼         ▼
      Node1     Node3
    (replicate) (replicate)
         │         │
         6         6
         └────┬────┘
              ▼
         Acknowledge
              │
              7
              ▼
           Client
```

### Queue Enqueue Flow

```
Producer ─1─► Queue Node
                   │
                   2 (hash message_id)
                   │
                   3 (determine replicas)
                   │
              ┌────┴────┬────┐
              4         4    4
              ▼         ▼    ▼
           Node1    Node2  Node3
         (primary) (replica)(replica)
              │         │    │
              5         5    5
         (persist) (persist)(persist)
              │         │    │
              6         6    6
              └────┬────┴────┘
                   ▼
             Acknowledge
                   │
                   7
                   ▼
              Producer
```

### Cache Get Flow

```
Client ─1─► Cache Node1
              │
              2 (check local cache)
              │
         ┌────┴────┐
         │         │
       Hit?      Miss?
         │         │
         3a        3b (fetch from peer)
         │         │
         │    ┌────┴────┐
         │    4         4
         │    ▼         ▼
         │  Node2    Node3
         │    │         │
         │    5 (check cache)
         │    │         │
         │    6         6
         │    └────┬────┘
         │         │
         7a        7b (update local)
         │         │
         └────┬────┘
              ▼
           Client
```

## Failure Scenarios

### 1. Node Failure

**Detection**:
- Missing heartbeats
- Phi value exceeds threshold
- Mark as SUSPECTED → DEAD

**Recovery**:
- Automatic failover
- Leader re-election if leader fails
- Data replication ensures no data loss

### 2. Network Partition

**Scenario**: Cluster splits into two groups

**Handling**:
- Majority partition continues operating
- Minority partition cannot make progress
- Automatic reconciliation when partition heals

**Example**:
```
Before Partition:
[Node1(L)] ─ [Node2] ─ [Node3]

After Partition:
[Node1(L)] ─ [Node2]    |    [Node3]
     │                   |
  Majority              Split-brain
  (continues)           (read-only)
```

### 3. Leader Failure

**Detection**:
- Followers don't receive heartbeats
- Election timeout triggers

**Recovery**:
1. Followers become candidates
2. Request votes
3. New leader elected
4. Resume normal operation

## Performance Characteristics

### Lock Manager

- **Latency**: O(RTT × log N) for consensus
- **Throughput**: ~1000 locks/sec per node
- **Scalability**: Horizontal with read replicas

### Queue

- **Latency**: O(1) for local operations
- **Throughput**: ~5000 messages/sec
- **Scalability**: Linear with consistent hashing

### Cache

- **Hit Latency**: O(1) for local hits
- **Miss Latency**: O(RTT) for peer fetch
- **Hit Rate**: 80-95% typical
- **Scalability**: Near-linear up to 10 nodes

## Monitoring and Observability

### Metrics Exported

1. **System Metrics**:
   - CPU, Memory, Network usage
   - GC statistics

2. **Business Metrics**:
   - Lock acquisition rate
   - Queue throughput
   - Cache hit rate

3. **Raft Metrics**:
   - Election frequency
   - Log replication lag
   - Commit index

### Health Checks

- `/health`: Overall system health
- `/ready`: Readiness for traffic
- `/metrics`: Prometheus metrics

## Security Considerations

1. **Authentication**: Token-based auth
2. **Authorization**: RBAC for operations
3. **Encryption**: TLS for inter-node communication
4. **Audit Logging**: All operations logged

## Deployment Topology

### Small Deployment (3 nodes)

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│  Node1  │  │  Node2  │  │  Node3  │
│ (Leader)│──│(Follower)│──│(Follower)│
└─────────┘  └─────────┘  └─────────┘
     │            │            │
     └────────────┴────────────┘
              Redis
```

### Production Deployment (5+ nodes)

```
     Load Balancer
          │
    ┌─────┴─────┐
    │           │
┌───▼───┐   ┌───▼───┐
│ Node1 │   │ Node2 │
│(Leader)│   │(Foll.)│
└───┬───┘   └───┬───┘
    │           │
┌───▼───┬───────┴───────┬───────┐
│ Node3 │    Node4      │ Node5 │
│(Foll.)│   (Foll.)     │(Foll.)│
└───┬───┴───────┬───────┴───┬───┘
    │           │           │
    └───────────┴───────────┘
         Redis Cluster
```
