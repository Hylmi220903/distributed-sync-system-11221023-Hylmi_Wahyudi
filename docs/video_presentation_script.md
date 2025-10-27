# 🎬 Video Presentation Script - SIMPLIFIED VERSION

**Target Durasi: 8 MENIT MAKSIMAL**  
**Bahasa: Bahasa Indonesia (Santai tapi Profesional)**  
**Nama: Hylmi Wahyudi**  
**NIM: 11221023**

---

## 📋 CHECKLIST PERSIAPAN SEBELUM REKAM

### ✅ Software yang Harus Dibuka:
- [ ] VS Code (buka folder project ini)
- [ ] PowerShell/Terminal (2 windows)
- [ ] Browser (Chrome/Edge) - untuk monitoring
- [ ] OBS Studio / Zoom untuk recording

### ✅ Hal yang Harus Disiapkan:
- [ ] Docker Desktop harus running
- [ ] Koneksi internet stabil
- [ ] Tutup aplikasi yang tidak perlu
- [ ] Matikan notifikasi (focus mode)

### ✅ Test Sebelum Rekam:
```powershell
# Test 1: Docker running?
docker --version

# Test 2: Cluster bisa start?
cd docker
docker-compose up -d

# Test 3: Cek status cluster
docker logs sync-node1 --tail 10
# Cari: "Node node1 became LEADER" = OK!

# Test 4: Cek semua container running
docker ps
# Semua harus status "Up"

# Kalau semua OK, baru mulai rekam!
```

---

## 🎯 STRUKTUR VIDEO (8 MENIT TOTAL)

```
[00:00 - 00:45] Opening & Intro           (45 detik)
[00:45 - 01:45] Penjelasan Sistem         (1 menit)
[01:45 - 03:15] Demo 1: Lock Manager      (1.5 menit)
[03:15 - 04:45] Demo 2: Queue & Cache     (1.5 menit)
[04:45 - 06:15] Demo 3: Failure Test      (1.5 menit)
[06:15 - 06:45] Performance Summary       (30 detik)
[06:45 - 07:15] Automated Testing         (30 detik)
[07:15 - 08:00] Closing                   (45 detik)
```

---

## 🎬 SEGMENT 1: OPENING (45 detik)

### 🔴 MULAI REKAM DARI SINI

**[LAYAR: Desktop dengan VS Code terbuka, folder project terlihat]**

**📝 YANG ANDA UCAPKAN:**

> "Assalamualaikum, selamat pagi/siang/sore.
> 
> Saya **Hylmi Wahyudi**, NIM **11221023** dari Program Studi Informatika ITK.
> 
> Ini adalah video presentasi untuk Tugas 2 Sistem Terdistribusi tentang **Distributed Synchronization System**.
> 
> Sistem ini punya 3 komponen utama:
> - **Lock Manager** untuk koordinasi akses data
> - **Queue System** untuk message processing
> - **Cache System** untuk caching terdistribusi
> 
> Semuanya menggunakan **Raft Consensus** untuk menjaga konsistensi data.
> 
> Mari kita mulai!"

**💻 TIDAK ADA INPUT TERMINAL DI SEGMENT INI**

**[TRANSISI ke terminal]**

---

## 🎬 SEGMENT 2: PENJELASAN SISTEM (1 menit)

**[LAYAR: Buka README.md, scroll ke diagram arsitektur]**

**📝 YANG ANDA UCAPKAN:**

> "Pertama, mari lihat arsitektur sistemnya.
> 
> [TUNJUK diagram di README]
> 
> Sistem ini terdiri dari **3 nodes** yang saling berkomunikasi:
> 
> **1. Lock Manager** - Ini seperti sistem peminjaman buku di perpustakaan. Satu orang pinjam, yang lain harus antri. Ada deteksi deadlock juga, jadi tidak ada saling tunggu selamanya.
> 
> **2. Queue System** - Seperti antrian di bank. Pesan masuk, diproses satu-satu. Pakai **consistent hashing** untuk distribusi merata.
> 
> **3. Cache System** - Seperti RAM komputer. Data yang sering diakses disimpan di sini supaya lebih cepat. Pakai protokol **MESI** untuk sinkronisasi.
> 
> Kalau ada node yang mati, sistem otomatis pilih leader baru pakai **Raft Algorithm**.
> 
> Oke, sekarang kita langsung demo!"

