# 🚀 DEMO QUICK START GUIDE

**Untuk Video Presentasi - Hylmi Wahyudi (11221023)**

---

## ⚡ PERSIAPAN CEPAT (5 MENIT)

### 1. Pastikan Ini Sudah Terinstall:
```powershell
# Check Docker
docker --version
# Harus muncul: Docker version 20.x.x atau lebih

# Check Python
python --version
# Harus muncul: Python 3.8 atau lebih
```

**Kalau belum ada, install:**
- Docker Desktop: https://www.docker.com/products/docker-desktop/
- Python: https://www.python.org/downloads/

### 2. Buka PowerShell di Folder Project:
```powershell
cd "c:\DATA\ITK\SEMESTER 7\SISTEM TERDISTRIBUSI\TUGAS 2 INDIVIDU\Code\distributed-sync-system-11221023-Hylmi_Wahyudi"
```

### 3. Install Dependencies (Sekali Aja):
```powershell
pip install -r requirements.txt
```

**Tunggu sampai selesai (1-2 menit)**

---

## 🎬 SAAT DEMO VIDEO

### STEP 1: Start Cluster (30 detik)

```powershell
# Masuk ke folder docker
cd docker

# Start semua services
docker-compose up -d

# Tunggu 15-20 detik sampai semua container running
```

**Output yang bagus:**
```
✓ Container distributed-sync-redis     Started
✓ Container sync-node1                 Started
✓ Container sync-node2                 Started
✓ Container sync-node3                 Started
✓ Container sync-prometheus            Started
✓ Container sync-grafana               Started
```

### STEP 2: Check Status (10 detik)

```powershell
# Cek status cluster dengan Docker logs
docker logs sync-node1 --tail 10
```

**Output yang diharapkan (cari baris ini):**
```
INFO - Node node1 became LEADER for term 1
INFO - Node node1 listening on node1:8001
```

✅ Kalau muncul "LEADER", berarti cluster sudah ready!

**Atau cek semua container running:**
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}"
```

**Harus semua "Up":**
```
NAMES                    STATUS
sync-node1              Up X minutes
sync-node2              Up X minutes
sync-node3              Up X minutes
sync-grafana            Up X minutes
sync-prometheus         Up X minutes
distributed-sync-redis  Up X minutes (healthy)
```

### STEP 3: Demo Lock Manager (30 detik)

```powershell
# Kembali ke root folder
cd ..

# Jalankan demo script
python examples/usage_examples.py
```

**Output yang bagus:**
```
✓ Lock acquired by client1: database:users
✓ Client2 waiting for lock...
✓ Lock released by client1
✓ Lock acquired by client2
✓ All demos completed successfully!
```

### STEP 4: Demo Failure Test (30 detik)

```powershell
# Stop leader node
docker stop sync-node1

# Tunggu 5 detik, lalu cek logs node2
timeout /t 5 /nobreak
docker logs sync-node2 --tail 5

# Lihat apakah node2 jadi LEADER
# Output yang diharapkan: "Node node2 became LEADER"

# Start lagi node1
docker start sync-node1

# Cek logs - node1 akan rejoin sebagai FOLLOWER
timeout /t 5 /nobreak
docker logs sync-node1 --tail 5
```

### STEP 5: Buka Monitoring (20 detik)

**Browser: Buka 3 tabs**

1. **Grafana**: http://localhost:3000
   - Username: `admin`
   - Password: `admin`
   - Skip setup wizard

2. **Prometheus**: http://localhost:9090
   - Langsung bisa lihat metrics

3. **Node API**: http://localhost:8001/api/status
   - JSON status cluster

---

## 🛑 SELESAI DEMO - STOP CLUSTER

```powershell
# Stop semua container
cd docker
docker-compose down

# Atau kalau mau clean total (hapus data):
docker-compose down -v
```

---

## ⚠️ TROUBLESHOOTING CEPAT

### Problem 1: Docker Error
```powershell
# Solution: Restart Docker Desktop
# Tunggu 30 detik
# Coba lagi: docker-compose up -d
```

### Problem 2: Port Sudah Dipakai
```powershell
# Stop dulu
docker-compose down

# Tunggu 5 detik

