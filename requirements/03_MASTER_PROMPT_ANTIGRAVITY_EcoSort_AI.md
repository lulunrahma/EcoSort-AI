# Master Prompt — Antigravity
## Build EcoSort AI: YOLO Waste Detection Web Dashboard

Kamu bertindak sebagai **senior full-stack engineer, computer vision engineer, software architect, dan UI/UX engineer**. Bangun aplikasi bernama **EcoSort AI** berdasarkan instruksi dan batasan berikut.

Dokumen ini adalah prompt utama proyek. Jika ada konflik, prioritaskan requirement yang lebih spesifik dan eksplisit di bagian ini, lalu dokumentasikan keputusan teknis yang dibuat.

---

## 1. Product Context

EcoSort AI adalah web dashboard untuk mendeteksi, mengklasifikasikan, melacak, menghitung, dan memantau sampah melalui **satu webcam pada meja pemilahan**.

Sistem menggunakan model object detection YOLO yang dilatih menggunakan dataset hybrid dari Roboflow Universe dan foto kamera sendiri.

Fitur MVP:
1. Dashboard analytics.
2. Real-time webcam detection.
3. Automatic notifications.
4. Object tracking.
5. Detection history dan database.
6. Automatic PDF reports.

Aplikasi adalah alat bantu monitoring. Jangan mengklaim sistem melakukan pemilahan fisik atau menentukan kelayakan daur ulang secara sempurna.

## 2. Class Mapping — WAJIB KONSISTEN

Gunakan enam class berikut dengan urutan yang sama di seluruh aplikasi:

| ID | Class |
|---:|---|
| 0 | `plastic_bottle` |
| 1 | `plastic_bag` |
| 2 | `paper` |
| 3 | `cardboard` |
| 4 | `metal_can` |
| 5 | `glass_bottle` |

Jangan mengganti, menerjemahkan, mengurutkan ulang, atau menambahkan class tanpa perubahan eksplisit dari pemilik proyek. Validasi nama class model saat startup. Jangan mengasumsikan class ID jika model menyediakan mapping names sendiri.

## 3. Technical Direction

Gunakan stack berikut sebagai default:

### Backend
- Python.
- FastAPI.
- OpenCV untuk webcam/frame handling.
- Ultralytics YOLO untuk inference.
- Tracker yang kompatibel dengan pipeline Ultralytics, misalnya ByteTrack.
- SQLAlchemy untuk ORM.
- Pydantic untuk request/response schemas.
- SQLite untuk development awal; buat konfigurasi agar PostgreSQL dapat dipakai kemudian.
- ReportLab untuk PDF.

### Frontend
- HTML, CSS, JavaScript modular atau framework yang sudah tersedia di repository.
- Chart.js untuk grafik bila sesuai.
- Lucide icons atau icon set yang tersedia.
- Responsive dashboard, prioritas desktop/tablet.

### Dataset/Model
- Roboflow sebagai dataset management.
- Format ekspor YOLO yang kompatibel dengan Ultralytics.
- Model path dan confidence threshold dari environment/config, bukan hard-coded.
- Jangan mengunduh dataset atau model secara otomatis tanpa instruksi dan konfigurasi pengguna.

Jika repository sudah memiliki stack atau pola arsitektur, inspeksi dahulu dan pertahankan pola yang masuk akal. Jangan mengganti framework hanya demi preferensi pribadi.

## 4. Workflow Sebelum Coding

1. Inspeksi seluruh repository dan file yang sudah ada.
2. Baca PRD, SRS, dan dokumen ketentuan tambahan bila tersedia.
3. Identifikasi bahasa, framework, entry point, dependency, dan cara menjalankan aplikasi.
4. Buat ringkasan kondisi repository dan rencana implementasi.
5. Buat atau perbarui `README.md`, `.env.example`, dan dependency manifest.
6. Implementasikan secara bertahap dan jalankan test setelah setiap bagian.
7. Jangan menghapus file atau konfigurasi pengguna tanpa alasan kuat.
8. Jangan menimpa file yang sudah berisi pekerjaan penting tanpa memeriksa isinya.

## 5. Arsitektur yang Diharapkan

Pisahkan tanggung jawab minimal menjadi:
- API routes/controllers.
- Services/business logic.
- Computer vision camera/inference.
- Tracking dan event counting.
- Database models/repositories.
- Notification rules.
- PDF report generation.
- Frontend pages/components.
- Configuration and logging.

Hindari menaruh seluruh aplikasi di satu file besar.