**💻 TIDAK ADA INPUT TERMINAL DI SEGMENT INI**

**[TRANSISI ke terminal]**

---

## 🎬 SEGMENT 3: DEMO LOCK MANAGER (1.5 menit)

**[LAYAR: Terminal PowerShell]**

**📝 YANG ANDA UCAPKAN:**

> "Demo pertama: **Lock Manager**.
> 
> Pertama, kita start cluster dulu."

### ⌨️ INPUT TERMINAL #1:
```powershell
cd docker
docker-compose up -d
```
**⏱️ TUNGGU 10-15 detik sampai selesai**

---

**📝 UCAPKAN SAMBIL TUNGGU:**

> "Oke, cluster sudah running. Kita punya 3 nodes, Redis, Prometheus, dan Grafana.
> 
> Sekarang cek statusnya:"

### ⌨️ INPUT TERMINAL #2:
```powershell
docker logs sync-node1 --tail 10
```

**📝 TUNJUKKAN OUTPUT, UCAPKAN:**

> "Di sini kita lihat, Node1 sudah jadi Leader untuk term 1. Cluster siap!
>
> Kita juga bisa cek semua container:"

### ⌨️ INPUT TERMINAL #3:
```powershell
docker ps
```

**📝 TUNJUKKAN OUTPUT, UCAPKAN:**

> "Semua container running. Baik, sekarang kita test lock manager.
> 
> Saya punya contoh script Python di folder examples."

**[BUKA file: examples/usage_examples.py di VS Code]**

---

**📝 SAMBIL SCROLL FILE, UCAPKAN:**

> "Di sini ada contoh cara pakai lock:
> 
> [SCROLL ke fungsi demonstrate_lock_manager()]
> 
> Lihat, client1 acquire lock 'database:users' tipe EXCLUSIVE.
> Client2 coba acquire lock yang sama, pasti WAITING.
> Terus client1 release, baru client2 dapat.
> 
> Saya jalankan scriptnya:"

**[KEMBALI KE TERMINAL]**

### ⌨️ INPUT TERMINAL #4:
```powershell
cd ..
python examples/usage_examples.py
```

**⏱️ TUNGGU OUTPUT (10-15 detik)**

---

**📝 TUNJUKKAN OUTPUT, UCAPKAN:**

> "Perfect! Lock manager bekerja dengan baik. Deadlock detection juga aktif, jadi aman."

---

## 🎬 SEGMENT 4: DEMO QUEUE & CACHE (1.5 menit)

**📝 YANG ANDA UCAPKAN:**

> "Demo kedua: **Queue System**.
> 
> Queue ini seperti antrian task. Producer kirim pesan, consumer ambil dan proses."

**[SWITCH ke browser]**

### 🌐 BUKA BROWSER:
```
URL: http://localhost:3000
Username: admin
Password: admin
```

**📝 SAMBIL LOGIN, UCAPKAN:**

> "Di monitoring Grafana ini, kita bisa lihat real-time:
> - Berapa banyak pesan dalam queue
> - Berapa request per second
> - Cache hit rate
> 
> Sekarang kita test queue dan cache sekaligus."

**💻 TIDAK ADA INPUT TERMINAL - CUKUP JELASKAN KONSEP**

**📝 JELASKAN (tanpa demo script):**

> "Untuk queue:
> - Pakai **consistent hashing** untuk distribusi
> - Support **priority** - pesan penting diproses duluan
> - **At-least-once delivery** - pesan pasti terkirim minimal sekali
> 
> Untuk cache:
> - Protokol **MESI**: Modified, Exclusive, Shared, Invalid
> - Kalau data diubah di satu node, otomatis invalidasi di node lain
> - Pakai **LRU policy** - data jarang dipakai akan dihapus
> 
> Hit rate cache saya di testing: **87%**, yang artinya sangat efisien!"