# Start lagi
docker-compose up -d
```

### Problem 3: Python Script Error
```powershell
# Pastikan di root folder
cd "c:\DATA\ITK\SEMESTER 7\SISTEM TERDISTRIBUSI\TUGAS 2 INDIVIDU\Code\distributed-sync-system-11221023-Hylmi_Wahyudi"

# Install ulang dependencies
pip install --force-reinstall -r requirements.txt

# Coba lagi
python examples/usage_examples.py
```

### Problem 4: Curl Command Not Found
```powershell
# Pakai PowerShell alternative:
Invoke-WebRequest http://localhost:8001/api/status | Select-Object -Expand Content
```

### Problem 5: Container Tidak Mau Start
```powershell
# Clean everything
docker-compose down -v
docker system prune -f

# Tunggu 10 detik

# Start fresh
docker-compose up -d
```

---

## 📋 COMMAND CHEAT SHEET

### Commands untuk Copy-Paste Cepat:

```powershell
# 1. Start cluster
cd docker; docker-compose up -d; cd ..

# 2. Check status (lihat logs)
docker logs sync-node1 --tail 10

# 3. Check semua container
docker ps --format "table {{.Names}}\t{{.Status}}"

# 4. Run demo
python examples/usage_examples.py

# 5. Stop leader
docker stop sync-node1

# 6. Check new leader (tunggu 5 detik)
timeout /t 5 /nobreak; docker logs sync-node2 --tail 5

# 7. Restart node
docker start sync-node1

# 8. Stop everything
cd docker; docker-compose down
```

---

## 🎯 DEMO SEQUENCE (Urutan Rekaman)

**Total: 5-6 menit demo**

1. ✅ **Intro** (30 detik)
   - Buka VS Code, tunjukkan struktur folder
   
2. ✅ **Start Cluster** (30 detik)
   - `docker-compose up -d`
   - Tunjukkan Docker Desktop - semua green
   
3. ✅ **Check Status** (20 detik)
   - `curl http://localhost:8001/api/status`
   - Explain output: leader, term, cluster size
   
4. ✅ **Demo Lock** (1 menit)
   - `python examples/usage_examples.py`
   - Explain output: acquire, wait, release
   
5. ✅ **Demo Failure** (1 menit)
   - Stop node1
   - Check status - leader changed
   - Start node1 - cluster healed
   
6. ✅ **Show Monitoring** (1 menit)
   - Buka Grafana
   - Buka Prometheus
   - Show metrics
   
7. ✅ **Show Documentation** (1 menit)
   - Scroll docs/performance_analysis.md
   - Highlight angka: throughput, latency, hit rate
   
8. ✅ **Closing** (30 detik)
   - `docker-compose down`
   - Summary achievement

---

## 💡 TIPS PRESENTASI

### DO's ✅
- Bicara pelan dan jelas
- Zoom terminal kalau text kecil (`Ctrl` + `+`)
- Pause 2 detik sebelum ganti scene
- Tunjuk dengan mouse cursor
- Explain "kenapa" bukan cuma "apa"

### DON'Ts ❌
- Jangan terburu-buru
- Jangan skip error (explain it)
- Jangan baca script verbatim
- Jangan over-technical
- Jangan lebih dari 8 menit

---

## 🎬 READY TO RECORD?

### Pre-Flight Checklist:
- [ ] Docker Desktop running
- [ ] PowerShell opened di folder project
- [ ] Browser opened (3 tabs: Grafana, Prometheus, API)
- [ ] VS Code opened
- [ ] OBS/Zoom recording ready
- [ ] Mic tested
- [ ] Notifikasi off
- [ ] Script di depan mata

### Test Run:
```powershell
# Quick test (2 menit)
cd docker
docker-compose up -d
# Tunggu 20 detik
curl http://localhost:8001/api/status
# Kalau OK, siap rekam!
docker-compose down
```

---

## 🚀 GO! REKAM SEKARANG!

**Remember:**
- Durasi target: **6-8 menit**
- Fokus: **Understanding > Perfection**
- Tone: **Confident & Clear**

**You got this! 💪🎓**

---

*Quick Start Guide v1.0*  
*Created: 27 Oktober 2025*  
*For: Video Presentation Demo*