Struktur referensi (adaptasikan dengan repository):

```text
ecosort-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── cv/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── public/
├── models/
├── storage/
│   ├── snapshots/
│   └── reports/
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

## 6. Functional Requirements

### 6.1 Dashboard Overview
Tampilkan:
- Total detection events pada periode aktif.
- Total per enam class.
- Grafik tren deteksi.
- Distribusi class.
- Status kamera.
- Status model/inference.
- Ringkasan notifikasi terbaru.

Semua angka harus berasal dari API/database, bukan mock/hard-coded setelah integrasi backend tersedia. Jika memakai mock untuk tahap UI awal, beri label jelas dan ganti dengan API sebelum menyatakan fitur selesai.

### 6.2 Live Detection
- Tombol Start Camera dan Stop Camera.
- Tampilkan frame/video dengan bounding box.
- Tampilkan class, confidence, dan track ID bila ada.
- Tampilkan status kamera dan koneksi.
- Tampilkan error state yang informatif.
- Hindari membuat proses capture ganda saat tombol start diklik berkali-kali.
- Pastikan kamera dilepas saat stop dan saat shutdown.

### 6.3 Object Tracking dan Counting
- Integrasikan tracker yang sesuai.
- Jangan menghitung setiap prediksi frame sebagai objek baru.
- Implementasikan event-based counting.
- Untuk MVP, sediakan virtual line yang dapat dikonfigurasi atau aturan track-completion yang terdokumentasi.
- Track ID bersifat sementara, bukan identitas permanen.
- Tangani track yang hilang/occlusion secara wajar.
- Simpan alasan/jenis event counting.

### 6.4 Detection History
- Tabel dengan waktu, class, confidence, track ID, session, dan snapshot bila tersedia.
- Filter tanggal, class, dan confidence.
- Pagination atau limit.
- Detail event dapat dibuka.

### 6.5 Notifications
- Aturan threshold per class pada time window tertentu.
- Cooldown agar notifikasi tidak spam.
- Simpan notifikasi di database.
- Mark as read.
- Notifikasi error kamera/model dapat ditampilkan.
- Jangan mengirim notifikasi berulang pada setiap frame.

### 6.6 PDF Reports
Gunakan ReportLab.
Laporan berisi:
- Judul EcoSort AI.
- Rentang waktu.
- Total event.
- Tabel jumlah per class.
- Grafik tren/distribusi.
- Snapshot representatif jika tersedia.
- Waktu generate dan filter yang digunakan.

Pastikan file report hanya dapat diakses melalui endpoint yang dikontrol backend.

## 7. API Contract Awal

Implementasikan endpoint yang relevan dan dokumentasikan melalui OpenAPI:

| Method | Endpoint | Tujuan |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/dashboard/summary` | Ringkasan |
| GET | `/api/dashboard/charts` | Grafik |
| POST | `/api/camera/start` | Mulai kamera |
| POST | `/api/camera/stop` | Hentikan kamera |
| GET | `/api/camera/status` | Status kamera |
| WS | `/ws/detection` | Live updates |
| GET | `/api/detections` | Riwayat/filter |
| GET | `/api/detections/{id}` | Detail |
| GET | `/api/notifications` | Daftar notifikasi |
| PATCH | `/api/notifications/{id}/read` | Tandai dibaca |
| POST | `/api/reports/generate` | Buat laporan |
| GET | `/api/reports` | Daftar laporan |
| GET | `/api/reports/{id}/download` | Unduh laporan |

Contoh payload live:

```json
{
  "type": "detection_update",
  "timestamp": "2026-11-11T09:30:00+07:00",
  "camera_status": "running",
  "objects": [
    {
      "class_id": 0,
      "class_name": "plastic_bottle",
      "confidence": 0.93,
      "track_id": 12,
      "bbox": [120, 80, 260, 410]
    }
  ]
}
```

Dokumentasikan satuan dan format bbox. Gunakan timestamp ISO 8601 dengan zona waktu yang konsisten.

## 8. Database

Buat model minimal:
- `camera_sessions`
- `detection_events`
- `notifications`
- `reports`

Gunakan primary key, foreign key, timestamp, dan index yang relevan. Simpan event counting, bukan setiap frame prediction, kecuali ada alasan teknis dan retensi yang jelas.

Gunakan migration atau mekanisme schema initialization yang terkontrol. Jangan menghapus database pengguna ketika aplikasi restart.

## 9. Configuration dan Environment

Sediakan `.env.example`, minimal:

