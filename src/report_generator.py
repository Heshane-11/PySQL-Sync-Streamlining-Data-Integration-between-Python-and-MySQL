import io
from datetime import datetime
import logging
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from src.analytics import analytics_engine
from src.ml_models import ml_hub

logger = logging.getLogger(__name__)

class ReportGenerator:
    def generate_pdf_report(self) -> io.BytesIO:
        """Generates an executive-ready business intelligence PDF report."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=14,
        )
        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=12,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#334155'),
        )

        story = []

        # Header Title
        story.append(Paragraph("⚡ PySQL-Sync | Retailytics Executive Brief", title_style))
        current_time = datetime.now().strftime("%B %d, %Y - %H:%M UTC")
        story.append(Paragraph(f"Generated on {current_time} | Data Engineering, Analytics & ML Platform", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#6366f1'), spaceAfter=14))

        # 1. Executive KPIs
        kpis = analytics_engine.get_kpi_summary()
        story.append(Paragraph("1. Executive Summary & Core KPIs", h2_style))
        
        kpi_data = [
            [
                Paragraph(f"<b>Gross Revenue</b><br/><font size=12 color='#10b981'><b>${kpis['total_revenue']:,.2f}</b></font>", body_style),
                Paragraph(f"<b>Total Orders</b><br/><font size=12 color='#6366f1'><b>{kpis['total_orders']:,}</b></font>", body_style),
                Paragraph(f"<b>Avg Order Value</b><br/><font size=12 color='#06b6d4'><b>${kpis['avg_order_value']:.2f}</b></font>", body_style),
                Paragraph(f"<b>Active Customers</b><br/><font size=12 color='#f59e0b'><b>{kpis['total_customers']:,}</b></font>", body_style),
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[135, 135, 135, 135])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 12))

        # 2. Annual Sales & YoY Growth Table
        story.append(Paragraph("2. Year-over-Year (YoY) Revenue Growth Trajectory", h2_style))
        yoy_df = analytics_engine.get_yoy_growth()
        yoy_rows = [["Year", "Gross Sales ($)", "Previous Year ($)", "YoY Growth (%)"]]
        for _, row in yoy_df.iterrows():
            yoy_rows.append([
                str(row["order_year"]),
                f"${row['total_sales']:,.2f}" if row["total_sales"] else "N/A",
                f"${row['previous_year_sales']:,.2f}" if row["previous_year_sales"] else "N/A",
                f"+{row['yoy_growth_percentage']}%" if row["yoy_growth_percentage"] else "Baseline",
            ])
        yoy_table = Table(yoy_rows, colWidths=[100, 150, 150, 140])
        yoy_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(yoy_table)
        story.append(Spacer(1, 12))

        # 3. RFM Customer Segments
        story.append(Paragraph("3. Customer RFM Segmentation (K-Means Clustering)", h2_style))
        rfm_res = ml_hub.run_rfm_segmentation()
        if rfm_res.get("status") == "success":
            rfm_rows = [["Segment Persona", "Customer Count", "Share %", "Avg Spend", "Recency"]]
            for seg in rfm_res["segments"]:
                rfm_rows.append([
                    seg["segment"],
                    f"{seg['customer_count']:,}",
                    f"{seg['percentage']}%",
                    f"${seg['avg_monetary_spend']:,.2f}",
                    f"{seg['avg_recency_days']} days",
                ])
            rfm_table = Table(rfm_rows, colWidths=[160, 100, 80, 100, 100])
            rfm_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            story.append(rfm_table)
        story.append(Spacer(1, 12))

        # 4. Logistics & Delivery Performance
        story.append(Paragraph("4. Logistics & Fulfillment Delivery Performance", h2_style))
        delay_res = ml_hub.get_logistics_delay_analysis()
        if delay_res.get("status") == "success":
            story.append(Paragraph(
                f"• <b>On-Time Delivery Rate:</b> {delay_res['on_time_rate_pct']}% | <b>Delay Rate:</b> {delay_res['overall_delay_rate_pct']}%<br/>"
                f"• <b>Average Transit Duration:</b> {delay_res['avg_delivery_days']} days nationwide.",
                body_style
            ))

        doc.build(story)
        buffer.seek(0)
        return buffer

report_generator = ReportGenerator()
