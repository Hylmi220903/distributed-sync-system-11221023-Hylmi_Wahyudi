# 📚 PENJELASAN KONSEP DASAR - Bahasa Sederhana

**Untuk Pemahaman Cepat Sebelum Presentasi**

---

## 🎯 APA ITU DISTRIBUTED SYSTEM?

### Analogi Sederhana:
**Single System** = 1 kasir di supermarket
- Kalau kasir sakit → toko tutup ❌
- Kalau antrian panjang → lambat ❌
- Kalau komputer crash → semua data hilang ❌

**Distributed System** = 5 kasir di supermarket
- Kalau 1 kasir sakit → 4 kasir lain masih kerja ✅
- Kalau antrian panjang → dibagi ke 5 kasir ✅
- Kalau 1 komputer crash → data ada di 4 lainnya ✅

**Intinya:** Distributed = banyak komputer kerja bareng untuk 1 tujuan

---

## 🔐 DISTRIBUTED LOCK MANAGER

### Apa itu Lock?
**Analogi:** Toilet umum dengan kunci

- **Exclusive Lock** = Toilet pribadi
  - Cuma 1 orang bisa masuk
  - Yang lain harus antri di luar
  - Contoh: Edit database (cuma 1 yang bisa edit)

- **Shared Lock** = Ruang perpustakaan
  - Banyak orang bisa baca buku bersamaan
  - Tapi kalau ada yang mau ganti buku → semua keluar dulu
  - Contoh: Baca data (banyak yang bisa baca)

### Masalah: Deadlock
**Analogi:** Kemacetan di perempatan

```
Mobil A tunggu Mobil B bergerak
Mobil B tunggu Mobil C bergerak
Mobil C tunggu Mobil A bergerak
→ MACET TOTAL! Tidak ada yang bisa gerak
```

**Solusi:** Deteksi deadlock pakai "wait-for graph"
- Buat peta: siapa tunggu siapa
- Kalau ada circle → DEADLOCK!
- Tolak request yang bikin deadlock

### Kenapa Pakai Raft?
**Raft** = sistem voting untuk ambil keputusan

```
3 komputer vote: "Kasih lock ke Client A?"
- Komputer 1: SETUJU ✅
- Komputer 2: SETUJU ✅
- Komputer 3: TIDAK SETUJU ❌

Mayoritas (2 dari 3) = SETUJU
→ Lock dikasih ke Client A
```

**Keuntungan:**
- Kalau 1 komputer mati, 2 lainnya masih bisa vote
- Data konsisten di semua komputer
- No single point of failure

---

## 📬 DISTRIBUTED QUEUE SYSTEM

### Apa itu Queue?
**Analogi:** Antrian di bank

```
Customer A → Customer B → Customer C
(masuk)      (tunggu)      (tunggu)
   ↓
Teller
   ↓
(selesai)
```

**Distributed Queue** = Antrian di banyak bank cabang
- Pesan datang → distribusi ke cabang yang kosong
- Kalau 1 cabang tutup → pesan dialihkan ke cabang lain

### Consistent Hashing
**Analogi:** Pembagian wilayah delivery

**Cara Sederhana (SALAH):**
```
Node 1 → handle Client 1-100
Node 2 → handle Client 101-200
Node 3 → handle Client 201-300
```
**Problem:** Kalau Node 2 mati, semua Client 101-200 pindah → chaos!

**Consistent Hashing (BENAR):**
```
Buat cincin (ring) 0-360 derajat
Node 1 di 10°, 130°, 250° (3 virtual nodes)
Node 2 di 50°, 170°, 290° (3 virtual nodes)
Node 3 di 90°, 210°, 330° (3 virtual nodes)

Client 145° → ke Node terdekat searah jarum jam → Node 2
```
**Keuntungan:** Kalau Node 2 mati, cuma client di sekitar Node 2 yang affected

### At-Least-Once Delivery
**Analogi:** Paket pos dengan resi

```
1. Kirim paket
2. Minta tanda tangan (acknowledgment)
3. Kalau tidak ada tanda tangan dalam 5 menit → kirim ulang
4. Ulangi sampai dapat tanda tangan
```

**Guarantee:** Pesan PASTI sampai minimal 1 kali
**Trade-off:** Mungkin sampai 2 kali (duplicate), tapi tidak hilang

---

## 💾 DISTRIBUTED CACHE SYSTEM

### Apa itu Cache?
**Analogi:** Meja kerja vs lemari arsip

