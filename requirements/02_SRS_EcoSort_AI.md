# Software Requirements Specification (SRS)
## EcoSort AI

**Versi dokumen:** 1.0  
**Tanggal:** 11 November 2026  
**Status:** Draft baseline untuk pengembangan

---

## 1. Pendahuluan

### 1.1 Tujuan
Dokumen ini menetapkan kebutuhan fungsional dan nonfungsional EcoSort AI agar dapat digunakan sebagai acuan implementasi, pengujian, dan penerimaan sistem.

### 1.2 Ruang Lingkup
EcoSort AI adalah aplikasi web untuk deteksi dan pemantauan enam kategori sampah menggunakan satu webcam dan model object detection YOLO. Sistem mencakup live view, tracking, pencatatan, analytics, notifikasi, dan laporan PDF.

### 1.3 Definisi
- **Detection:** hasil prediksi objek pada satu frame.
- **Track:** identitas sementara objek yang dipertahankan lintas frame.
- **Detection event:** kejadian yang disimpan/dihitung, bukan setiap prediksi frame.
- **Confidence:** skor keyakinan model.
- **Version dataset:** snapshot dataset dan konfigurasi preprocessing/augmentation.
- **MVP:** versi minimum yang memenuhi ruang lingkup awal.

## 2. Gambaran Sistem

### 2.1 Arsitektur Logis
1. Webcam mengirim frame ke proses capture.
2. Modul inference menjalankan model YOLO.
3. Modul tracking menghubungkan deteksi antar-frame.
4. Modul event menentukan kapan objek dicatat/dihitung.
5. Backend menyimpan event dan metadata.
6. WebSocket mengirim pembaruan live ke browser.
7. Frontend menampilkan video, statistik, riwayat, dan notifikasi.
8. Modul report menghasilkan PDF berdasarkan data tersimpan.

### 2.2 Komponen
- Frontend web dashboard.
- Backend API berbasis FastAPI.
- Computer Vision worker berbasis Python, OpenCV, Ultralytics.
- Object tracker, misalnya ByteTrack melalui integrasi yang didukung.
- Database SQLite untuk pengembangan awal atau PostgreSQL untuk deployment.
- Penyimpanan snapshot dan file laporan.
- Roboflow untuk pengelolaan dataset.

### 2.3 Batas Sistem
- MVP hanya mendukung satu kamera.
- Sistem tidak mengendalikan conveyor atau aktuator.
- Sistem tidak menjamin identifikasi material bila objek tidak terlihat jelas.
- Internet tidak harus tersedia untuk inference lokal setelah model dan dependency terpasang; fitur yang memerlukan layanan eksternal tetap bergantung koneksi.

## 3. Kebutuhan Fungsional

Prioritas: **MUST** wajib untuk MVP, **SHOULD** diharapkan, **COULD** opsional.

### FR-01 — Konfigurasi Model (MUST)
Sistem harus dapat memuat file model YOLO dari konfigurasi.
- Path model tidak boleh ditulis tersebar di banyak modul.
- Sistem harus memeriksa keberadaan file model saat startup.
- Sistem menampilkan status model: ready atau error.
- Nama class model harus divalidasi terhadap enam class yang disepakati.

### FR-02 — Capture Kamera (MUST)
- Sistem harus dapat memulai dan menghentikan satu webcam.
- Indeks/device kamera dapat dikonfigurasi.
- Sistem menampilkan status kamera.
- Jika kamera gagal dibuka, sistem mengembalikan error yang informatif.
- Proses capture tidak boleh membuat lebih dari satu worker aktif untuk kamera yang sama.

### FR-03 — Object Detection (MUST)
- Sistem memproses frame menggunakan model YOLO.
- Sistem menampilkan bounding box, class, dan confidence.
- Sistem menyediakan confidence threshold yang dapat dikonfigurasi.
- Sistem mengabaikan hasil di bawah threshold.
- Sistem mempertahankan urutan class yang sama dengan `data.yaml`/model.

### FR-04 — Object Tracking (MUST)
- Sistem menghubungkan deteksi antar-frame menggunakan tracker.
- Sistem menampilkan track ID bila tersedia.
- Sistem tidak menghitung satu objek pada setiap frame.
- Event counting harus menggunakan aturan yang terdokumentasi, misalnya crossing virtual line atau track completion.
- Sistem menangani track yang hilang dengan toleransi tracker; track ID tidak dianggap sebagai identitas permanen lintas sesi.

### FR-05 — Live Dashboard (MUST)
- Menampilkan stream/frame hasil anotasi.
- Menampilkan status kamera dan model.
- Menampilkan jumlah deteksi/event pada sesi aktif.
- Menampilkan label dan confidence.
- Menampilkan pesan saat kamera berhenti atau koneksi WebSocket terputus.

