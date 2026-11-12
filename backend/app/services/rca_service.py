from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.entities import DetectionEvent, Notification
from backend.app.core.config import MACRO_CATEGORIES
from backend.app.core.logging import logger

class RCAService:
    # In-memory status state for demo/runtime tracking
    _status_overrides: Dict[str, str] = {}
    _custom_diagnostics: List[Dict[str, Any]] = []

    @classmethod
    def get_all_diagnostics(cls, db: Session) -> Dict[str, Any]:
        """Evaluates database statistics, alerts, and predefined RCA models
        to return active root cause analysis diagnostics.
        """
        # Fetch current class counts from DB
        class_rows = (
            db.query(DetectionEvent.class_name, func.count(DetectionEvent.id))
            .group_by(DetectionEvent.class_name)
            .all()
        )
        counts = {r[0]: r[1] for r in class_rows}

        # Check for recent alerts
        recent_notifs = db.query(Notification).filter(Notification.is_read == False).all()
        has_metal_alert = any("metal_can" in (n.rule_key or "") or "metal_can" in n.title for n in recent_notifs)
        has_bag_alert = any("plastic_bag" in (n.rule_key or "") or "plastic_bag" in n.title for n in recent_notifs)

        metal_count = counts.get("metal_can", 0)
        bag_count = counts.get("plastic_bag", 0)
        paper_card_count = counts.get("paper", 0) + counts.get("cardboard", 0)

        diagnostics = [
            {
                "id": "RCA-001",
                "title": "Lonjakan Sampah Logam & Kaleng Berbahaya (Metal Can B3 Anomaly)",
                "severity": "high",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "category": "Berbahaya",
                "problem_statement": (
                    f"Terdeteksi {metal_count} kaleng logam/metal pada meja pemilahan. "
                    "Limbah kaleng berpotensi mengandung residu bahan kimia, aerosol bertekanan, "
                    "atau tepi tajam yang membahayakan keselamatan operator dan merusak belt konveyor."
                ),
                "five_whys": [
                    "Mengapa kaleng logam ditemukan di meja sortir? Limbah minuman kaleng dan workshop tercampur ke jalur umum.",
                    "Mengapa limbah tercampur? Tempat sampah di sumber (kantin & gudang) tidak memiliki partisi khusus logam B3.",
                    "Mengapa tidak ada partisi pemilah? Belum ada standardisasi wadah pemilahan terpisah untuk kaleng logam tajam.",
                    "Mengapa belum ada standardisasi? Kurangnya audit lingkungan berkala di area hulu fasilitas.",
                    "Akar Masalah (Root Cause): Ketiadaan regulasi segregasi sampah B3 di sumber hulu serta ketiadaan separator magnetik sebelum meja pemilahan."
                ],
                "ishikawa": {
                    "Man (Manusia)": [
                        "Operator belum terlatih menangani kaleng bertekanan",
                        "Penghasil sampah membuang kaleng bersama sampah umum"
                    ],
                    "Machine (Mesin)": [
                        "Belum ada overband magnetic separator di feeder conveyor",
                        "Sensor kamera terpasang di atas meja tanpa sensor induksi logam"
                    ],
                    "Method (Metode)": [
                        "Tidak ada screening visual sebelum sampah naik ke konveyor",
                        "SOP pemilahan logam B3 belum diperbarui"
                    ],
                    "Material (Material)": [
                        "Kaleng cat/aerosol dengan sisa gas berbahaya",
                        "Kaleng minuman dengan tepi bergerigi tajam"
                    ],
                    "Environment (Lingkungan)": [
                        "Pencahayaan di area loading dock redup",
                        "Kecepatan arus sampah tidak sebanding dengan kapasitas sortir"
                    ]
                },
                "corrective_actions": [
                    "Segera isolasi objek kaleng logam ke wadah khusus 'BERBAHAYA (B3)' dengan warna ungu/merah.",
                    "Gunakan penjepit magnetik manual untuk memindahkan kaleng tanpa sentuhan tangan langsung."
                ],
                "preventive_actions": [
                    "Instalasi separator magnetik permanen pada hopper awal sebelum conveyor meja pemilahan.",
                    "Sediakan tong sampah terpilah berlabel 'LOGAM / KALENG B3' di kantin, kantor, dan bengkel.",
                    "Lakukan pelatihan K3 penanganan limbah berbahaya bagi seluruh kru pemilah."
                ],
                "status": cls._status_overrides.get("RCA-001", "active" if has_metal_alert or metal_count >= 3 else "investigating")
            },
            {
                "id": "RCA-002",
                "title": "Akumulasi Kantong Plastik Fleksibel (Plastic Bag Jamming Risk)",
                "severity": "medium",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "category": "Anorganik",
                "problem_statement": (
                    f"Terdeteksi {bag_count} kantong kresek/plastik tipis. "
                    "Plastik fleksibel memiliki rasio luas terhadap berat yang tinggi dan "
                    "berisiko melilit as roda konveyor atau menutupi objek lain di bawahnya (occlusion)."
                ),
                "five_whys": [
                    "Mengapa kantong kresek menumpuk? Banyak kemasan plastik sekali pakai masuk dari area kantin.",
                    "Mengapa tidak ditekan/dipadatkan? Tidak ada alat pres plastik di jalur awal.",
                    "Mengapa berisiko bagi konveyor? Sifatnya yang tipis mudah tertarik celah roller bergerak.",
                    "Mengapa operator terlambat mengambilnya? Kecepatan konveyor terlalu tinggi.",
                    "Akar Masalah (Root Cause): Belum adanya air-classifier (peniup angin) untuk memisahkan plastik ringan sebelum meja sortir mekanik."
                ],
                "ishikawa": {
                    "Man (Manusia)": ["Kecenderungan membuang kantong plastik tanpa dilipat atau diikat"],
                    "Machine (Mesin)": ["Roller konveyor tanpa pelindung anti-lilitan (wrap guard)"],
                    "Method (Metode)": ["Belum ada tahapan pre-sorting plastik film"],
                    "Material (Material)": ["Plastik kresek LDPE/HDPE sangat tipis dan mudah melayang"],
                    "Environment (Lingkungan)": ["Arus udara di ruangan sortir mempengaruhi posisi kantong plastik"]
                },
                "corrective_actions": [
                    "Prioritaskan pengambilan kantong plastik di bagian depan meja pemilahan.",
                    "Kumpulkan kantong plastik ke dalam karung baling terpisah."
                ],
                "preventive_actions": [
                    "Pasang roller wrap-guard dan pertimbangkan peniup udara (air knife) pemisah film plastik.",
                    "Sosialisasikan pengurangan kantong kresek sekali pakai di lingkungan fasilitas."
                ],
                "status": cls._status_overrides.get("RCA-002", "active" if has_bag_alert or bag_count >= 5 else "resolved")
            },
            {
                "id": "RCA-003",
                "title": "Risiko Degradasi Kualitas Kertas & Kardus Organik (Pulp Contamination)",
                "severity": "medium",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "category": "Organik",
                "problem_statement": (
                    f"Terdeteksi {paper_card_count} produk kertas & kardus organik. "
                    "Serat selulosa pada kertas dan kardus sangat rentan rusak jika basah terkena sisa cairan "
                    "dari botol plastik atau botol kaca yang tidak tertutup rapat."
                ),
                "five_whys": [
                    "Mengapa kertas/kardus berisiko rusak? Terkontaminasi tumpahan cairan minuman dari botol.",
                    "Mengapa ada sisa cairan di conveyor? Botol plastik dan kaca dibuang dengan kondisi masih berisi cairan.",
                    "Mengapa masyarakat/karyawan tidak mengosongkan botol? Tidak tersedia bak wastafel peniris cairan di samping tong sampah.",
                    "Mengapa tidak ada fasilitas peniris? Fasilitas tempat sampah hanya berupa tong kering biasa.",
                    "Akar Masalah (Root Cause): Ketiadaan wastafel peniris cairan (liquid dump sink) di stasiun tempat sampah hulu menyebabkan kertas tercemar cairan."
                ],
                "ishikawa": {
                    "Man (Manusia)": ["Pengguna tidak membuang sisa minuman sebelum membuang botol"],
                    "Machine (Mesin)": ["Tidak ada sensor pendeteksi kelembaban pada tumpukan kertas"],
                    "Method (Metode)": ["Pencampuran sampah kering (kertas) dengan sampah basah (botol)"],
                    "Material (Material)": ["Kertas koran dan karton bergelombang mudah menyerap air"],
                    "Environment (Lingkungan)": ["Kelembaban udara meja pemilahan tinggi"]
                },
                "corrective_actions": [
                    "Segera pisahkan kardus dan kertas kering ke wadah berpenutup kering.",
                    "Kertas yang basah dipisahkan untuk pengomposan daripada daur ulang kertas bersih."
                ],
                "preventive_actions": [
                    "Pasang wastafel peniris cairan di setiap stasiun tong sampah fasilitas.",
                    "Edukasi aturan 'Kosongkan, Bilas, Keringkan' sebelum botol dibuang."
                ],
                "status": cls._status_overrides.get("RCA-003", "investigating")
            },
            {
                "id": "RCA-004",
                "title": "Optimasi Akurasi Pelacakan Objek Saat Penumpukan (Occlusion & Tracking Jitter)",
                "severity": "low",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "category": "System",
                "problem_statement": (
                    "Saat laju tumpukan sampah tinggi, beberapa objek saling bertumpuk (occlusion), "
                    "mengakibatkan fluktuasi bounding box sementara."
                ),
                "five_whys": [
                    "Mengapa objek saling menumpuk? Sampah dijatuhkan secara berkelompok dari conveyor masuk.",
                    "Mengapa dijatuhkan berkelompok? Tidak ada spreader mekanik (penyebar tumpukan).",
                    "Mengapa kamera kesulitan saat bertumpuk? YOLO mendeteksi permukaan atas, bagian bawah tertutup.",
                    "Mengapa tracker melompat? Jarak Euclidean antar centroid bergeser saat tertutup.",
                    "Akar Masalah (Root Cause): Distribusi sampah tidak merata (clumping) sebelum melewati bidang pandang kamera pemilahan."
                ],
                "ishikawa": {
                    "Man (Manusia)": ["Operator feeding menuangkan sampah sekaligus banyak"],
                    "Machine (Mesin)": ["Kamera tunggal dari arah tegak lurus (top-down view)"],
                    "Method (Metode)": ["Laju feeding manual tanpa timer interval"],
                    "Material (Material)": ["Bentuk sampah bervariasi dengan derajat refleksi cahaya berbeda"],
                    "Environment (Lingkungan)": ["Pencahayaan specular highlight pada plastik mengkilap"]
                },
                "corrective_actions": [
                    "Aktifkan mode tracking multi-hypothetical pada modul ByteTrack/Centroid.",
                    "Atur ambang confidence kamera ke 0.40 agar deteksi lebih adaptif."
                ],
                "preventive_actions": [
                    "Pasang spreader vibrator / sirip penyebar sampah di mulut conveyor.",
                    "Pertimbangkan pemasangan kamera sudut kedua (multi-angle vision) untuk rilis lanjutan."
                ],
                "status": cls._status_overrides.get("RCA-004", "resolved")
            }
        ]

        # Append custom diagnostics if any
        diagnostics.extend(cls._custom_diagnostics)

        summary = {
            "total": len(diagnostics),
            "active": sum(1 for d in diagnostics if d["status"] == "active"),
            "investigating": sum(1 for d in diagnostics if d["status"] == "investigating"),
            "resolved": sum(1 for d in diagnostics if d["status"] == "resolved")
        }

        return {"diagnostics": diagnostics, "summary": summary}

    @classmethod
    def update_status(cls, diagnostic_id: str, new_status: str) -> bool:
        cls._status_overrides[diagnostic_id] = new_status
        logger.info(f"RCA Diagnostic {diagnostic_id} status updated to {new_status}")
        return True

    @classmethod
    def create_custom_rca(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        rca_id = f"RCA-{len(cls._custom_diagnostics) + 101}"
        new_diag = {
            "id": rca_id,
            "title": data.get("title", "Custom Root Cause Analysis"),
            "severity": data.get("severity", "medium"),
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "category": data.get("category", "Anorganik"),
            "problem_statement": data.get("problem_statement", ""),
            "five_whys": data.get("five_whys", []),
            "ishikawa": data.get("ishikawa", {"Man": [], "Machine": [], "Method": [], "Material": [], "Environment": []}),
            "corrective_actions": data.get("corrective_actions", []),
            "preventive_actions": data.get("preventive_actions", []),
            "status": "active"
        }
        cls._custom_diagnostics.append(new_diag)
        return new_diag