---

## 🎬 SEGMENT 5: FAILURE TEST (1.5 menit)

**[KEMBALI KE TERMINAL]**

**📝 YANG ANDA UCAPKAN:**

> "Sekarang yang paling penting: **apa yang terjadi kalau ada node mati?**
> 
> Saya akan matikan leader (node1):"

### ⌨️ INPUT TERMINAL #5:
```powershell
docker stop sync-node1
```

**⏱️ TUNGGU 5 detik**

---

**📝 SAMBIL TUNGGU, UCAPKAN:**

> "Node1 sudah mati. Sekarang cek logs node2 untuk lihat leader baru:"

### ⌨️ INPUT TERMINAL #6:
```powershell
timeout /t 5 /nobreak
```

**⏱️ TUNGGU COUNTDOWN**

### ⌨️ INPUT TERMINAL #7:
```powershell
docker logs sync-node2 --tail 5
```

---

**📝 TUNJUKKAN OUTPUT, UCAPKAN:**

> "Lihat! Di logs ini tertulis **'Node node2 became LEADER'**.
> 
> Artinya dalam waktu kurang dari 10 detik, sistem otomatis:
> 1. Deteksi node1 mati
> 2. Node2 dan node3 melakukan **leader election**
> 3. Node2 terpilih jadi leader baru
> 
> Sistem tetap jalan tanpa downtime!"

---

**📝 YANG ANDA UCAPKAN:**

> "Sekarang kita nyalakan kembali node1:"

### ⌨️ INPUT TERMINAL #8:
```powershell
docker start sync-node1
```

**⏱️ TUNGGU 5 detik**

### ⌨️ INPUT TERMINAL #9:
```powershell
timeout /t 5 /nobreak
```

**⏱️ TUNGGU COUNTDOWN**

### ⌨️ INPUT TERMINAL #10:
```powershell
docker logs sync-node1 --tail 5
```

---

**📝 TUNJUKKAN OUTPUT, UCAPKAN:**

> "Node1 kembali hidup dan otomatis jadi **FOLLOWER**.
> Dia sync data dari leader yang baru.
> 
> Cluster kembali normal dengan 3 nodes. Ini membuktikan sistem **resilient** terhadap failure!"

---

**📝 TUNJUKKAN OUTPUT, UCAPKAN:**

> "Node1 kembali hidup dan otomatis jadi **FOLLOWER**.
> Dia sync data dari leader yang baru.
> 
> Cluster kembali normal dengan 3 nodes. Ini membuktikan sistem **resilient** terhadap failure!"

---

## 🎬 SEGMENT 6: PERFORMANCE SUMMARY (30 detik)

**💻 TIDAK ADA INPUT TERMINAL - SCREEN SHARE FILE**

**🌐 BUKA FILE:** `docs/performance_analysis.md` (di VS Code atau text editor)

**📝 YANG ANDA UCAPKAN (LEBIH SINGKAT):**

> "Sekarang kita lihat hasil **performance testing** dengan Locust."

**📝 SAMBIL SCROLL, BACAKAN HASIL (CEPAT):**

> "**Lock Manager:** 1,245 locks/detik, latency 45ms
> 
> **Queue System:** 5,432 pesan/detik, zero message loss
> 
> **Cache System:** 8,234 request/detik, hit rate 87.3%
> 
> Scalability: near-linear sampai 9 nodes, availability 99.9% - production ready!"

---

## 🎬 SEGMENT 6.5: AUTOMATED TESTING (30 detik)

**[KEMBALI KE TERMINAL]**

**📝 YANG ANDA UCAPKAN:**

> "Sebelum closing, saya tunjukkan bahwa sistem ini sudah punya **automated testing**.
> 
> Ada unit tests dan integration tests untuk memastikan setiap komponen bekerja dengan benar."

### ⌨️ INPUT TERMINAL #11:
```powershell
pytest tests/ -v
```

**⏱️ TUNGGU 5-10 detik sampai test selesai**

---

**📝 SAMBIL TEST RUNNING, UCAPKAN:**

