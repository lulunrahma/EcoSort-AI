# Folder Model — EcoSort AI

Folder ini digunakan untuk menyimpan bobot model YOLO yang telah dilatih (*trained weights*).

## File Model
- **Lokasi Default:** `models/best.pt`
- Jika file `models/best.pt` belum ada (karena proses training masih berjalan), sistem backend EcoSort AI akan menampilkan status:
  - `Model Status: Training in Progress / Not Loaded Yet`
  - Web dashboard tetap dapat dibuka dengan aman tanpa mengalami crash.
  - Sedia mode simulasi/demo di Settings untuk menguji alur bounding box, tracking, WebSocket, dan pencatatan database sebelum model selesai dilatih.
- Setelah proses training selesai, letakkan file `best.pt` di folder ini, lalu restart backend atau perbarui konfigurasi di menu Settings.