### FR-06 — Persistensi Detection Event (MUST)
Setiap event yang disimpan minimal memiliki:
- ID.
- Timestamp.
- Class name dan class ID.
- Confidence.
- Track ID jika tersedia.
- Camera session ID.
- Snapshot path/URL jika disimpan.
- Informasi sumber/inference yang diperlukan untuk audit.

Simpan event counting terpisah dari raw frame predictions agar database tidak membengkak.

### FR-07 — Riwayat dan Filter (MUST)
- Pengguna dapat melihat daftar event.
- Filter berdasarkan rentang tanggal, class, dan confidence.
- Hasil diurutkan berdasarkan waktu terbaru secara default.
- Daftar menggunakan pagination atau mekanisme pembatasan hasil.

### FR-08 — Dashboard Analytics (MUST)
- Total event dalam periode terpilih.
- Total per class.
- Grafik tren waktu.
- Ringkasan sesi kamera.
- Statistik dihitung dari data tersimpan, bukan angka hard-coded.

### FR-09 — Notifikasi (SHOULD)
- Sistem membuat notifikasi ketika aturan terpenuhi.
- Aturan minimal mendukung ambang jumlah class pada jendela waktu tertentu.
- Setiap aturan memiliki cooldown.
- Notifikasi tersimpan dan dapat ditandai telah dibaca.
- Notifikasi kamera/model error dapat dibuat sebagai event sistem.

### FR-10 — PDF Report (SHOULD)
- Pengguna dapat memilih periode laporan.
- Sistem membuat PDF berisi ringkasan, tabel per class, grafik, dan metadata periode.
- Sistem menyimpan metadata laporan dan lokasi file.
- Pengguna dapat mengunduh laporan yang telah dibuat.
- Kegagalan pembuatan PDF harus menghasilkan pesan error yang jelas.

### FR-11 — Konfigurasi Aplikasi (MUST)
Konfigurasi minimal:
- Camera device index.
- Model path.
- Confidence threshold.
- Inference image size.
- Frame processing interval/FPS limit.
- Database URL/path.
- Snapshot storage path.
- Notification thresholds/cooldown.

Nilai konfigurasi harus dipusatkan di environment/config file dan tidak di-hardcode di banyak tempat.

### FR-12 — Audit dan Logging (MUST)
- Sistem mencatat startup, shutdown, error kamera, error model, dan error database.
- Log tidak boleh menyimpan API key atau secret.
- Error yang ditampilkan ke UI tidak boleh membocorkan stack trace atau secret.

## 4. Kebutuhan Antarmuka

### 4.1 Halaman
1. Overview/Dashboard.
2. Live Detection.
3. Analytics.
4. Detection History.
5. Notifications.
6. Reports.
7. Settings (minimal konfigurasi yang aman).

### 4.2 API yang Disarankan

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/api/health` | Status backend |
| GET | `/api/dashboard/summary` | Ringkasan statistik |
| GET | `/api/dashboard/charts` | Data grafik |
| POST | `/api/camera/start` | Mulai kamera |
| POST | `/api/camera/stop` | Hentikan kamera |
| GET | `/api/camera/status` | Status kamera |
| WS | `/ws/detection` | Update live detection |
| GET | `/api/detections` | Daftar dan filter event |
| GET | `/api/detections/{id}` | Detail event |
| GET | `/api/notifications` | Daftar notifikasi |
| PATCH | `/api/notifications/{id}/read` | Tandai dibaca |
| POST | `/api/reports/generate` | Generate PDF |
| GET | `/api/reports` | Daftar laporan |
| GET | `/api/reports/{id}/download` | Download PDF |

### 4.3 Contoh Payload WebSocket

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
  ],
  "session_counts": {
    "plastic_bottle": 1,
    "plastic_bag": 0,
    "paper": 0,
    "cardboard": 0,
    "metal_can": 0,
    "glass_bottle": 0
  }
}
```

Payload di atas adalah contoh kontrak. Format koordinat bounding box harus didokumentasikan dan konsisten, misalnya `[x1, y1, x2, y2]` dalam pixel frame asli.

## 5. Model Data

### 5.1 `camera_sessions`
- `id` — primary key.
- `started_at`.
- `ended_at`, nullable.
- `status`.
- `camera_name` atau device identifier.
- `notes`, nullable.

### 5.2 `detection_events`
- `id` — primary key.
- `camera_session_id` — foreign key ke `camera_sessions.id`.
- `detected_at`.
- `class_id`.
- `class_name`.
- `confidence`.
- `track_id`, nullable.
- `bbox_json`, nullable.
- `snapshot_path`, nullable.
- `event_type`, misalnya `line_crossing` atau `track_completed`.