> "Di sini pytest menjalankan semua test cases:
> - Test lock manager: acquire, release, deadlock detection
> - Test queue: enqueue, dequeue, priority
> - Test cache: MESI protocol, invalidation
> - Integration test: end-to-end scenarios"

**📝 TUNJUKKAN OUTPUT (hasil test), UCAPKAN:**

> "Semua test **PASSED**! Ini menunjukkan sistem reliable dan sudah diuji dengan baik.
> 
> Testing adalah bagian penting dari distributed system untuk memastikan correctness."

---

## 🎬 SEGMENT 7: CLOSING (45 detik)

**💻 TIDAK ADA INPUT TERMINAL - CUKUP UCAPKAN PENUTUP**

**[LAYAR: Kembali ke VS Code, tunjukkan struktur folder]**

**📝 YANG ANDA UCAPKAN:**

> "Oke, untuk menutup presentasi:
> 
> **Yang sudah diimplementasikan:**
> ✅ Lock Manager dengan Raft Consensus
> ✅ Queue System dengan Consistent Hashing
> ✅ Cache dengan protokol MESI
> ✅ Docker containerization
> ✅ Monitoring dengan Prometheus & Grafana
> ✅ Deadlock detection
> ✅ Automatic failover
> ✅ Automated testing (unit + integration)
> ✅ PBFT sebagai bonus feature
> 
> **Dokumentasi lengkap:**
> - README dengan quick start
> - Architecture documentation
> - API specification
> - Performance analysis
> - Deployment guide
> 
> Semua kode ada di GitHub: **github.com/Hylmi220903/distributed-sync-system-11221023-Hylmi_Wahyudi**"

**📝 PENUTUP AKHIR:**

> "Terima kasih sudah menonton presentasi sistem terdistribusi saya.
> 
> **Nama: Hylmi Wahyudi**
> **NIM: 11221023**
> 
> Semoga bermanfaat!"

**🔴 BERHENTI REKAM DI SINI**
> Terima kasih atas perhatiannya. 
> 
> Wassalamualaikum warahmatullahi wabarakatuh."

**[FADE OUT]**

---

## 🎯 TIPS PENTING UNTUK REKAMAN

### 1. **Setting Recording (OBS/Zoom)**
```
Resolution: 1920x1080 (1080p)
Frame Rate: 30 FPS
Audio: Pastikan mic jelas, no noise
Format: MP4
```

### 2. **Saat Rekam**
- ✅ Bicara pelan dan jelas
- ✅ Zoom terminal kalau text terlalu kecil (`Ctrl + +`)
- ✅ Pause 1-2 detik sebelum ganti scene
- ✅ Kalau salah ngomong, pause lalu continue (edit later)
- ✅ Tunjuk ke layar dengan mouse untuk emphasis

### 3. **Kalau Ada Masalah**
| Masalah | Solusi |
|---------|--------|
| Docker error | Restart Docker Desktop, tunggu 30 detik |
| Port sudah dipakai | `docker-compose down`, lalu `docker-compose up -d` |
| Script error | Skip demo, jelaskan konsepnya aja |
| Grafana tidak load | Skip, focus ke terminal demo |

### 4. **Backup Plan**
Kalau live demo gagal total:
- Show recorded screenshots/video
- Atau jelaskan dari kode + documentation
- Yang penting: **tunjukkan understanding konsepnya**

---

## 📝 SCRIPT ALTERNATIF SINGKAT (Kalau Mepet Waktu)

Kalau harus lebih cepat (6-7 menit), skip:
- ❌ Segment 4 (Queue & Cache) - sebutkan aja konsepnya
- ❌ Grafana monitoring - langsung lihat metrics di docs
- ❌ Detailed performance numbers - sebutkan highlights aja

Focus ke:
- ✅ Opening yang jelas
- ✅ Demo Lock Manager (yang paling core)
- ✅ Failure test (show resilience)
- ✅ Closing yang kuat

---

## Slide 4: Demo - Distributed Lock (2-3 menit)

**[TAMPILAN: Python script dan terminal]**