**Tanpa Cache:**
```
Butuh data → buka lemari → cari folder → ambil → tutup lemari
(10 detik)
```

**Dengan Cache:**
```
Butuh data → ambil dari meja (cache)
(1 detik)
```

**Keuntungan:** 10x lebih cepat!

### MESI Protocol
Untuk sinkronisasi cache di banyak komputer

**4 Status:**

1. **M = Modified** (Merah)
   - Data di cache ini sudah diubah
   - Data di tempat lain belum update
   - Harus write-back ke database

2. **E = Exclusive** (Hijau)
   - Data cuma ada di cache ini
   - Data sama dengan database
   - Aman untuk baca/tulis

3. **S = Shared** (Kuning)
   - Data ada di banyak cache
   - Semua copy sama
   - Aman untuk baca, tapi kalau mau tulis → invalidasi dulu

4. **I = Invalid** (Abu-abu)
   - Data tidak valid
   - Harus fetch dari database

**Contoh Flow:**
```
Komputer A: Ambil data User 123 → Status: EXCLUSIVE (E)
Komputer B: Ambil data User 123 → A & B status: SHARED (S)
Komputer A: Update User 123 → A status: MODIFIED (M), B status: INVALID (I)
Komputer B: Kalau mau data → fetch lagi dari A
```

### LRU vs LFU
**LRU = Least Recently Used** (yang paling lama tidak dipakai)
```
Cache penuh → hapus yang terakhir diakses paling lama
Contoh: File yang dibuka 1 bulan lalu → hapus
```

**LFU = Least Frequently Used** (yang paling jarang dipakai)
```
Cache penuh → hapus yang paling jarang diakses
Contoh: File yang cuma dibuka 1x vs 100x → hapus yang 1x
```

---

## ⚙️ RAFT CONSENSUS ALGORITHM

### 3 Role dalam Raft:

1. **LEADER** = Ketua kelas
   - Terima request dari client
   - Kasih instruksi ke follower
   - Kirim heartbeat tiap 1 detik

2. **FOLLOWER** = Anggota kelas
   - Dengarkan instruksi dari leader
   - Kalau leader tidak terdengar 3 detik → mulai election

3. **CANDIDATE** = Calon ketua
   - Minta vote dari follower
   - Kalau dapat mayoritas → jadi leader
   - Kalau kalah → balik jadi follower

### Leader Election (Pemilihan Ketua)
```
1. Leader mati / tidak terdengar
2. Follower A: "Saya kandidat! Vote saya dong!"
3. Follower B: "OK, saya vote kamu" ✅
4. Follower C: "OK, saya vote kamu" ✅
5. Follower A dapat 2 dari 3 vote → MENANG!
6. Follower A jadi LEADER baru
```

**Random timeout:** Supaya tidak semua jadi kandidat bersamaan (collision)

### Log Replication (Replikasi Data)
```
1. Leader terima request: "Tambah data X"
2. Leader tulis ke log: [Term 1, Index 5, Data X]
3. Leader kirim ke Follower A & B
4. Follower A: "OK, sudah tulis" ✅
5. Follower B: "OK, sudah tulis" ✅
6. Leader: "Mayoritas OK → COMMIT!"
7. Data X officially saved
```

**Consistency guarantee:** Semua node pasti punya data yang sama

---

## 🎯 PBFT (Bonus Feature)

### Apa itu Byzantine Failure?
**Raft:** Hanya handle node mati (crash)
**PBFT:** Handle node jahat (malicious)

**Analogi:** Mafia game
- Ada pemain normal ✅
- Ada pemain mafia (bohong) ❌

**PBFT Rule:** Untuk handle f pemain jahat, perlu minimal 3f+1 pemain
```
Contoh: 1 pemain jahat → perlu 4 pemain (3×1 + 1)
        2 pemain jahat → perlu 7 pemain (3×2 + 1)
```

### 3 Phase PBFT:
1. **Pre-Prepare:** Leader propose request
2. **Prepare:** Semua node agree sama order
3. **Commit:** Execute setelah 2f+1 node agree

**Lebih secure** tapi **lebih lambat** dari Raft

---

## 📊 PERFORMANCE METRICS - Apa Artinya?

### Throughput
**Berapa banyak request per detik**
```
Lock Manager: 1,245 locks/detik
Queue: 5,432 pesan/detik
Cache: 8,234 request/detik
```
**Artinya:** Sistem bisa handle ribuan operasi per detik

