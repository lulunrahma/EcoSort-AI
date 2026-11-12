# Product Requirements Document (PRD)
## EcoSort AI — Web Dashboard untuk Deteksi dan Pemantauan Sampah

**Versi dokumen:** 1.0  
**Tanggal:** 11 November 2026  
**Status:** Draft baseline untuk pengembangan  
**Bahasa:** Indonesia

---

## 1. Ringkasan Produk

EcoSort AI adalah aplikasi web berbasis Computer Vision untuk mendeteksi, mengklasifikasikan, menghitung, dan memantau objek sampah melalui satu webcam yang ditempatkan di meja pemilahan. Model deteksi menggunakan YOLO dan dataset dikelola melalui Roboflow.

Aplikasi menyediakan dashboard analitik, tampilan deteksi langsung, object tracking, riwayat deteksi, notifikasi otomatis, dan pembuatan laporan PDF.

## 2. Latar Belakang dan Masalah

Pemilahan sampah secara manual membutuhkan perhatian operator dan pencatatan yang konsisten. Penghitungan objek secara manual berisiko tidak konsisten, sulit ditelusuri, dan tidak selalu menyediakan ringkasan data yang cepat.

EcoSort AI ditujukan untuk membantu proses pemantauan tersebut melalui kamera dan sistem deteksi otomatis. Sistem merupakan alat bantu pemantauan, bukan pengganti keputusan manusia untuk kasus objek yang ambigu.

## 3. Tujuan Produk

1. Mendeteksi enam kategori sampah dari input webcam.
2. Menampilkan hasil deteksi secara langsung pada dashboard.
3. Melacak objek agar objek yang sama tidak dihitung berulang kali pada setiap frame.
4. Menyimpan hasil deteksi dan snapshot yang relevan.
5. Menyajikan statistik dan tren deteksi.
6. Mengirim notifikasi berdasarkan aturan yang dapat dikonfigurasi.
7. Menghasilkan laporan PDF berdasarkan rentang waktu.

## 4. Pengguna dan Peran

### 4.1 Operator
- Memulai dan menghentikan sesi kamera.
- Memantau hasil deteksi.
- Melihat riwayat dan notifikasi.
- Mengunduh laporan.

### 4.2 Administrator
- Mengelola konfigurasi kamera dan ambang notifikasi.
- Mengelola konfigurasi model.
- Mengakses seluruh riwayat dan laporan.
- Mengelola akun jika autentikasi multi-pengguna diterapkan.

Untuk MVP, sistem dapat dimulai dengan satu peran operator/admin sederhana. Hak akses terpisah dapat ditambahkan kemudian.

## 5. Ruang Lingkup MVP

### Termasuk
- Satu webcam.
- Deteksi object detection berbasis YOLO.
- Enam kelas sampah.
- Live detection pada web dashboard.
- Object tracking dan penghitungan berbasis track/event.
- Penyimpanan riwayat deteksi ke database.
- Dashboard ringkasan dan grafik.
- Notifikasi berbasis aturan sederhana.
- Pembuatan dan unduh laporan PDF.
- Pengaturan ambang confidence dan interval notifikasi.

### Tidak termasuk pada MVP
- Dukungan multi-kamera.
- Integrasi perangkat IoT atau aktuator pemilah otomatis.
- Penimbangan massa sampah.
- Prediksi nilai ekonomi atau daur ulang.
- Aplikasi mobile native.
- Pengenalan material tingkat lanjut seperti jenis resin plastik.
- Klaim bahwa sistem dapat menentukan kelayakan daur ulang secara sempurna.

## 6. Kategori Deteksi

| ID | Class | Contoh |
|---:|---|---|
| 0 | `plastic_bottle` | Botol minuman plastik |
| 1 | `plastic_bag` | Kantong plastik |
| 2 | `paper` | Kertas dan koran |
| 3 | `cardboard` | Kardus dan karton |
| 4 | `metal_can` | Kaleng minuman/makanan |
| 5 | `glass_bottle` | Botol kaca |

Urutan class di atas harus disamakan dengan urutan class pada `data.yaml` dan model terlatih. Class yang ambigu atau tidak termasuk daftar tidak boleh dipaksakan menjadi salah satu dari enam class.

## 7. Dataset dan Model

- Sumber dataset: hybrid, yaitu dataset publik Roboflow Universe dan foto yang dikumpulkan sendiri.
- Project Roboflow: `ecosort-ai`.
- Project type: Object Detection.
- Target image size: 640 × 640.
- Pembagian awal: 70% train, 20% validation, 10% test.
- Dataset Version 1 menjadi baseline eksperimen.
- Model awal: YOLO11n atau varian Ultralytics yang dipilih dan dikunci versinya.
- Dataset publik wajib diperiksa lisensi, label, kualitas, dan kesesuaian kelasnya.
- Data dari video/sesi yang sama harus dikelompokkan agar tidak terjadi data leakage antar-split.

Target jumlah data adalah sasaran perencanaan, bukan jaminan performa. Keseimbangan kelas dan kualitas anotasi lebih penting daripada jumlah gambar semata.

## 8. Fitur dan Kebutuhan Produk