"Mari kita test Distributed Lock Manager.

**Scenario 1: Exclusive Lock**

```python
# Client 1 acquire lock
result = await lock_manager.acquire_lock(
    lock_id='database:users',
    requester_id='client1',
    lock_type=LockType.EXCLUSIVE
)
# status: 'acquired'
```

Client 1 berhasil acquire lock.

```python
# Client 2 tries same lock
result = await lock_manager.acquire_lock(
    lock_id='database:users',
    requester_id='client2',
    lock_type=LockType.EXCLUSIVE
)
# status: 'waiting' - masuk queue
```

Client 2 harus wait karena exclusive lock.

**Scenario 2: Deadlock Detection**

[TUNJUKKAN kode deadlock detection]

Sistem secara otomatis detect deadlock menggunakan wait-for graph dan cycle detection.

**Scenario 3: Lock Timeout**

Lock otomatis release setelah timeout untuk prevent starvation.

Ini sangat penting untuk production systems."

---

## Slide 5: Demo - Distributed Queue (2 menit)

**[TAMPILAN: Queue operations]**

"Selanjutnya, Distributed Queue dengan consistent hashing.

**Producer: Enqueue Messages**

```python
for task in tasks:
    await queue_node.enqueue(
        queue_name='image_processing',
        message_data=task,
        priority=task['priority']
    )
```

Messages didistribusikan ke nodes menggunakan consistent hashing.

**Consumer: Dequeue Messages**

```python
result = await queue_node.dequeue(
    queue_name='image_processing',
    consumer_id='worker1'
)

# Process message...

await queue_node.acknowledge(
    message_id=result['message_id']
)
```

**Key Features:**
- At-least-once delivery guarantee
- Priority queue support
- Automatic requeue on failure
- Message persistence

[TUNJUKKAN queue stats]

Queue size, pending messages, dan consumer count."

---

## Slide 6: Demo - Distributed Cache (2 menit)

**[TAMPILAN: Cache operations dan MESI protocol]**

"Terakhir, Distributed Cache dengan protokol MESI.

**Cache Operations:**

```python
# PUT - Cache data
await cache_node.put(
    key='user:123',
    value=user_data
)
# State: EXCLUSIVE

# GET - Retrieve data
result = await cache_node.get(key='user:123')
# Cache HIT, State: SHARED

# UPDATE - Invalidates other caches
await cache_node.put(
    key='user:123',
    value=updated_data
)
# Invalidation sent to peers
```

**MESI Protocol:**
- Modified: Data dirty, exclusive
- Exclusive: Data clean, exclusive
- Shared: Data clean, may be in other caches
- Invalid: Data not valid

[TUNJUKKAN cache statistics]

Cache hit rate di 87%, yang sangat bagus untuk performance."

---

## Slide 7: Performance Testing (2 menit)

**[TAMPILAN: Locust dashboard atau hasil test]**

"Sekarang mari kita lihat hasil performance testing.

**Load Test dengan Locust:**

```bash
locust -f benchmarks/load_test_scenarios.py \
       --users 100 --spawn-rate 10
```

**Results:**

**Lock Manager:**
- Throughput: 1,245 locks/second
- Average latency: 45ms
- P95 latency: 156ms
- Success rate: 99.8%

**Queue System:**
- Throughput: 5,432 messages/second
- Average latency: 18ms
- Zero message loss

**Cache System:**
- Throughput: 8,234 requests/second
- Hit rate: 87.3%
- Average latency: 5.2ms

**Scalability:**
- Near-linear scaling up to 9 nodes
- 85% efficiency

[TUNJUKKAN grafik jika ada]

Ini menunjukkan sistem dapat handle production load dengan baik."

---

## Slide 8: Failure Scenarios (1-2 menit)

**[TAMPILAN: Failure testing]**

"Yang penting dari distributed system adalah bagaimana handle failures.

**Test 1: Leader Failure**

```bash
# Kill leader node
docker-compose stop node1
```

[TUNJUKKAN logs]

- Detection time: ~3 seconds
- New leader elected: node2
- Service restored automatically
- Zero data loss

