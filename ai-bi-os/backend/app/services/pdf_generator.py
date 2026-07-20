import io
import json
from app.core.database import get_db_connection
import pandas as pd
import numpy as np
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.services.stats_service import compute_kpis, find_column, forecast_series
from app.core.config import DB_PATH

# DESIGN SYSTEM (Big 4 Aesthetic)
# =====================================================================
INK_STR    = "#0F172A"
PAPER_STR  = "#FFFFFF"
MUTED_STR  = "#64748B"
LINE_STR   = "#E2E8F0"
ACCENT_STR = "#2563EB"
SUCCESS_STR= "#16A34A"
DANGER_STR = "#DC2626"
PANEL_BG_STR="#F8FAFC"

INK        = colors.HexColor(INK_STR)
PAPER      = colors.HexColor(PAPER_STR)
MUTED      = colors.HexColor(MUTED_STR)
LINE       = colors.HexColor(LINE_STR)
ACCENT     = colors.HexColor(ACCENT_STR)
SUCCESS    = colors.HexColor(SUCCESS_STR)
DANGER     = colors.HexColor(DANGER_STR)
PANEL_BG   = colors.HexColor(PANEL_BG_STR)

def format_number(value):
    if value is None or pd.isna(value):
        return "0"
    try:
        val = float(value)
        abs_val = abs(val)
        if abs_val >= 10000000: # 1 Crore
            return f"{val / 10000000:.2f}Cr"
        if abs_val >= 100000: # 1 Lakh
            return f"{val / 100000:.2f}L"
        if abs_val >= 1000: # 1 Thousand
            return f"{val / 1000:.2f}K"
        if val.is_integer():
            return str(int(val))
        return f"{val:.2f}"
    except:
        return str(value)

def matplotlib_formatter(x, pos):
    return format_number(x)

class PremiumCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        self.dataset_name = kwargs.pop('dataset_name', '')
        self.gen_date = kwargs.pop('gen_date', '')
        self.report_title = kwargs.pop('report_title', 'DATA ANALYSIS REPORT')
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            if self._pageNumber > 1:
                self.draw_footer(page_count)
                self.draw_header(page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_footer(self, page_count):
        self.saveState()
        self.setStrokeColor(LINE)
        self.setLineWidth(0.5)
        self.line(22*mm, 15*mm, A4[0] - 22*mm, 15*mm)
        
        self.setFont('Helvetica', 7.5)
        self.setFillColor(MUTED)
        self.drawString(22*mm, 10*mm, "DataMind OS")
        self.drawRightString(A4[0] - 22*mm, 10*mm, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

    def draw_header(self, page_count):
        self.saveState()
        self.setStrokeColor(LINE)
        self.setLineWidth(0.5)
        self.line(22*mm, A4[1] - 15*mm, A4[0] - 22*mm, A4[1] - 15*mm)
        
        self.setFont('Helvetica', 8)
        self.setFillColor(MUTED)
        # Simple all-caps letterspaced effect by just drawing string, tracking is limited in standard reportlab
        self.drawString(22*mm, A4[1] - 12*mm, " ".join(list(self.report_title.upper())))
        self.drawRightString(A4[0] - 22*mm, A4[1] - 12*mm, f"{self._pageNumber:02d} / {page_count:02d}")
        self.restoreState()

def get_regression_models(dataset_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT target, features, r2_test, timestamp
            FROM regression_models
            WHERE dataset_id = ?
            ORDER BY timestamp DESC
        ''', (dataset_id,))
        rows = cursor.fetchall()
        conn.close()
        
        models = []
        for r in rows:
            models.append({
                "target": r[0],
                "features": r[1] if isinstance(r[1], (dict, list)) else json.loads(r[1]),
                "r2_test": r[2],
                "timestamp": r[3]
            })
        return models
    except:
        return []
    
def get_outliers(df):
    num_cols = df.select_dtypes(include=[np.number]).columns
    outliers = []
    for col in num_cols:
        clean_col = df[col].dropna()
        if len(clean_col) < 5: continue
        
        mean_val = clean_col.mean()
        std_val = clean_col.std()
        
        if std_val > 0:
            z_scores = ((clean_col - mean_val) / std_val).abs()
            for idx, z in z_scores.items():
                if z > 3:
                    outliers.append({
                        "column": col,
                        "row": str(idx),
                        "value": df.loc[idx, col],
                        "expected": f"µ±3σ ({format_number(mean_val-3*std_val)} to {format_number(mean_val+3*std_val)})",
                        "method": "Z-Score > 3",
                        "z": z
                    })
    
    outliers = sorted(outliers, key=lambda x: x["z"], reverse=True)[:10]
    return outliers

def generate_pdf_report(dataset_info, df):
    buffer = io.BytesIO()
    gen_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=22*mm, leftMargin=22*mm,
        topMargin=22*mm, bottomMargin=22*mm
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', fontName='Helvetica-Bold', fontSize=26, textColor=INK, spaceAfter=20, leading=30)
    h2_style = ParagraphStyle('H2Style', fontName='Helvetica-Bold', fontSize=13, textColor=INK, spaceBefore=12, spaceAfter=8, leading=16)
    body_style = ParagraphStyle('BodyStyle', fontName='Helvetica', fontSize=9.5, textColor=INK, spaceAfter=8, leading=14)
    caption_style = ParagraphStyle('CaptionStyle', fontName='Helvetica', fontSize=7.5, textColor=MUTED, spaceBefore=4, spaceAfter=8, leading=10)
    kpi_name_style = ParagraphStyle('KPINameStyle', fontName='Helvetica', fontSize=8, textColor=MUTED, leading=10)
    kpi_val_style = ParagraphStyle('KPIValStyle', fontName='Helvetica-Bold', fontSize=24, textColor=INK, leading=28)
    kpi_trend_style = ParagraphStyle('KPITrendStyle', fontName='Helvetica', fontSize=9.5, leading=13)
    kpi_source_style = ParagraphStyle('KPISourceStyle', fontName='Helvetica', fontSize=7.5, textColor=MUTED, leading=10)

    story = []
    
    # --- COMPONENT LIBRARY ---
    def section_header(number_str, title):
        p_text = f"<font color='{ACCENT.hexval()}'>{number_str}</font>  {title}"
        story.append(Paragraph(p_text, h2_style))
        story.append(Table([[""]], colWidths=[doc.width], rowHeights=[0.5], style=TableStyle([
            ('BACKGROUND', (0,0), (0,0), LINE),
            ('BOTTOMPADDING', (0,0), (0,0), 0),
            ('TOPPADDING', (0,0), (0,0), 0),
        ])))
        story.append(Spacer(1, 6*mm))

    def kpi_row(kpi_list):
        if not kpi_list:
            return None
        cells = []
        # If there are many KPIs, limit to 4 per row or handle wrapping, but for exec summary usually 3-4.
        display_kpis = kpi_list[:4]
        col_w = doc.width / len(display_kpis)
        for k in display_kpis:
            name = str(k.get('name', '')).upper()
            value = k.get('value', 0)
            prev = k.get('previous_value', 0)
            trend_pct = k.get('trend', 0)
            delta = value - prev
            fmt_val = format_number(value)
            
            t_color = SUCCESS.hexval() if delta > 0 else DANGER.hexval() if delta < 0 else MUTED.hexval()
            t_char = "▲" if delta > 0 else "▼" if delta < 0 else "—"
            trend_str_val = f"{trend_pct:+.1f}%" if isinstance(trend_pct, (int, float)) else f"{trend_pct}%"
            if delta == 0: trend_str_val = "0.0%"
            t_str = f"<font color='{t_color}'>{t_char} {trend_str_val}</font>"
            
            cell_table = Table([
                [Paragraph(name, kpi_name_style)],
                [Paragraph(fmt_val, kpi_val_style)],
                [Paragraph(t_str, kpi_trend_style)]
            ], colWidths=[col_w - 6])
            cell_table.setStyle(TableStyle([
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ]))
            cells.append(cell_table)
            
        row_table = Table([cells], colWidths=[col_w]*len(display_kpis))
        row_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ]))
        return row_table

    def progress_bar(label, value, max_val=100):
        from reportlab.graphics.shapes import Drawing, Rect
        w = doc.width * 0.5
        d = Drawing(w, 12)
        d.add(Rect(0, 2, w, 8, fillColor=LINE, strokeColor=None))
        fill_w = (value / max_val) * w
        color = SUCCESS if value >= 90 else (ACCENT if value >= 70 else DANGER)
        d.add(Rect(0, 2, fill_w, 8, fillColor=color, strokeColor=None))
        
        t = Table([
            [Paragraph(label, body_style), d, Paragraph(f"<b>{value}%</b>", body_style)]
        ], colWidths=[doc.width*0.3, w + 10, doc.width*0.15])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        return t

    # ================= COVER PAGE =================
    story.append(Spacer(1, doc.height * 0.35))
    story.append(Paragraph("DATA ANALYSIS REPORT", title_style))
    story.append(Paragraph(f"Dataset: {dataset_info.get('name', 'N/A')}", body_style))
    story.append(Paragraph(f"Generated: {gen_date}", caption_style))
    story.append(Spacer(1, 12))
    story.append(Table([[""]], colWidths=[doc.width], rowHeights=[2], style=TableStyle([
        ('BACKGROUND', (0,0), (0,0), ACCENT),
        ('BOTTOMPADDING', (0,0), (0,0), 0),
        ('TOPPADDING', (0,0), (0,0), 0),
    ])))
    story.append(PageBreak())
    
    # ================= EXECUTIVE SUMMARY =================
    section_header("01", "Executive Summary")
    
    semantic_dict = dataset_info.get("semantic_dict", {})
    bus_term = semantic_dict.get("business_terminology", {}) if semantic_dict else {}
    rev_col = bus_term.get("primary_metric") if bus_term else None
    rev_label = bus_term.get("primary_metric_label", "Total Revenue") if bus_term else "Total Revenue"
    rev_type = bus_term.get("primary_metric_type", "currency") if bus_term else "currency"
    
    kpi_results = compute_kpis(df, semantic_dict)
    kpis = kpi_results.get("kpis", [])
    
    if kpis:
        kpi_table = kpi_row(kpis)
        if kpi_table:
            story.append(kpi_table)
            story.append(Spacer(1, 8))
            
    # AI Summary placeholder
    date_col = None
    if semantic_dict:
        date_cols = semantic_dict.get("semantic_dictionary", {}).get("date_columns", [])
        if date_cols and date_cols[0] in df.columns:
            date_col = date_cols[0]
            
    if not date_col:
        date_col = find_column(df, r'date|month|year|time')
        
    story.append(Paragraph(f"This report presents a synthesized view of core business metrics and underlying data trends. The executive dashboard above highlights top-line performance. Further sections detail {rev_label.lower()} analytics, forecast modeling, segment distribution, and data quality indicators.", body_style))
    story.append(Spacer(1, 8))
    
    # Key Observations
    story.append(Paragraph("<b>Key Observations</b>", h2_style))
    rev_kpi = next((k for k in kpis if k.get('name', '') == rev_label or k.get('column', '') == rev_col), None)
    obs = []
    if rev_kpi:
        trend = rev_kpi.get('trend', 0)
        direction = "increased" if trend >= 0 else "decreased"
        obs.append(f"Top-line performance ({rev_label}) has {direction} by {abs(trend)}% compared to the prior period.")
        
    obs.append(f"Data Quality stands at {dataset_info.get('quality_score', 0)}/100, indicating reliable inputs.")
    
    for ob in obs:
        # Small accent square bullet
        bullet = f"<font color='{ACCENT.hexval()}' size=8>■</font>"
        story.append(Paragraph(f"{bullet}  {ob}", body_style))
        
    story.append(Spacer(1, 12))
        
    story.append(PageBreak())
    
    def data_table(headers, rows, col_widths=None):
        if not col_widths:
            col_widths = [doc.width / len(headers)] * len(headers)
        table_data = [headers] + rows
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), INK),
            ('TEXTCOLOR', (0,0), (-1,0), PAPER),
            ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 9),
            ('FONT', (0,1), (-1,-1), 'Helvetica', 9),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'), # numbers right aligned
            ('LINEBELOW', (0,1), (-1,-1), 0.5, LINE),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        return t

    # ================= KPI DASHBOARD =================
    section_header("02", "KPI Dashboard")
    
    if len(kpis) > 0:
        for i in range(0, len(kpis), 4):
            kr = kpi_row(kpis[i:i+4])
            if kr:
                story.append(kr)
                story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("No KPIs were generated for this dataset.", body_style))
        story.append(Spacer(1, 8))
        
    story.append(PageBreak())
    
    # ================= REVENUE ANALYTICS =================
    section_header("03", f"{rev_label} Analytics")
    
    chart_data = kpi_results.get("chart_data", [])
    
    if date_col and rev_col and chart_data:
        plt.figure(figsize=(8, 4), dpi=200)
        ax = plt.gca()
        # Big-4 Aesthetic Chart
        plt.gcf().patch.set_facecolor(PAPER_STR)
        ax.set_facecolor(PAPER_STR)
        
        hist_data = [d for d in chart_data if d.get("value") is not None]
        fcst_data = [d for d in chart_data if d.get("forecast") is not None and d.get("value") is None]
        
        if hist_data and fcst_data:
            last_hist = hist_data[-1].copy()
            last_hist["forecast"] = last_hist["value"]
            fcst_data.insert(0, last_hist)
            
        fcst_bounds = None
        if fcst_data and len(fcst_data) > 1:
            f_res = forecast_series(df, rev_col, periods=len(fcst_data)-1)
            if f_res.get("available"):
                fcst_bounds = f_res.get("forecast")
                
        x_hist = [d["name"] for d in hist_data]
        y_hist = [d["value"] for d in hist_data]
        
        ax.plot(x_hist, y_hist, color=ACCENT_STR, marker='o', markersize=4, linestyle='-', linewidth=2, label='Actual')
        
        if hist_data:
            lbl_val = f"${format_number(y_hist[-1])}" if rev_type == "currency" else format_number(y_hist[-1])
            ax.annotate(lbl_val, (len(x_hist)-1, y_hist[-1]), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color=INK_STR, fontweight='bold')
            
        if fcst_data:
            x_fcst = [d["name"] for d in fcst_data]
            y_fcst = [d["forecast"] for d in fcst_data]
            x_idx = range(len(x_hist)-1, len(x_hist)-1 + len(x_fcst))
            ax.plot(x_fcst, y_fcst, color=ACCENT_STR, linestyle='--', linewidth=2, label='Forecast')
            
            if fcst_bounds:
                y_lower = [y_fcst[0]] + [b["lower"] for b in fcst_bounds]
                y_upper = [y_fcst[0]] + [b["upper"] for b in fcst_bounds]
                ax.fill_between(x_idx, y_lower, y_upper, alpha=0.1, color=ACCENT_STR)
                
            lbl_fc = f"${format_number(y_fcst[-1])}" if rev_type == "currency" else format_number(y_fcst[-1])
            ax.annotate(lbl_fc, (x_idx[-1], y_fcst[-1]), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color=INK_STR, fontweight='bold')

        def custom_formatter(x, pos):
            val_str = format_number(x)
            if rev_type == "currency":
                return f"${val_str}"
            return val_str

        ax.yaxis.set_major_formatter(FuncFormatter(custom_formatter))
        ax.grid(axis='y', linestyle='-', alpha=0.08, color=MUTED_STR)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(LINE_STR)
        ax.spines['bottom'].set_linewidth(0.5)
        ax.tick_params(axis='x', colors=MUTED_STR, labelsize=8, length=0)
        ax.tick_params(axis='y', colors=MUTED_STR, labelsize=8, length=0)
        ax.margins(y=0.15)
        ax.set_ylim(bottom=0)
        plt.xticks(rotation=45, ha='right')
        ax.legend(loc='lower left', bbox_to_anchor=(0, 1.05), ncol=2, frameon=False, fontsize=8, labelcolor=MUTED_STR)
        
        plt.tight_layout()
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', facecolor=plt.gcf().get_facecolor())
        plt.close()
        img_buffer.seek(0)
        story.append(Image(img_buffer, width=doc.width, height=doc.width*0.5)) 
        
        story.append(Spacer(1, 20))
        
        # Monthly Table
        section_header("04", f"Monthly {rev_label} Values")
        h_row = [Paragraph("<b>Period</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER)),
                 Paragraph(f"<b>{rev_label}</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2)),
                 Paragraph("<b>MoM %</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2)),
                 Paragraph("<b>Type</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2))]
        
        rows = []
        prev_val = None
        for d in chart_data:
            val = d.get("value")
            fcst = d.get("forecast")
            v = val if val is not None else fcst
            typ = "Actual" if val is not None else "Forecast"
            
            mom = "—"
            if prev_val is not None and prev_val > 0:
                pct = ((v - prev_val) / prev_val) * 100
                c = SUCCESS.hexval() if pct > 0 else DANGER.hexval() if pct < 0 else MUTED.hexval()
                mom = f"<font color='{c}'>{pct:+.1f}%</font>"
            
            p_style = ParagraphStyle('italic', fontName='Helvetica-Oblique', fontSize=9, textColor=MUTED) if typ == "Forecast" else body_style
            right_align = ParagraphStyle('ra', parent=p_style, alignment=2)
            
            v_formatted = f"${format_number(v)}" if rev_type == "currency" else format_number(v)
            
            rows.append([
                Paragraph(d["name"], p_style),
                Paragraph(v_formatted, right_align),
                Paragraph(mom, right_align),
                Paragraph(typ, right_align)
            ])
            prev_val = v
            
        col_widths = [doc.width * 0.4, doc.width * 0.2, doc.width * 0.2, doc.width * 0.2]
        story.append(KeepTogether([data_table(h_row, rows, col_widths)]))
        
        # Forecast bounds table if available
        if fcst_bounds:
            story.append(Spacer(1, 20))
            section_header("05", "Forecast Details")
            fh_row = [Paragraph("<b>Period</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER)),
                      Paragraph("<b>Expected</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2)),
                      Paragraph("<b>Lower Bound</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2)),
                      Paragraph("<b>Upper Bound</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2))]
            
            f_rows = []
            right_align = ParagraphStyle('ra', fontName='Helvetica', fontSize=9, alignment=2)
            for b in fcst_bounds:
                f_rows.append([
                    Paragraph(b["date"], body_style), 
                    Paragraph(format_number(b["forecast"]), right_align), 
                    Paragraph(format_number(b["lower"]), right_align), 
                    Paragraph(format_number(b["upper"]), right_align)
                ])
            story.append(KeepTogether([data_table(fh_row, f_rows, col_widths), Spacer(1,4), Paragraph("Method: Linear trend projection", caption_style)]))
    elif rev_col:
        cat_cols = df.select_dtypes(exclude=[np.number, 'datetime64']).columns
        if len(cat_cols) > 0:
            c = cat_cols[0]
            grp = df.groupby(c)[rev_col].sum().sort_values(ascending=False).head(8)
            if len(grp) > 0:
                plt.figure(figsize=(8, 4), dpi=200)
                ax = plt.gca()
                plt.gcf().patch.set_facecolor(PAPER_STR)
                ax.set_facecolor(PAPER_STR)
                
                x_pos = np.arange(len(grp))
                labels = [str(x) for x in grp.index]
                values = grp.values
                
                ax.bar(x_pos, values, color=ACCENT_STR, width=0.6)
                ax.set_xticks(x_pos)
                ax.set_xticklabels(labels, fontsize=8, color=MUTED_STR, rotation=45, ha='right')
                
                for i, v in enumerate(values):
                    ax.text(i, v, format_number(v), ha='center', va='bottom', fontsize=8, color=INK_STR, fontweight='bold')
                
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_visible(False)
                ax.spines['bottom'].set_color(LINE_STR)
                ax.spines['bottom'].set_linewidth(0.5)
                ax.tick_params(axis='y', left=False, labelleft=False)
                ax.tick_params(axis='x', length=0)
                
                plt.tight_layout()
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', bbox_inches='tight', facecolor=plt.gcf().get_facecolor())
                plt.close()
                img_buffer.seek(0)
                
                story.append(Paragraph(f"<b>Revenue / Metric Distribution by {c.title()}</b>", body_style))
                story.append(Image(img_buffer, width=doc.width, height=doc.width*0.5))
                story.append(Spacer(1, 20))
        else:
            story.append(Paragraph("Not enough dimensions for detailed charting.", body_style))
    else:
        story.append(Paragraph("No appropriate metrics found for charting.", body_style))
        
    story.append(Spacer(1, 20))
    
    # ================= SEGMENT BREAKDOWN =================
    if rev_col:
        df_temp = df.copy()
        if date_col:
            df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
            latest_month = df_temp[date_col].max()
            if pd.notna(latest_month):
                df_temp = df_temp[df_temp[date_col].dt.to_period('M') == latest_month.to_period('M')]
                
        cat_cols = df_temp.select_dtypes(exclude=[np.number, 'datetime64']).columns
            
        dims = []
        for c in cat_cols:
            if 'id' in c.lower() or df_temp[c].nunique() > 50 or df_temp[c].nunique() < 2: continue
            grp = df_temp.groupby(c)[rev_col].sum().sort_values(ascending=False).head(5)
            if len(grp) > 0: dims.append((c, grp))
            if len(dims) == 3: break
            
        if dims:
            story.append(PageBreak())
            section_header("06", "Segment Analysis (Latest Period)")
            for c, grp in dims:
                tot = grp.sum()
                if tot == 0: continue
                
                plt.figure(figsize=(6, 2.5), dpi=200)
                ax = plt.gca()
                plt.gcf().patch.set_facecolor(PAPER_STR)
                ax.set_facecolor(PAPER_STR)
                
                y_pos = np.arange(len(grp))
                labels = [str(x) for x in grp.index]
                values = grp.values
                
                ax.barh(y_pos, values, color=ACCENT_STR, height=0.6)
                ax.set_yticks(y_pos)
                ax.set_yticklabels(labels, fontsize=8, color=INK_STR)
                
                for i, v in enumerate(values):
                    ax.text(v, i, f"  {format_number(v)} ({(v/tot*100):.1f}%)", va='center', fontsize=8, color=INK_STR)
                    
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_visible(False)
                ax.spines['left'].set_color(LINE_STR)
                ax.tick_params(axis='x', bottom=False, labelbottom=False)
                ax.tick_params(axis='y', length=0)
                ax.invert_yaxis()
                
                plt.tight_layout()
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', bbox_inches='tight', facecolor=plt.gcf().get_facecolor())
                plt.close()
                img_buffer.seek(0)
                
                story.append(Paragraph(f"<b>Segment: {c.title()}</b>", body_style))
                story.append(Image(img_buffer, width=doc.width*0.8, height=doc.width*0.33))
                story.append(Spacer(1, 15))

    # ================= NUMERIC COLUMNS =================
    story.append(PageBreak())
    section_header("07", "Statistical Summary")
    num_cols = df.select_dtypes(include=[np.number]).columns
    if len(num_cols) > 0:
        h_row = [Paragraph("<b>Column</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER)),
                 Paragraph("<b>Sum</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2)),
                 Paragraph("<b>Mean</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2)),
                 Paragraph("<b>Min</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2)),
                 Paragraph("<b>Max</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2)),
                 Paragraph("<b>Trend</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2))]
        
        recent_df, prior_df = df, None
        if date_col:
            try:
                periods = df.groupby(pd.to_datetime(df[date_col], errors='coerce').dt.to_period('M'))
                if len(periods) >= 2:
                    sorted_periods = sorted(periods.groups.keys())
                    recent_df = periods.get_group(sorted_periods[-1])
                    prior_df = periods.get_group(sorted_periods[-2])
            except: pass
            
        rows = []
        right_align = ParagraphStyle('ra', fontName='Helvetica', fontSize=9, alignment=2)
        for col in num_cols[:15]:
            c_sum = format_number(df[col].sum())
            c_mean = format_number(df[col].mean())
            c_min = format_number(df[col].min())
            c_max = format_number(df[col].max())
            
            trend_str = "—"
            if prior_df is not None and not prior_df.empty:
                c_val = recent_df[col].sum()
                p_val = prior_df[col].sum()
                if p_val != 0 and pd.notna(p_val):
                    pct = ((c_val - p_val) / p_val) * 100
                    c = SUCCESS.hexval() if pct > 0 else DANGER.hexval() if pct < 0 else MUTED.hexval()
                    t_char = "▲" if pct > 0 else "▼" if pct < 0 else "—"
                    trend_str = f"<font color='{c}'>{t_char} {pct:+.1f}%</font>"
                    
            rows.append([
                Paragraph(str(col), body_style),
                Paragraph(c_sum, right_align),
                Paragraph(c_mean, right_align),
                Paragraph(c_min, right_align),
                Paragraph(c_max, right_align),
                Paragraph(trend_str, right_align)
            ])
            
        col_widths = [doc.width * 0.25, doc.width * 0.15, doc.width * 0.15, doc.width * 0.15, doc.width * 0.15, doc.width * 0.15]
        story.append(KeepTogether([data_table(h_row, rows, col_widths)]))
    else:
        story.append(Paragraph("No numeric columns available.", body_style))
        
    story.append(Spacer(1, 20))
    
    # ================= OUTLIERS =================
    section_header("08", "Data Quality & Outliers")
    
    # Progress bars for Data Quality
    try:
        import json
        qb_str = dataset_info.get("quality_breakdown")
        if qb_str:
            qb = json.loads(qb_str) if isinstance(qb_str, str) else qb_str
            story.append(Paragraph("<b>Dataset Health Metrics</b>", h2_style))
            for k, v in qb.items():
                story.append(progress_bar(k.replace('_', ' ').title(), float(v)))
            story.append(Spacer(1, 15))
    except Exception as e:
        pass
        
    outliers = get_outliers(df)
    if outliers:
        h_row = [Paragraph("<b>Column</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER)),
                 Paragraph("<b>Row Index</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2)),
                 Paragraph("<b>Value</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2)),
                 Paragraph("<b>Expected Range</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER)),
                 Paragraph("<b>Method</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER))]
                 
        rows = []
        right_align = ParagraphStyle('ra', fontName='Helvetica', fontSize=9, alignment=2)
        for o in outliers:
            rows.append([
                Paragraph(str(o["column"]), body_style),
                Paragraph(str(o["row"]), right_align),
                Paragraph(format_number(o["value"]), right_align),
                Paragraph(str(o["expected"]), body_style),
                Paragraph(str(o["method"]), body_style)
            ])
            
        col_widths = [doc.width * 0.25, doc.width * 0.15, doc.width * 0.15, doc.width * 0.25, doc.width * 0.2]
        story.append(KeepTogether([data_table(h_row, rows, col_widths)]))
    else:
        story.append(Paragraph("No statistical outliers detected.", body_style))
        
    story.append(Spacer(1, 20))
    
    # ================= REGRESSION MODELS =================
    models = get_regression_models(dataset_info["id"])
    if models:
        section_header("09", "Regression Models")
        h_row = [Paragraph("<b>Target</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER)),
                 Paragraph("<b>Features</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER)),
                 Paragraph("<b>R² Test</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER, alignment=2)),
                 Paragraph("<b>Trained Date</b>", ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=9, textColor=PAPER))]
                 
        rows = []
        right_align = ParagraphStyle('ra', fontName='Helvetica', fontSize=9, alignment=2)
        for m in models:
            f_str = ", ".join(m["features"])
            if len(f_str) > 40: f_str = f_str[:37] + "..."
            dt = m["timestamp"].split("T")[0]
            rows.append([
                Paragraph(str(m["target"]), body_style),
                Paragraph(f_str, body_style),
                Paragraph(f"{m['r2_test']:.3f}", right_align),
                Paragraph(dt, body_style)
            ])
            
        col_widths = [doc.width * 0.2, doc.width * 0.45, doc.width * 0.15, doc.width * 0.2]
        story.append(KeepTogether([data_table(h_row, rows, col_widths)]))

    doc.build(story, canvasmaker=lambda *args, **kwargs: PremiumCanvas(*args, dataset_name=dataset_info["name"], gen_date=gen_date, **kwargs))
    buffer.seek(0)
    return buffer
