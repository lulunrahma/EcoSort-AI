import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

from backend.app.models.entities import Report, DetectionEvent
from backend.app.core.config import settings, OFFICIAL_CLASSES, CLASS_COLOR_PALETTE, MACRO_CATEGORIES
from backend.app.core.logging import logger

class ReportService:
    @staticmethod
    def generate_pdf(
        db: Session,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        title: str = "Laporan Monitoring Pemilahan Sampah - EcoSort AI"
    ) -> Report:
        """Generates a professional PDF report using ReportLab and Matplotlib."""
        if period_end is None:
            period_end = datetime.now(timezone.utc)
        if period_start is None:
            period_start = period_end - timedelta(days=7)

        # Query events within range
        events = (
            db.query(DetectionEvent)
            .filter(
                DetectionEvent.detected_at >= period_start,
                DetectionEvent.detected_at <= period_end
            )
            .all()
        )

        total_count = len(events)
        class_counts = {c: 0 for c in OFFICIAL_CLASSES}
        macro_counts = {"Anorganik": 0, "Organik": 0, "Berbahaya": 0}

        for e in events:
            if e.class_name in class_counts:
                class_counts[e.class_name] += 1
                m = MACRO_CATEGORIES.get(e.class_name, "Anorganik")
                macro_counts[m] += 1

        # File paths
        report_id_str = uuid.uuid4().hex[:10]
        filename = f"EcoSort_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{report_id_str}.pdf"
        file_path = os.path.join(settings.REPORT_DIR, filename)

        # Generate Distribution Chart with Matplotlib (Futuristic Theme Colors)
        chart_path = os.path.join(settings.REPORT_DIR, f"chart_{report_id_str}.png")
        try:
            fig, ax = plt.subplots(figsize=(6.5, 3), dpi=150)
            labels = list(class_counts.keys())
            values = list(class_counts.values())
            bar_colors = [CLASS_COLOR_PALETTE.get(c, "#3B82F6") for c in labels]

            ax.bar(labels, values, color=bar_colors, edgecolor="#4338CA", linewidth=0.8)
            ax.set_title("Distribusi Deteksi Sampah Meja Pemilahan", fontsize=11, fontweight="bold", color="#1E1B4B")
            ax.set_ylabel("Jumlah Objek", fontsize=9, color="#4B5563")
            ax.tick_params(axis='x', rotation=20, labelsize=8)
            ax.grid(axis='y', linestyle='--', alpha=0.4)
            plt.tight_layout()
            plt.savefig(chart_path)
            plt.close(fig)
        except Exception as err:
            logger.error(f"Failed to create chart image: {err}")
            chart_path = None

        # Build PDF with ReportLab
        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "EcoTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#4338CA"),  # Futuristic Indigo/Purple
            alignment=1,  # Center
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            "EcoSubtitle",
            parent=styles["Normal"],
            fontSize=9.5,
            textColor=colors.HexColor("#6B7280"),
            alignment=1,
            spaceAfter=16
        )
        h2_style = ParagraphStyle(
            "EcoH2",
            parent=styles["Heading2"],
            fontSize=11.5,
            leading=15,
            textColor=colors.HexColor("#1E1B4B"),
            spaceBefore=10,
            spaceAfter=6
        )

        story = []

        # 1. Header
        story.append(Paragraph(title, title_style))
        period_str = f"Periode: {period_start.strftime('%Y-%m-%d %H:%M')} s/d {period_end.strftime('%Y-%m-%d %H:%M')} (UTC)"
        story.append(Paragraph(period_str, subtitle_style))
        story.append(Spacer(1, 8))

        # 2. Executive Summary Box
        summary_data = [
            ["Parameter Sistem", "Nilai / Status"],
            ["Total Deteksi Objek", str(total_count)],
            ["Waktu Laporan Dibuat", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Pipeline Inferensi", "Ultralytics YOLO + Centroid Tracking"],
            ["Status K3 Pemilahan", "Pengawasan Limbah B3 Logam & Anorganik Aktif"]
        ]
        summary_table = Table(summary_data, colWidths=[200, 340])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 12))

        # 3. Macro Category Summary Table
        story.append(Paragraph("Rekapitulasi Kategori Makro (Pilahan Sampah Utama)", h2_style))
        macro_table_data = [
            ["Kategori Makro", "Komponen Objek Terdeteksi", "Jumlah", "Persentase", "Instruksi Penanganan"]
        ]

        m_anorganik = macro_counts.get("Anorganik", 0)
        pct_anorganik = f"{(m_anorganik / total_count * 100):.1f}%" if total_count > 0 else "0.0%"
        macro_table_data.append([
            "Anorganik",
            "plastic_bottle, plastic_bag, glass_bottle",
            str(m_anorganik),
            pct_anorganik,
            "Bilas residu cairan, pisahkan plastik & kaca."
        ])

        m_organik = macro_counts.get("Organik", 0)
        pct_organik = f"{(m_organik / total_count * 100):.1f}%" if total_count > 0 else "0.0%"
        macro_table_data.append([
            "Organik",
            "paper, cardboard",
            str(m_organik),
            pct_organik,
            "Jaga tetap kering untuk daur ulang serat pulp/kompos."
        ])

        m_b3 = macro_counts.get("Berbahaya", 0)
        pct_b3 = f"{(m_b3 / total_count * 100):.1f}%" if total_count > 0 else "0.0%"
        macro_table_data.append([
            "Berbahaya (B3)",
            "metal_can (Kaleng Logam)",
            str(m_b3),
            pct_b3,
            "Wadah khusus B3 tahan tusuk, gunakan sarung tangan K3."
        ])

        macro_table = Table(macro_table_data, colWidths=[80, 180, 50, 65, 165])
        macro_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (3, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(macro_table)
        story.append(Spacer(1, 12))

        # 4. Detail 6 Class Breakdown Table
        story.append(Paragraph("Rincian Deteksi per 6 Kelas Resmi", h2_style))
        class_table_data = [["No", "Nama Kelas", "Kategori Makro", "Jumlah", "Persentase (%)"]]
        
        for idx, cname in enumerate(OFFICIAL_CLASSES, start=1):
            cnt = class_counts.get(cname, 0)
            pct = f"{(cnt / total_count * 100):.1f}%" if total_count > 0 else "0.0%"
            macro_label = MACRO_CATEGORIES.get(cname, "Anorganik")
            class_table_data.append([str(idx), cname, macro_label, str(cnt), pct])

        class_table = Table(class_table_data, colWidths=[30, 160, 120, 90, 140])
        class_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#7C3AED")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAF5FF")]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E9D5FF")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(class_table)
        story.append(Spacer(1, 12))

        # 5. Embedded Chart
        if chart_path and os.path.exists(chart_path):
            story.append(Paragraph("Visualisasi Distribusi Objek Deteksi", h2_style))
            story.append(RLImage(chart_path, width=480, height=220))
            story.append(Spacer(1, 10))

        # 6. Build Document
        doc.build(story)

        # Cleanup chart image
        if chart_path and os.path.exists(chart_path):
            try:
                os.remove(chart_path)
            except Exception:
                pass

        # Save Report record in DB
        report_record = Report(
            created_at=datetime.now(timezone.utc),
            period_start=period_start,
            period_end=period_end,
            file_path=file_path,
            status="completed"
        )
        db.add(report_record)
        db.commit()
        db.refresh(report_record)
        return report_record