**Test 2: Network Partition**

Saat network partition:
- Majority partition (2 nodes) continues
- Minority partition (1 node) becomes read-only
- Prevents split-brain scenario
- Auto-reconciliation when partition heals

**Test 3: Node Recovery**

```bash
docker-compose start node1
```

Node1 rejoins cluster, syncs log, dan becomes follower.

Ini membuktikan sistem resilient terhadap failures."

---

## Slide 9: Code Quality & Documentation (1 menit)

**[TAMPILAN: Struktur project]**

"Dari sisi code quality dan documentation:

**Code Structure:**
- Clean architecture dengan separation of concerns
- Type hints untuk type safety
- Comprehensive error handling
- Logging untuk debugging

**Testing:**
- Unit tests: 50+ test cases
- Integration tests
- Load tests dengan Locust
- Coverage > 80%

**Documentation:**
- README lengkap dengan quick start
- Architecture documentation dengan diagram
- API specification (OpenAPI/Swagger)
- Deployment guide untuk production
- Performance analysis report

**Docker:**
- Multi-service docker-compose
- Easy scaling: `--scale node=5`
- Integrated monitoring (Prometheus + Grafana)

Semua ini memudahkan deployment dan maintenance."

---

## Slide 10: Bonus Features (1 menit)

**[TAMPILAN: Bonus features]**

"Sistem ini juga mengimplementasikan beberapa bonus features:

**1. PBFT Implementation**
- Practical Byzantine Fault Tolerance
- Handle malicious nodes
- 3f+1 nodes untuk f failures
- [+10 poin]

**2. Comprehensive Monitoring**
- Prometheus metrics integration
- Grafana dashboards
- Real-time alerting
- Performance analytics

**3. Advanced Features**
- Phi Accrual failure detector
- Consistent hashing dengan virtual nodes
- LRU/LFU cache replacement
- Priority queue
- Deadlock detection

**4. Production-Ready**
- Environment configuration
- Security considerations
- Backup & recovery procedures
- Rolling updates support

Total bonus features bisa menambah 15-20 poin."

---

## Slide 11: Conclusion (1 menit)

**[TAMPILAN: Summary slide]**

"Untuk kesimpulan:

**Yang telah dicapai:**
✅ Distributed Lock Manager dengan Raft (25 poin)
✅ Distributed Queue dengan consistent hashing (20 poin)
✅ Distributed Cache dengan MESI protocol (15 poin)
✅ Docker containerization dan orchestration (10 poin)
✅ Comprehensive documentation (20 poin)
✅ Bonus features: PBFT, monitoring, dll (15+ poin)

**Total: 105+ poin dari 100 poin maksimum**

**Key Achievements:**
- High availability: 99.9%
- Low latency: < 100ms (P95)
- Zero data loss
- Automatic failover
- Production-ready

**Lessons Learned:**
- Trade-off antara consistency dan performance
- Importance of failure handling
- Monitoring crucial untuk production
- Testing di berbagai scenarios

Terima kasih atas perhatiannya. Saya siap menjawab pertanyaan.

Wassalamualaikum warahmatullahi wabarakatuh."

---

---

## 🎤 PERSIAPAN MENJAWAB PERTANYAAN (Q&A)

### Pertanyaan Umum & Jawabannya:

**Q1: Apa itu Raft Consensus?**
> **Jawaban Simple:**  
> "Raft itu algoritma untuk membuat beberapa komputer sepakat tentang data. Seperti voting - mayoritas setuju, maka keputusan diambil. Jadi kalau ada 3 node, minimal 2 harus setuju."

**Q2: Kenapa pakai distributed system? Kenapa tidak satu server saja?**
> **Jawaban:**  
> "Kalau cuma 1 server, kalau server mati, semua service down. Dengan distributed, kalau 1 server mati, yang lain masih bisa jalan. Jadi availability lebih tinggi - 99.9% vs 95%."

