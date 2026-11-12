from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.services.detection_service import DetectionService
from backend.app.services.notification_service import NotificationService
from backend.app.services.rca_service import RCAService
from backend.app.core.config import OFFICIAL_CLASSES, MACRO_CATEGORIES, MACRO_CATEGORY_META, settings
from backend.app.cv.camera import camera_manager

class ChatService:
    @classmethod
    def generate_reply(cls, db: Session, user_message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Generates an intelligent assistant reply based on EcoSort AI domain knowledge,
        live system metrics, macro classification, and RCA diagnostics.
        """
        msg_lower = user_message.strip().lower()
        
        # Gather live system context from DB & Camera
        summary = DetectionService.get_summary(db)
        total_det = summary["total_detections"]
        macro_counts = summary["macro_counts"]
        class_counts = {c.class_name: c.count for c in summary["class_counts"]}
        camera_status = camera_manager.status
        model_status = camera_manager.detector.status
        unread_notifs = len(NotificationService.get_notifications(db, unread_only=True))

        reply = ""
        suggested_actions = []

        # 1. Kategori Makro / Pilahan Sampah (Organik, Anorganik, Berbahaya)
        if any(w in msg_lower for w in ["organik", "anorganik", "berbahaya", "kategori", "pilah", "masuk mana", "jenis sampah"]):
            reply = (
                "♻️ **Panduan Pengelompokan & Pemilahan Sampah EcoSort AI:**\n\n"
                "Sesuai regulasi sistem, 6 kelas deteksi dikelompokkan ke dalam 3 Kategori Utama:\n\n"
                "1. **Anorganik (Plastik & Kaca):**\n"
                "   - 🧴 `plastic_bottle` (Botol Plastik)\n"
                "   - 🛍️ `plastic_bag` (Kantong Kresek/Kemasan Plastik)\n"
                "   - 🍾 `glass_bottle` (Botol Kaca Minuman/Saus)\n"
                "   *Penanganan:* Kumpulkan terpisah, bilas sisa cairan, dan salurkan ke industri daur ulang polimer/silika.\n\n"
                "2. **Organik (Serat Selulosa Terurai):**\n"
                "   - 📄 `paper` (Kertas HVS, Koran, Dokumen)\n"
                "   - 📦 `cardboard` (Kardus & Karton Kemasan)\n"
                "   *Penanganan:* Pastikan tetap kering. Daur ulang menjadi bubur kertas (pulp) atau kompos terkontrol.\n\n"
                "3. **Berbahaya (Logam / B3):**\n"
                "   - ⚠️ `metal_can` (Kaleng Minuman, Kaleng Cat/Aerosol)\n"
                "   *Penanganan:* Pisahkan ke wadah khusus bertanda **BERBAHAYA (Warna Ungu/Merah)**. Gunakan APD dan jauhkan dari sumber api karena risiko tekanan gas atau tepi tajam!"
            )
            suggested_actions = [
                "Berapa jumlah sampah berbahaya saat ini?",
                "Tampilkan statistik sampah organik",
                "Bagaimana analisis RCA kaleng logam?"
            ]

        # 2. Statistik & Data Terkini
        elif any(w in msg_lower for w in ["statistik", "berapa", "jumlah", "total", "hitung", "terdeteksi", "data sekarang"]):
            reply = (
                f"📊 **Statistik Live Monitoring Pemilahan Sampah:**\n\n"
                f"• **Total Deteksi Tersimpan:** **{total_det}** objek\n\n"
                f"**Rekap Berdasarkan Kategori Makro:**\n"
                f"• 🧴 **Anorganik:** **{macro_counts.get('Anorganik', 0)}** objek (Botol Plastik, Kantong Plastik, Botol Kaca)\n"
                f"• 🍃 **Organik:** **{macro_counts.get('Organik', 0)}** objek (Kertas & Kardus)\n"
                f"• ⚠️ **Berbahaya:** **{macro_counts.get('Berbahaya', 0)}** objek (Kaleng Logam / Metal Can)\n\n"
                f"**Rincian 6 Kelas Resmi:**\n"
                f"- `plastic_bottle`: {class_counts.get('plastic_bottle', 0)}\n"
                f"- `plastic_bag`: {class_counts.get('plastic_bag', 0)}\n"
                f"- `paper`: {class_counts.get('paper', 0)}\n"
                f"- `cardboard`: {class_counts.get('cardboard', 0)}\n"
                f"- `metal_can`: {class_counts.get('metal_can', 0)}\n"
                f"- `glass_bottle`: {class_counts.get('glass_bottle', 0)}\n\n"
                f"• **Status Kamera:** `{camera_status.upper()}` | **Status Model:** `{model_status.upper()}`\n"
                f"• **Notifikasi Belum Dibaca:** {unread_notifs} alert."
            )
            suggested_actions = [
                "Buka Analisis Akar Masalah (RCA)",
                "Bagaimana cara unduh laporan PDF?",
                "Pilah botol plastik masuk mana?"
            ]

        # 3. Root Cause Analysis (RCA)
        elif any(w in msg_lower for w in ["rca", "akar masalah", "root cause", "fishbone", "ishikawa", "5 whys", "anomali"]):
            rca_data = RCAService.get_all_diagnostics(db)
            active_cnt = rca_data["summary"]["active"]
            reply = (
                f"🔍 **Root Cause Analysis (RCA) — Pemantauan Meja Pemilahan:**\n\n"
                f"Sistem memiliki modul RCA otomatis untuk mendeteksi sumber masalah operasional, "
                f"kontaminasi limbah berbahaya, dan hambatan alur konveyor.\n\n"
                f"• **Status Anomali Aktif:** **{active_cnt} kasus** memerlukan perhatian.\n\n"
                f"**Topik RCA Utama:**\n"
                f"1. **RCA-001 [Berbahaya]:** Lonjakan Sampah Logam & Kaleng — Mengapa kaleng B3 masuk ke jalur sortir umum dan bagaimana memasang separator magnetik di hulu.\n"
                f"2. **RCA-002 [Anorganik]:** Penumpukan Plastik Fleksibel — Mencegah kantong kresek melilit poros roller konveyor.\n"
                f"3. **RCA-003 [Organik]:** Kontaminasi Cairan pada Kertas/Kardus — Mencegah rusaknya serat daur ulang pulp.\n"
                f"4. **RCA-004 [Sistem]:** Occlusion & Tracking Jitter — Menangani penumpukan objek berlebih.\n\n"
                f"💡 Anda dapat membuka tab **RCA Diagnostics** di sidebar untuk melihat diagram 5-Whys dan matriks Fishbone Ishikawa lengkap!"
            )
            suggested_actions = [
                "Detail RCA kaleng berbahaya",
                "Apa itu metode 5-Whys?",
                "Tampilkan total deteksi"
            ]

        # 4. Model Training & Dataset Help
        elif any(w in msg_lower for w in ["training", "latih", "model", "dataset", "best.pt", "roboflow", "yolo"]):
            reply = (
                "🤖 **Panduan Model & Dataset EcoSort AI:**\n\n"
                "• **Status Model Saat Ini:** `" + model_status.upper() + "`\n"
                "• **File Bobot:** `models/best.pt`\n"
                "• **Folder Dataset:** Folder `dataset/` telah disiapkan dengan file `data.yaml` untuk 6 kelas resmi.\n\n"
                "**Langkah setelah training selesai:**\n"
                "1. Salin file `best.pt` hasil training ke folder `models/best.pt`.\n"
                "2. Klik tombol **'Muat Ulang Model'** di tab Pengaturan.\n"
                "3. Sistem akan memuat bobot model YOLO baru secara instan tanpa perlu mematikan aplikasi!"
            )
            suggested_actions = [
                "Bagaimana cara menjalankan kamera?",
                "Tampilkan statistik saat ini"
            ]

        # 5. Kamera, Garis Virtual, & Pengaturan
        elif any(w in msg_lower for w in ["kamera", "camera", "garis", "virtual line", "webcam", "fps"]):
            reply = (
                f"📹 **Status & Konfigurasi Kamera:**\n\n"
                f"• **Status:** `{camera_status.upper()}` ({camera_manager.status_message})\n"
                f"• **FPS Kamera:** {camera_manager.current_fps} FPS (Batas Maksimal: {settings.MAX_INFERENCE_FPS})\n"
                f"• **Posisi Garis Virtual:** {camera_manager.counter.line_ratio * 100:.0f}% ketinggian frame\n"
                f"• **Confidence Threshold:** {camera_manager.detector.conf_threshold}\n\n"
                f"Objek yang melintasi garis virtual dari atas ke bawah akan dicatat sebagai 1 event counting unik tanpa duplikasi."
            )
            suggested_actions = [
                "Mulai kamera sekarang",
                "Bagaimana cara memilah sampah?"
            ]

        # 6. Default / Sapaan Ramah
        else:
            reply = (
                "👋 Halo! Saya **EcoBot AI**, asisten cerdas untuk dashboard pemantauan sampah **EcoSort AI**.\n\n"
                "Saya dapat membantu Anda dalam:\n"
                "• ♻️ **Pedoman Pemilahan Sampah:** Mengetahui kategori **Organik** (Kertas/Kardus), **Anorganik** (Botol/Plastik/Kaca), dan **Berbahaya** (Kaleng Logam).\n"
                "• 📊 **Informasi Data & Statistik:** Menampilkan total deteksi, rekap per kategori, dan alert terkini.\n"
                "• 🔍 **Root Cause Analysis (RCA):** Menganalisis akar masalah lonjakan limbah berbahaya menggunakan metode 5-Whys & Fishbone.\n"
                "• ⚙️ **Bantuan Teknis:** Pengaturan kamera, garis virtual, dan pemuatan model YOLO.\n\n"
                "Silakan ajukan pertanyaan atau pilih salah satu menu cepat di bawah ini:"
            )
            suggested_actions = [
                "Bagaimana pengelompokan sampah?",
                "Berapa total deteksi sekarang?",
                "Jelaskan Root Cause Analysis (RCA)",
                "Status model & kamera"
            ]

        return {
            "reply": reply,
            "suggested_actions": suggested_actions,
            "stats_context": {
                "total_detections": total_det,
                "macro_counts": macro_counts,
                "camera_status": camera_status,
                "model_status": model_status
            }
        }

