# Ketentuan Tambahan — EcoSort AI
## Aturan Implementasi, Dataset, UI, dan Kolaborasi AI Coding Agent

**Versi:** 1.0  
**Tanggal:** 11 November 2026

Dokumen ini melengkapi PRD, SRS, dan Master Prompt Antigravity. Ketentuan di sini dimaksudkan untuk mencegah implementasi yang tampak selesai tetapi tidak benar-benar bekerja.

---

## 1. Aturan Class dan Dataset

1. Enam class resmi dan urutannya adalah:
   - `plastic_bottle`
   - `plastic_bag`
   - `paper`
   - `cardboard`
   - `metal_can`
   - `glass_bottle`
2. Jangan menambahkan class ketujuh tanpa persetujuan.
3. Jangan memetakan class umum `plastic` menjadi `plastic_bottle` atau `plastic_bag` tanpa inspeksi anotasi.
4. Jangan memetakan class `metal` menjadi `metal_can` tanpa memastikan objeknya memang kaleng.
5. Catat sumber dataset, nama project, version, lisensi, tanggal unduh, dan perubahan label.
6. Simpan dataset mentah secara terpisah dari dataset yang sudah direview.
7. Jangan mengubah dataset Version 1 setelah training tanpa membuat version baru.
8. Simpan `data.yaml` dan daftar class bersama artefak training.
9. Split data berdasarkan sumber/sesi/video bila memungkinkan untuk menghindari data leakage.
10. Jangan menghapus objek sulit hanya demi menaikkan metrik; tandai dan evaluasi secara konsisten.

## 2. Aturan Anotasi

- Satu bounding box untuk satu objek.
- Bounding box mencakup objek yang terlihat, tidak terlalu longgar.
- Jangan menggabungkan beberapa objek menjadi satu box.
- Objek yang tertutup sebagian hanya diberi label jika class masih dapat dikenali.
- Objek sangat kecil/tidak jelas dapat ditandai untuk review sesuai kebijakan anotasi.
- Benda yang bukan bagian dari enam class tidak diberi salah satu class secara paksa.
- Untuk objek komposit, tentukan aturan konsisten. Contoh: label kertas pada botol tidak menjadi objek `paper` terpisah jika label tersebut merupakan bagian dari botol.

## 3. Aturan Kamera dan Computer Vision

1. MVP hanya satu webcam.
2. Device index kamera harus configurable.
3. Hanya boleh ada satu capture worker aktif untuk device yang sama.
4. Selalu release camera resource pada stop dan shutdown.
5. Inference tidak boleh memblokir event loop API.
6. Batasi FPS inference melalui konfigurasi.
7. Frame yang dikirim ke browser harus menggunakan format dan resolusi yang terdokumentasi.
8. Confidence threshold harus configurable.
9. Jangan menganggap satu prediction pada satu frame sebagai event baru yang harus disimpan.
10. Tracking ID hanya valid dalam konteks tracker/session dan dapat berubah.
11. Counting harus event-based dan memiliki aturan deduplication.
12. Untuk virtual line, dokumentasikan arah crossing dan kondisi kapan objek dihitung.
13. Jangan menghitung objek yang bergerak bolak-balik melewati garis sebagai objek baru tanpa aturan eksplisit.

## 4. Aturan Database dan Retensi

- Gunakan timestamp yang konsisten; simpan timezone-aware timestamp atau UTC dan konversi pada tampilan.
- Simpan detection event yang relevan, bukan semua frame secara default.
- Snapshot bersifat opsional dan harus memiliki kebijakan penyimpanan.
- Hindari menyimpan frame tanpa batas.
- Sediakan konfigurasi folder penyimpanan.
- Jangan menghapus database saat startup.
- Gunakan foreign key untuk relasi.
- Gunakan index untuk query berdasarkan waktu, class, dan session.
- Tangani kegagalan simpan secara eksplisit; jangan mengirim status sukses palsu ke UI.

## 5. Aturan Notifikasi

1. Setiap rule harus memiliki key atau identitas.
2. Threshold harus dikaitkan dengan time window.
3. Cooldown harus mencegah notifikasi berulang.
4. Notifikasi baru dibuat ketika kondisi berubah atau aturan menyatakan perlu.
5. Status read/unread harus tersimpan.
6. Notifikasi error sistem harus dibedakan dari notifikasi volume sampah.
7. Jangan mengirim email, SMS, atau push notification pada MVP kecuali diminta dan dikonfigurasi.

## 6. Aturan PDF