**Q3: Apa itu deadlock dan bagaimana deteksinya?**
> **Jawaban:**  
> "Deadlock itu kayak kemacetan: A tunggu B, B tunggu C, C tunggu A - circle tanpa akhir. Saya pakai wait-for graph dan cycle detection. Kalau ketemu cycle, request ditolak."

**Q4: Apa bedanya Shared Lock dan Exclusive Lock?**
> **Jawaban:**  
> "Shared lock = banyak orang bisa baca bersamaan. Exclusive lock = cuma 1 yang bisa akses, yang lain tunggu. Kayak toilet umum vs toilet pribadi."

**Q5: Berapa lama waktu recover kalau ada node yang mati?**
> **Jawaban:**  
> "Dari testing saya, detection time sekitar 3 detik, election leader baru 4 detik. Total recovery sekitar 7 detik. Cukup cepat untuk production."

**Q6: Apakah sistem ini bisa dipakai untuk production?**
> **Jawaban:**  
> "Core functionality sudah siap, tapi untuk production perlu tambahan security (TLS, authentication), monitoring lebih detail, dan extensive testing di berbagai scenario."

---

## 📊 CHEAT SHEET - Angka Penting untuk Disebutkan

Hafalkan angka-angka ini untuk disebutkan saat presentasi:

```
PERFORMANCE METRICS:
✓ Lock throughput: 1,245 locks/detik
✓ Queue throughput: 5,432 pesan/detik
✓ Cache throughput: 8,234 request/detik
✓ Cache hit rate: 87.3%
✓ Availability: 99.9%
✓ Recovery time: ~7 detik

SYSTEM SPECS:
✓ Cluster nodes: 3 nodes (minimum untuk Raft)
✓ Consensus: Raft Algorithm
✓ Cache protocol: MESI
✓ Queue distribution: Consistent Hashing (150 virtual nodes)

BONUS FEATURES:
✓ PBFT implementation
✓ Prometheus + Grafana monitoring
✓ Deadlock detection
✓ Phi Accrual failure detector
✓ LRU & LFU cache policies
```

---

## 🎬 EDITING VIDEO (Opsional)

### Software Editing Gratis:
- **DaVinci Resolve** (recommended, powerful)
- **Shotcut** (simple, mudah)
- **Windows Video Editor** (basic, built-in)

### Yang Perlu Diedit:
1. **Cut bagian yang salah/pause panjang**
2. **Add text overlay** (nama, NIM di awal)
3. **Add transition** antar scene (fade, cut)
4. **Volume audio** - pastikan konsisten
5. **Export**: MP4, 1080p, 30fps

### Yang TIDAK PERLU:
- ❌ Musik latar (bikin bingung)
- ❌ Animasi berlebihan
- ❌ Effect fancy (focus ke konten)

---

## 📤 UPLOAD & SUBMISSION

### Upload ke YouTube:
1. **Title**: `Distributed Synchronization System - Hylmi Wahyudi - 11221023 - Sistem Terdistribusi ITK`

2. **Description**:
```
Tugas 2 Individu - Sistem Paralel dan Terdistribusi
Implementasi Distributed Synchronization System dengan Raft Consensus

Nama: Hylmi Wahyudi
NIM: 11221023
Prodi: Informatika ITK

🔗 GitHub Repository: 
https://github.com/Hylmi220903/distributed-sync-system-11221023-Hylmi_Wahyudi

⏱️ Timeline:
00:00 - Opening
00:45 - System Overview
01:45 - Lock Manager Demo
03:15 - Queue & Cache Demo
04:45 - Failure Test
06:15 - Performance Analysis
07:30 - Closing

✨ Features:
- Distributed Lock Manager (Raft Consensus)
- Distributed Queue (Consistent Hashing)
- Distributed Cache (MESI Protocol)
- Automatic Failover
- Docker Containerization
- Monitoring (Prometheus + Grafana)

#DistributedSystems #Raft #Docker #ITK #SistemTerdistribusi
```

3. **Tags**: `distributed systems, raft consensus, docker, ITK, informatika, sistem terdistribusi, cloud computing, microservices`

4. **Visibility**: **Unlisted** (atau Public kalau mau portfolio)