### Latency (Delay)
**Berapa lama untuk 1 request**
```
Average: 45ms (milidetik) → 0.045 detik
P95: 156ms → 95% request selesai dalam 0.156 detik
P99: 287ms → 99% request selesai dalam 0.287 detik
```
**Artinya:** Hampir semua request cepat (< 300ms)

### Hit Rate (Cache)
**Berapa persen data ada di cache**
```
87.3% hit rate
→ 87 dari 100 request dapat data dari cache (cepat)
→ 13 dari 100 request harus fetch dari database (lambat)
```
**Semakin tinggi semakin bagus!**

### Availability
**Berapa persen waktu sistem online**
```
99.9% availability
→ 365 hari × 24 jam = 8,760 jam/tahun
→ Downtime: 0.1% × 8,760 = 8.76 jam/tahun ≈ 9 jam/tahun
→ Uptime: 8,751 jam/tahun ✅
```
**Production standard:** minimal 99% (three nines)

---

## 🔧 DOCKER & CONTAINERIZATION

### Apa itu Docker?
**Analogi:** Kontainer cargo

**Tanpa Docker:**
```
Di laptop A: Python 3.9 → jalan ✅
Di laptop B: Python 3.7 → error ❌
Problem: "Works on my machine!" syndrome
```

**Dengan Docker:**
```
Buat kontainer dengan Python 3.9 di dalamnya
Kontainer jalan di laptop manapun → konsisten ✅
```

### Docker Compose
**Analogi:** Orkestra musik

**Manual (RIBET):**
```
Start Redis
Start Node 1
Start Node 2
Start Node 3
Start Prometheus
Start Grafana
```

**Docker Compose (MUDAH):**
```
docker-compose up -d
→ Start semua sekaligus! 🎵
```

---

## 💡 KENAPA SEMUA INI PENTING?

### Real World Use Cases:

**1. E-Commerce (Tokopedia/Shopee)**
- Lock: Supaya 2 orang tidak beli barang terakhir bersamaan
- Queue: Process order secara berurutan
- Cache: Product details supaya cepat loading

**2. Banking (BCA/Mandiri)**
- Lock: Prevent double spending
- Queue: Transaction queue
- Cache: Saldo account

**3. Social Media (Instagram/Twitter)**
- Lock: Edit post
- Queue: Notification queue
- Cache: Feed & profile cache

**Tanpa distributed system:** Kalau server mati → semua service down!

---

## 🎯 KEY TAKEAWAYS (HAFALKAN!)

### 3 Hal Penting:

**1. CONSISTENCY (Konsistensi)**
→ Semua node punya data yang sama
→ Pakai Raft Consensus untuk voting

**2. AVAILABILITY (Ketersediaan)**
→ Sistem tetap jalan walaupun ada node mati
→ 99.9% uptime

**3. PARTITION TOLERANCE (Toleransi Partisi)**
→ Sistem handle kalau network putus
→ Majority partition tetap jalan

**Ini adalah CAP Theorem → pilih 2 dari 3**
**Sistem ini pilih:** CP (Consistency + Partition Tolerance)

---

## 📝 TIPS JAWAB PERTANYAAN

### Kalau Tidak Tahu Jawabannya:

**JANGAN bilang:** "Saya tidak tahu"

**TAPI bilang:**
> "Untuk hal itu, saya belum implement secara detail, tapi conceptnya adalah... [explain general concept]. Untuk production, ini perlu ditambahkan dengan... [suggest improvement]"

**Contoh:**
> Q: "Bagaimana handle security?"
> 
> A: "Untuk security, saya belum implement TLS encryption di versi ini, tapi conceptnya adalah setiap komunikasi antar node harus encrypted pakai certificate. Untuk production, perlu ditambahkan authentication token dan RBAC untuk access control."

**Show you understand the concept**, walaupun belum implement!

---

## ✅ READY FOR PRESENTATION!

**Anda sudah paham:**
- ✅ Apa itu distributed system (banyak komputer kerja bareng)
- ✅ Lock manager (atur akses data)
- ✅ Queue system (antrian pesan)
- ✅ Cache system (percepat akses data)
- ✅ Raft consensus (voting untuk konsisten)
- ✅ Performance metrics (throughput, latency, availability)

**Next step:** Rekam video dengan percaya diri! 🚀🎓

---

*Simplified Concepts Guide v1.0*  
*Last Updated: 27 Oktober 2025*  
*You got this! 💪*