### 5.3 `notifications`
- `id`.
- `created_at`.
- `type`.
- `title`.
- `message`.
- `is_read`.
- `related_detection_id`, nullable.
- `rule_key`, nullable.

### 5.4 `reports`
- `id`.
- `created_at`.
- `period_start`.
- `period_end`.
- `file_path`.
- `status`.
- `parameters_json`, nullable.

Gunakan index pada timestamp, class, dan foreign key yang sering dipakai untuk filter.

## 6. Kebutuhan Nonfungsional

### NFR-01 — Performa
- Sistem harus membatasi FPS pemrosesan agar UI dan database tidak terbebani.
- Target FPS dan latensi harus diukur pada perangkat aktual.
- Proses inference tidak boleh memblokir event loop API.
- Video live boleh menggunakan frame sampling bila diperlukan.

### NFR-02 — Keandalan
- Kamera dapat dihentikan dengan aman.
- Resource kamera dilepas saat stop/shutdown.
- Error satu frame tidak boleh otomatis mematikan seluruh backend.
- Kegagalan database harus dicatat dan ditampilkan secara terkendali.

### NFR-03 — Keamanan
- Secret/API key disimpan di environment variable.
- Batasi akses ke file snapshot dan laporan.
- Validasi parameter filter dan request.
- Terapkan autentikasi sebelum deployment yang dapat diakses jaringan publik.
- Jangan membuka webcam atau server ke internet tanpa kontrol akses.

### NFR-04 — Maintainability
- Pisahkan modul API, CV, tracking, database, report, dan frontend.
- Gunakan type hints dan validasi skema.
- Hindari duplikasi aturan class.
- Dokumentasikan setup dan cara menjalankan aplikasi.

### NFR-05 — Usability
- UI menampilkan status loading, empty, success, dan error.
- Nama class mudah dibaca.
- Warna class konsisten dan selalu disertai teks.
- Filter dan rentang waktu mudah dipahami.

### NFR-06 — Portability
- Dependency memiliki versi yang dipin atau rentang kompatibilitas yang terdokumentasi.
- Aplikasi dapat dijalankan melalui instruksi setup yang konsisten.
- Path file tidak bergantung pada working directory yang tidak terdokumentasi.

## 7. Validasi dan Kriteria Penerimaan

| ID | Kriteria | Cara uji |
|---|---|---|
| AT-01 | Model berhasil dimuat | Jalankan startup dan cek status |
| AT-02 | Webcam dapat start/stop | Uji beberapa kali dan cek resource |
| AT-03 | Enam class dikenali sesuai mapping | Uji gambar berlabel |
| AT-04 | Bounding box tampil | Uji live view |
| AT-05 | Objek tidak dihitung setiap frame | Letakkan satu objek selama beberapa detik |
| AT-06 | Event tersimpan | Cek database setelah event |
| AT-07 | Filter riwayat bekerja | Filter tanggal dan class |
| AT-08 | Grafik sesuai database | Bandingkan query dan grafik |
| AT-09 | Cooldown notifikasi bekerja | Simulasikan ambang berulang |
| AT-10 | PDF berhasil diunduh | Generate dan buka PDF |
| AT-11 | Error kamera terlihat | Cabut/tutup kamera saat berjalan |
| AT-12 | Secret tidak muncul di log | Audit log dan repository |

## 8. Penanganan Error

| Kondisi | Perilaku |
|---|---|
| Kamera tidak tersedia | Status error dan instruksi cek device |
| Model file tidak ditemukan | Gagal startup CV dengan pesan konfigurasi |
| WebSocket putus | UI menampilkan disconnected dan mencoba reconnect terbatas |
| Database tidak tersedia | Catat error; jangan mengklaim event tersimpan |
| PDF gagal dibuat | Status report failed dan alasan aman |
| Tidak ada deteksi | Tampilkan empty state, bukan error |

## 9. Pengujian

- Unit test: class mapping, threshold, event counting, cooldown.
- Integration test: API dengan database test.
- CV test: gambar statis dan video rekaman.
- End-to-end: start kamera, deteksi, simpan event, lihat dashboard, generate PDF.
- Dataset evaluation: test split yang tidak digunakan saat training/tuning.
- Robustness: variasi cahaya, occlusion, orientasi, objek bertumpuk, dan latar.

## 10. Asumsi yang Harus Dikonfirmasi

- Sistem operasi dan spesifikasi komputer.
- Jenis webcam dan resolusinya.
- Apakah backend dan webcam berjalan pada komputer yang sama.
- Apakah perlu login untuk MVP.
- Kebijakan retensi snapshot.
- Target deployment lokal atau server.
- Definisi operasional hitungan: crossing virtual line atau track completion.
