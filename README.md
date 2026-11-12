# 🌍 EcoSort AI
**Futuristic Waste Vision Dashboard, RCA & AI Assistant**

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)
![YOLO](https://img.shields.io/badge/YOLOv8%2Fv11-Ultralytics-7C3AED.svg?style=for-the-badge)
![OpenCV](https://img.shields.io/badge/OpenCV-Vision-5C3EE8.svg?style=for-the-badge&logo=opencv&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)

**[Fitur Utama](#-fitur-utama) • [Pengelompokan Sampah](#-pengelompokan--pilahan-sampah) • [Instalasi](#-cara-menjalankan-website) • [Struktur Proyek](#-struktur-proyek)**

</div>

---

**EcoSort AI** adalah platform web Computer Vision terintegrasi untuk mendeteksi, mengklasifikasikan, melacak (*tracking*), menghitung (*event counting*), menganalisis akar masalah (*Root Cause Analysis - RCA*), dan mengonsultasikan pemilahan sampah secara *real-time* melalui satu webcam pada meja pemilahan.

Aplikasi ini dibalut dengan tema visual **Putih, Biru Elektrik, dan Ungu Futuristik** yang elegan, serta mengelompokkan sampah ke dalam 3 pilahan makro: **Anorganik**, **Organik**, dan **Berbahaya (B3)**.

---

## ✨ Fitur Utama

- 📸 **Real-time Live Detection:** Deteksi sampah secara instan menggunakan YOLO.
- 🎯 **Object Tracking & Counting:** Deduplikasi hitungan menggunakan algoritma *Virtual Line Crossing*.
- 📊 **Futuristic Dashboard Analytics:** Visualisasi data menggunakan *Chart.js* dan tabel riwayat interaktif.
- 🔔 **Smart Notifications:** Sistem peringatan otomatis berdasarkan ambang batas volume sampah.
- 📄 **Automated PDF Reports:** Pembuatan laporan operasional dengan *ReportLab*.
- 🔍 **Root Cause Analysis (RCA):** Modul diagnostik anomali meja pemilahan (5-Whys & Ishikawa/Fishbone).
- 🤖 **EcoBot AI Assistant:** Chatbot cerdas untuk konsultasi pemilahan, K3, dan status statistik terkini.

---

## 🗑️ Pengelompokan & Pilahan Sampah

Sistem memetakan **6 kelas deteksi resmi YOLO** ke dalam **3 Kategori Makro**:

| Makro | Kategori | Kelas Objek YOLO | Keterangan & Contoh | Penanganan & K3 | Warna UI |
|:---:|:---|:---|:---|:---|:---:|
| 🧴 | **Anorganik** | `plastic_bottle`<br>`plastic_bag`<br>`glass_bottle` | Botol plastik minuman, kantong kresek kemasan, botol kaca sirup/saus. Sulit terurai secara hayati. | Bilas residu cairan, pisahkan plastik film & polimer kaku, kirim ke bank sampah/daur ulang. | ![#2563EB](https://placehold.co/15x15/2563EB/2563EB.png) Biru |
| 🍃 | **Organik** | `paper`<br>`cardboard` | Kertas HVS dokumen, koran bekas, kardus cokelat, karton boks. Serat selulosa alami. | Jaga tetap kering dari tumpahan air/minyak agar serat pulp dapat didaur ulang/dikompos. | ![#10B981](https://placehold.co/15x15/10B981/10B981.png) Hijau |
| ⚠️ | **Berbahaya** | `metal_can` | Kaleng minuman aluminium, kaleng cat timah, kaleng aerosol bertekanan. | **Wadah khusus B3 tahan tusuk**. Hindari kompresi manual tanpa APD (risiko tajam & gas). | ![#7C3AED](https://placehold.co/15x15/7C3AED/7C3AED.png) Ungu |

---

## 🧠 Modul Cerdas Tambahan

### 🔬 Root Cause Analysis (RCA)
Modul **RCA Diagnostics** dirancang untuk mendiagnosis anomali operasional di meja pemilahan menggunakan metodologi industri:
- **Metode 5-Whys:** Penelusuran berantai untuk menemukan akar masalah.
- **Diagram Tulang Ikan Ishikawa (5M+1E):** Analisis multidimensi (*Man, Machine, Method, Material, Environment*).
- **CAPA (Corrective & Preventive Actions):** Rekomendasi tindakan korektif darurat dan pencegahan sistemik jangka panjang.
- **Interactive Anomaly Lifecycle:** *Active* ➔ *Investigating* ➔ *Resolved*.

### 🤖 AI Chatbot Assistant (EcoBot AI)
Asisten cerdas tersemat langsung di *dashboard*:
- **Konsultasi Edukatif:** *"Kardus dan kertas itu organik atau bukan?"*
- **Panduan K3 Berbahaya:** *"Bagaimana menangani kaleng logam tajam?"*
- **Live Database Query:** *"Berapa jumlah sampah berbahaya hari ini?"*
- **Ringkasan Analitik:** Merangkum RCA dan memberikan rekomendasi pencegahan lonjakan sampah.

---

## 🚀 Cara Menjalankan Website

Ikuti langkah-langkah berikut untuk menjalankan EcoSort AI di lingkungan lokal Anda.

### 1. Persiapan Environment
Pastikan Anda sudah menginstal dependensi (disarankan menggunakan *virtual environment*):
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Jalankan Server FastAPI
Jalankan server *backend* menggunakan Uvicorn:
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Akses Dashboard
Buka *browser* Anda dan kunjungi tautan berikut:
- 🌐 **Web Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- 📖 **Interactive API Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Hasil Pengujian (Test Suite)

Proyek ini dilengkapi dengan serangkaian *unit test* menggunakan `pytest`. Jalankan perintah berikut untuk menguji *codebase*:

```bash
python -m pytest backend/tests -v
```

✅ **Hasil Pengujian: 10 passed (100% Lulus)**
- `test_class_mapping_order`
- `test_macro_categories_mapping`
- `test_health_check_endpoint`
- `test_requirements_docs_endpoint`
- `test_tracking_and_event_counting_deduplication`
- `test_database_detection_service_with_macro_categories`
- `test_rca_diagnostics_endpoint`
- `test_chatbot_endpoint`
- `test_notification_service_and_cooldown`
- `test_report_generation`

---

## 📂 Struktur Proyek

```text
EcoSort-AI/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # Endpoint Camera, Dashboard, Notifikasi, Chat, RCA
│   │   ├── core/            # Config, Database Engine, Logging
│   │   ├── cv/              # YOLO Detector, Tracker, Counter, Camera Worker
│   │   ├── models/          # ORM Models (SQLAlchemy)
│   │   ├── schemas/         # Pydantic Schemas
│   │   ├── services/        # Business Logic (Detection, Report, Chat, RCA)
│   │   └── main.py          # FastAPI Entrypoint
│   └── tests/               # Pytest Suite
├── dataset/                 # Data, Labels, dan Konfigurasi (data.yaml)
├── frontend/
│   ├── static/              # CSS (Tema Putih-Biru-Ungu) & JavaScript Modular
│   └── templates/           # Halaman HTML Dashboard
├── models/                  # File weight model YOLO (best.pt)
├── requirements/            # Dokumen proyek (PRD, SRS)
├── storage/                 # Penyimpanan Snapshots & Laporan PDF
├── .env.example             # Template variabel lingkungan
└── requirements.txt         # Dependensi Python
```

---

<div align="center">
  Dibuat dengan ❤️ untuk lingkungan yang lebih bersih dan masa depan yang berkelanjutan. <br>
  © 2026 EcoSort AI Team.
</div>