### 8.1 Dashboard Analytics
Menampilkan:
- Total objek terdeteksi pada periode terpilih.
- Jumlah per class.
- Distribusi class.
- Tren deteksi berdasarkan waktu.
- Status kamera dan model.
- Ringkasan notifikasi.

### 8.2 Real-time Webcam Detection
- Operator dapat memulai dan menghentikan kamera.
- Video dan bounding box ditampilkan pada dashboard.
- Label class dan confidence ditampilkan.
- Status kamera dan status model terlihat jelas.
- Kegagalan kamera ditampilkan sebagai pesan yang dapat ditindaklanjuti.

### 8.3 Object Tracking
- Sistem menggunakan tracker untuk mempertahankan identitas objek lintas frame.
- Satu track tidak boleh dihitung sebagai objek baru pada setiap frame.
- Penghitungan utama dilakukan melalui aturan event, misalnya saat objek melewati garis virtual atau saat track dinyatakan selesai.
- Track ID bersifat sementara dan dapat berubah setelah occlusion atau kehilangan deteksi.

### 8.4 Riwayat Deteksi
Menyimpan waktu, class, confidence, track ID jika ada, sesi kamera, dan referensi snapshot jika tersedia. Pengguna dapat memfilter riwayat berdasarkan tanggal, class, dan confidence.

### 8.5 Notifikasi Otomatis
Notifikasi dibuat berdasarkan aturan, misalnya:
- Jumlah class tertentu melewati ambang pada periode tertentu.
- Kamera terputus.
- Model atau inference mengalami error.

Notifikasi harus memiliki cooldown agar tidak berulang pada setiap frame.

### 8.6 Laporan PDF
Laporan memuat:
- Judul dan periode laporan.
- Ringkasan total deteksi.
- Rekap per class.
- Grafik tren.
- Contoh snapshot jika tersedia.
- Waktu pembuatan laporan dan parameter filter.

## 9. Alur Pengguna Utama

1. Operator membuka dashboard.
2. Operator memulai sesi kamera.
3. Backend membaca frame dan menjalankan inference.
4. Sistem melakukan tracking dan menghasilkan event deteksi.
5. Hasil live dikirim ke browser.
6. Event yang memenuhi aturan disimpan ke database.
7. Dashboard memperbarui statistik.
8. Sistem membuat notifikasi bila aturan terpenuhi.
9. Operator membuka riwayat atau membuat laporan PDF.

## 10. Prinsip UX dan Desain

- Dashboard harus mudah dibaca dari jarak kerja normal.
- Status kamera, model, dan koneksi harus terlihat.
- Gunakan warna class yang konsisten pada bounding box, legenda, tabel, dan grafik.
- Jangan hanya mengandalkan warna untuk membedakan class; tampilkan teks.
- Tampilkan waktu dan zona waktu secara konsisten.
- Berikan loading, empty state, error state, dan konfirmasi tindakan.
- Layout responsif untuk desktop dan tablet.

## 11. Indikator Keberhasilan

MVP dianggap berhasil bila:
- Enam class tampil konsisten dengan model.
- Operator dapat menjalankan satu webcam dari dashboard.
- Bounding box dan label tampil pada live view.
- Tracking tidak menambah hitungan pada setiap frame untuk objek yang sama.
- Riwayat dapat disimpan dan difilter.
- Grafik dashboard dihitung dari data database.
- Notifikasi memiliki cooldown.
- PDF dapat dibuat dan diunduh.
- Error kamera/model ditampilkan secara jelas.

Nilai precision, recall, mAP, dan FPS harus diukur pada perangkat dan dataset uji yang terdokumentasi. Jangan menyatakan target metrik sebagai hasil aktual sebelum pengujian.

## 12. Risiko dan Mitigasi

| Risiko | Mitigasi |
|---|---|
| Dataset publik tidak sesuai kondisi meja | Tambahkan foto kamera sendiri |
| Class tertukar | Panduan anotasi dan audit confusion matrix |
| Objek dihitung berkali-kali | Tracking dan event-based counting |
| Kamera terputus | Reconnect terbatas dan status error |
| Performa lambat | Uji model kecil, resolusi, dan frame sampling |
| Kebocoran data train/test | Split berdasarkan sesi/video sumber |
| Lisensi dataset tidak sesuai | Verifikasi lisensi dan simpan atribusi |

## 13. Asumsi dan Keputusan yang Belum Dikunci

- Satu webcam lokal pada satu meja pemilahan.
- Satu pengguna/operator untuk MVP.
- Backend berjalan pada komputer yang memiliki akses ke webcam.
- Database awal dapat menggunakan SQLite; PostgreSQL dapat dipakai saat deployment multi-user.
- Detail OS, jenis kamera, spesifikasi GPU, autentikasi, retensi snapshot, dan deployment masih perlu dikonfirmasi.
- Sistem tidak mengendalikan mesin pemilah fisik.

## 14. Rencana Tahapan

1. Setup project Roboflow dan dataset Version 1.
2. Training dan evaluasi baseline YOLO.
3. Implementasi pipeline webcam, inference, dan tracking.
4. Backend API, database, dan WebSocket.
5. Frontend dashboard dan live view.
6. Notifikasi, PDF, integrasi, dan pengujian.