```env
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000

DATABASE_URL=sqlite:///./ecosort.db

CAMERA_INDEX=0
MODEL_PATH=./models/best.pt
CONFIDENCE_THRESHOLD=0.40
IMAGE_SIZE=640
MAX_INFERENCE_FPS=15

SNAPSHOT_DIR=./storage/snapshots
REPORT_DIR=./storage/reports
```

Nilai di atas adalah default awal yang dapat disesuaikan, bukan jaminan performa. Jangan commit `.env`, API key, token, atau secret.

Tambahkan validasi startup untuk path model, folder storage, dan konfigurasi kritis.

## 10. UI/UX Direction

Buat dashboard modern, profesional, bersih, dan mudah dipresentasikan:
- Tema visual lingkungan/daur ulang tanpa terlalu dekoratif.
- Sidebar navigasi yang jelas.
- Overview dengan KPI cards dan grafik.
- Live Detection sebagai halaman yang menonjol.
- Warna class konsisten.
- Tabel mudah dipindai.
- Status badge untuk camera/model/connection.
- Empty, loading, success, dan error states.
- Responsive untuk desktop dan tablet.
- Accessibility: label input, kontras memadai, keyboard focus.

Jangan membuat tombol dekoratif yang tidak berfungsi. Jika fitur belum tersedia, tampilkan disabled state dan jelaskan statusnya.

## 11. Error Handling dan Reliability

- Kamera gagal dibuka: kembalikan status error yang aman dan informatif.
- Model tidak ditemukan: jangan pura-pura inference aktif.
- WebSocket putus: UI menunjukkan disconnected dan melakukan reconnect terbatas.
- Database gagal: jangan menyatakan event sudah tersimpan.
- PDF gagal: tandai report failed.
- Pastikan resource kamera dilepas.
- Hindari blocking inference pada event loop FastAPI.
- Logging tidak boleh membocorkan secret.

## 12. Testing dan Definition of Done

Buat test minimal untuk:
- Class mapping.
- Confidence threshold.
- Event counting/deduplication.
- Notification cooldown.
- Database create/read/filter.
- Report generation.
- API health dan endpoint utama.
- Kamera/model unavailable state.

Sebelum menyatakan selesai:
1. Install dependency dari instruksi proyek.
2. Jalankan backend.
3. Jalankan frontend.
4. Jalankan test.
5. Perbaiki error yang dapat direproduksi.
6. Pastikan README berisi langkah menjalankan.
7. Catat fitur yang belum bisa diuji karena tidak ada webcam/model file.

Jangan mengarang hasil test. Laporkan command yang dijalankan dan hasil sebenarnya.

## 13. Development Strategy

Kerjakan dalam milestone kecil:

**Milestone 1 — Foundation**
- Repository inspection.
- App skeleton.
- Configuration.
- Health endpoint.
- Database initialization.
- Basic frontend layout.

**Milestone 2 — Computer Vision**
- Load YOLO model.
- Camera start/stop.
- Detection overlay.
- Status reporting.

**Milestone 3 — Tracking and Persistence**
- Tracker.
- Event counting.
- Camera sessions.
- Detection history.

**Milestone 4 — Dashboard**
- Summary API.
- Charts.
- History filters.

**Milestone 5 — Notifications and Reports**
- Threshold/cooldown rules.
- Notification center.
- PDF generation/download.

**Milestone 6 — Integration and QA**
- End-to-end tests.
- Error states.
- Documentation.
- Demo readiness.

Jangan mencoba mengimplementasikan semua milestone sekaligus tanpa menjalankan dan memvalidasi tiap milestone.

## 14. Expected Deliverables

- Source code frontend dan backend.
- Dependency manifest dan `.env.example`.
- Database models/migrations.
- API documentation.
- Test suite.
- README setup/run.
- Dokumentasi arsitektur dan keputusan teknis.
- UI dashboard yang terhubung ke backend.
- Daftar batasan dan pekerjaan tersisa.

## 15. Instruksi Akhir

Mulai dengan memeriksa repository dan dokumen proyek. Setelah itu:
1. Laporkan ringkasan struktur dan kondisi awal.
2. Usulkan rencana implementasi singkat.
3. Implementasikan Milestone 1 terlebih dahulu.
4. Jalankan test dan laporkan hasil.
5. Tunggu arahan sebelum berpindah ke milestone berikutnya jika perubahan besar atau keputusan produk diperlukan.

Prioritaskan correctness, keterlacakan, maintainability, dan demo yang benar-benar berfungsi di atas tampilan yang hanya terlihat bagus.