- PDF harus dibuat dari data database sesuai periode filter.
- Cantumkan periode, waktu generate, dan parameter filter.
- Angka di PDF harus dapat ditelusuri ke query/API.
- Jika data kosong, buat laporan yang menyatakan tidak ada event pada periode itu.
- Jangan menampilkan snapshot jika file tidak tersedia atau tidak boleh diakses.
- Pastikan nama file aman dan tidak berasal langsung dari input bebas pengguna.

## 7. Aturan UI/UX

1. Utamakan dashboard yang rapi dan presentable.
2. Jangan gunakan angka statistik palsu setelah API tersedia.
3. Mock data hanya untuk prototyping dan harus diberi label.
4. Setiap tombol harus punya aksi nyata atau disabled state dengan penjelasan.
5. Tampilkan status kamera, model, database, dan WebSocket secara jujur.
6. Semua tabel harus punya empty state dan loading state.
7. Semua operasi async harus menampilkan error state.
8. Warna class konsisten di seluruh halaman.
9. Jangan hanya membedakan class melalui warna; sertakan nama class.
10. Pastikan layout tetap dapat digunakan pada resolusi desktop dan tablet.
11. Hindari animasi berlebihan yang mengganggu live monitoring.

## 8. Keamanan dan Privasi

- Jangan commit `.env`, API key Roboflow, token, password, atau secret.
- Sediakan `.env.example` dengan placeholder.
- Validasi input API.
- Batasi akses file report dan snapshot melalui backend.
- Jangan membuka port kamera atau server ke internet tanpa autentikasi dan firewall.
- Jangan menampilkan absolute path server kepada browser.
- Jangan menyimpan gambar sensitif jika tidak dibutuhkan.
- Jika autentikasi belum dibuat, dokumentasikan bahwa aplikasi hanya untuk lingkungan lokal/terkontrol.

## 9. Aturan Kualitas Kode

1. Gunakan modul dengan tanggung jawab jelas.
2. Hindari satu file yang memuat seluruh API, inference, database, dan report.
3. Gunakan type hints pada fungsi penting.
4. Gunakan Pydantic schema untuk kontrak API.
5. Gunakan logging, bukan `print()` untuk logging aplikasi.
6. Jangan menelan exception tanpa logging dan penanganan.
7. Jangan menambahkan dependency tanpa alasan.
8. Pin atau dokumentasikan versi dependency yang diuji.
9. Buat test untuk logic yang kritis.
10. Jangan mengklaim test berhasil jika tidak dijalankan.

## 10. Aturan untuk Antigravity / AI Coding Agent

- Inspeksi repository sebelum mengedit.
- Baca semua dokumen requirement.
- Jangan menghapus atau menimpa pekerjaan yang sudah ada tanpa pemeriksaan.
- Jangan membuat file konfigurasi duplikat jika sudah ada.
- Sebelum perubahan besar, jelaskan rencana dan file yang akan disentuh.
- Implementasikan per milestone.
- Setelah perubahan, jalankan test atau minimal lint/type check yang tersedia.
- Laporkan file yang dibuat/diubah, command yang dijalankan, hasil test, dan batasan yang belum diuji.
- Jangan mengarang output terminal, hasil metrik, atau status integrasi.
- Jangan membuat API key atau credential palsu seolah-olah valid.
- Jangan mengunduh model/dataset besar atau mengubah dataset tanpa persetujuan eksplisit.
- Jika spesifikasi tidak cukup, pilih default paling aman, dokumentasikan asumsi, dan tanyakan hanya untuk keputusan yang benar-benar memblokir pekerjaan.

## 11. Definition of Done Umum

Sebuah fitur hanya boleh dinyatakan selesai jika:
- Implementasi tersedia.
- Jalur sukses diuji.
- Jalur error utama dipertimbangkan.
- UI menampilkan status yang sesuai.
- Dokumentasi diperbarui jika cara penggunaan berubah.
- Tidak ada secret yang masuk repository.
- Tidak ada mock yang disamarkan sebagai data aktual.

## 12. Keputusan yang Masih Terbuka

Keputusan berikut perlu ditetapkan sebelum deployment final:
- Sistem operasi dan spesifikasi perangkat.
- Model webcam, resolusi, dan posisi pemasangan.
- Apakah kamera tersambung ke mesin backend yang sama.
- Model YOLO final dan versi dependency.
- Definisi final event counting: virtual line crossing atau track completion.
- Ambang confidence per class.
- Ambang notifikasi dan cooldown.
- Kebijakan retensi snapshot dan laporan.
- Autentikasi dan target deployment.