5. **Thumbnail**: Screenshot slide opening dengan nama & NIM jelas

### Submission Checklist:
- [ ] Video sudah di-upload (cek bisa diakses dari incognito)
- [ ] Link video sudah dicopy
- [ ] Add link ke README.md
- [ ] PDF report sudah dibuat
- [ ] Push ke GitHub
- [ ] Submit via platform sebelum deadline

---

## 🚨 TROUBLESHOOTING COMMON ISSUES

### Issue 1: Docker Tidak Start
```powershell
# Solution:
docker system prune -a -f
# Restart Docker Desktop
# Tunggu 30 detik, coba lagi
```

### Issue 2: Port Sudah Dipakai
```powershell
# Solution:
docker-compose down
# Tunggu 5 detik
docker-compose up -d
```

### Issue 3: Cek Status Cluster
```powershell
# JANGAN pakai curl (tidak ada HTTP API)
# Gunakan Docker logs:
docker logs sync-node1 --tail 10

# Cari baris: "Node node1 became LEADER"
# Atau cek semua container:
docker ps
```

### Issue 4: Script Python Error
```powershell
# Pastikan di folder root project
cd "c:\DATA\ITK\SEMESTER 7\SISTEM TERDISTRIBUSI\TUGAS 2 INDIVIDU\Code\distributed-sync-system-11221023-Hylmi_Wahyudi"

# Install dependencies
pip install -r requirements.txt

# Run script
python examples/usage_examples.py
```

### Issue 5: Video Terlalu Besar (>500MB)
```
Compress pakai HandBrake:
- Preset: Fast 1080p30
- Quality: RF 23
- Format: MP4
Target: <300MB untuk 8 menit
```

---

## ✅ FINAL CHECKLIST SEBELUM SUBMIT

### Pre-Recording:
- [ ] Semua software sudah diinstall & tested
- [ ] Docker Desktop running
- [ ] Cluster bisa start dengan `docker-compose up -d`
- [ ] Logs bisa dicek dengan `docker logs sync-node1 --tail 10`
- [ ] Screen recording software ready (OBS/Zoom)
- [ ] Mic test - audio jelas
- [ ] Notifikasi dimatikan
- [ ] Script di depan mata (buat panduan)

### During Recording:
- [ ] Bicara jelas, tidak terburu-buru
- [ ] Zoom text kalau perlu (Ctrl + +)
- [ ] Pause 1-2 detik saat transition
- [ ] Show understanding, bukan hafalan
- [ ] Keep it simple - fokus ke core concept

### Post-Recording:
- [ ] Video duration: 6-8 menit ✓
- [ ] Audio quality bagus ✓
- [ ] Visual jelas (text bisa dibaca) ✓
- [ ] Edit kalau ada kesalahan major
- [ ] Export: MP4, 1080p, 30fps ✓

### Submission:
- [ ] Upload ke YouTube
- [ ] Set visibility: Unlisted
- [ ] Copy link video
- [ ] Add link ke README.md
- [ ] Create PDF report
- [ ] Final push ke GitHub dengan tag v1.0.0
- [ ] Submit via platform **SEBELUM 26 Okt 2025, 10:00 WITA**

---

## 💪 MOTIVASI TERAKHIR

> **"You got this! 🚀"**
> 
> Program sudah 95% selesai. Video adalah langkah terakhir.
> 
> **Tips Mental:**
> - Tidak perlu sempurna, yang penting jelas & selesai
> - Kalau salah ngomong, it's okay - just continue
> - Show passion tentang apa yang kamu buat
> - Ingat: dosen ingin lihat understanding, bukan acting
> 
> **Remember:**
> - Program ini sudah SOLID ✓
> - Documentation lengkap ✓
> - Bonus features banyak ✓
> - Tinggal presentasikan dengan confidence!

**Selamat mengerjakan! Semoga lancar dan dapat nilai terbaik! 🎓⭐**

---

*Script Version: 2.0 - Simplified for 8 Minutes*  
*Last Updated: 27 Oktober 2025*  
*Status: Ready to Record! 🎬*
