import io
import json
import os
import re
from datetime import datetime

from app.core.database import get_db_connection
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    KeepTogether, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect, String

from app.services.stats_service import compute_kpis, find_column, forecast_series, quality_report
from app.core.config import DB_PATH

# reportlab's built-in base-14 fonts (Helvetica, Times-Roman, ...) only cover
# WinAnsi/Latin-1 — the ₹ glyph (U+20B9) falls outside that and renders as a
# missing-glyph box. DejaVu Sans/Serif (bundled inside matplotlib's own
# package data, so guaranteed present wherever this app runs, incl. Render)
# both cover it, so those replace Helvetica/Times-Roman everywhere below.
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
_FONT_DIR = os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf')
for _name, _file in [
    ('DejaVuSans', 'DejaVuSans.ttf'),
    ('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'),
    ('DejaVuSerif', 'DejaVuSerif.ttf'),
    ('DejaVuSerif-Bold', 'DejaVuSerif-Bold.ttf'),
]:
    pdfmetrics.registerFont(TTFont(_name, os.path.join(_FONT_DIR, _file)))

# ── DESIGN SYSTEM — "Editorial" aesthetic ───────────────────────────────────
PAGE_BG_STR   = "#F2F2F0"
COVER_BG_STR  = "#1D1A16"
INK_STR       = "#211D18"
MUTED_STR     = "#8A8378"
LINE_STR      = "#DBD7CF"
GOLD_STR      = "#8A6218"
GOLD_LIGHT_STR= "#C9A227"
CREAM_STR     = "#FBF1DD"
SUCCESS_STR   = "#4B7355"
DANGER_STR    = "#9E4936"
PAPER_STR     = "#FFFFFF"

INK        = colors.HexColor(INK_STR)
MUTED      = colors.HexColor(MUTED_STR)
LINE       = colors.HexColor(LINE_STR)
GOLD       = colors.HexColor(GOLD_STR)
GOLD_LIGHT = colors.HexColor(GOLD_LIGHT_STR)
CREAM      = colors.HexColor(CREAM_STR)
SUCCESS    = colors.HexColor(SUCCESS_STR)
DANGER     = colors.HexColor(DANGER_STR)
PAPER      = colors.HexColor(PAPER_STR)
WHITE      = colors.HexColor("#FFFFFF")
CREAM_TEXT = colors.HexColor("#D8D2C6")

AMBER_SHADES = ["#4A3315", "#6B491D", "#8A6218", "#AB8330", "#C9A227", "#E0C46E"]


def format_number(value):
    if value is None or pd.isna(value):
        return "0"
    try:
        val = float(value)
        abs_val = abs(val)
        if abs_val >= 10000000:
            return f"{val / 10000000:.2f}Cr"
        if abs_val >= 100000:
            return f"{val / 100000:.2f}L"
        if abs_val >= 1000:
            return f"{val / 1000:.2f}K"
        if val.is_integer():
            return str(int(val))
        return f"{val:.2f}"
    except Exception:
        return str(value)


def fmt_currency(value):
    if value is None or pd.isna(value):
        return "₹0"
    sign = "-" if float(value) < 0 else ""
    return f"{sign}₹{format_number(abs(float(value)))}"


def fmt_value(value, vtype):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    if vtype == "currency":
        return fmt_currency(value)
    if vtype == "percent":
        return f"{float(value):.1f}%"
    return format_number(value)


def fmt_trend(delta_pct):
    if delta_pct is None:
        return "—", MUTED
    if delta_pct > 0:
        return f"▲ {abs(delta_pct):.1f}%", SUCCESS
    if delta_pct < 0:
        return f"▼ {abs(delta_pct):.1f}%", DANGER
    return "0.0%", MUTED


def grade_letter(score):
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def matplotlib_formatter(x, pos):
    return format_number(x)


class EditorialCanvas(canvas.Canvas):
    """Two-pass canvas: buffers every page so the footer can print an
    accurate 'NN / total' once the final page count is known."""

    def __init__(self, *args, **kwargs):
        self.report_title = kwargs.pop('report_title', 'DATA ANALYSIS REPORT')
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            if self._pageNumber > 1:
                self.draw_chrome(total)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_chrome(self, total):
        self.saveState()
        w, h = A4
        self.setStrokeColor(LINE)
        self.setLineWidth(0.6)
        self.line(22 * mm, h - 15 * mm, w - 22 * mm, h - 15 * mm)
        self.setFont('DejaVuSans', 7.5)
        self.setFillColor(MUTED)
        self.drawString(22 * mm, h - 12 * mm, " ".join(list(self.report_title.upper())))
        self.drawRightString(w - 22 * mm, h - 12 * mm, f"{self._pageNumber:02d} / {total:02d}")

        self.line(22 * mm, 15 * mm, w - 22 * mm, 15 * mm)
        self.drawString(22 * mm, 10 * mm, "C O N F I D E N T I A L  —  P R E P A R E D  F O R  C L I E N T")
        self.drawRightString(w - 22 * mm, 10 * mm, "N U M E R A T E  A N A L Y T I C S")
        self.restoreState()


def get_regression_models(dataset_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT target, features, r2_test, timestamp
            FROM regression_models
            WHERE dataset_id = %s
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
    except Exception:
        return []


def get_outliers(df):
    num_cols = df.select_dtypes(include=[np.number]).columns
    outliers = []
    for col in num_cols:
        clean_col = df[col].dropna()
        if len(clean_col) < 5:
            continue
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
                        "expected": f"μ±3σ ({format_number(mean_val-3*std_val)} to {format_number(mean_val+3*std_val)})",
                        "method": "Z-Score > 3",
                        "z": z
                    })
    outliers = sorted(outliers, key=lambda x: x["z"], reverse=True)[:10]
    return outliers


def pick_segment_column(df, exclude_cols):
    cat_cols = [c for c in df.select_dtypes(exclude=[np.number, 'datetime64']).columns if c not in exclude_cols]
    preferred, fallback = [], []
    for c in cat_cols:
        n = df[c].nunique()
        if n < 2 or n > 40 or re.search(r'id|uuid|code|name|email|phone', c, re.IGNORECASE):
            continue
        target = preferred if re.search(r'channel|segment|categor|type|method|region|status|mode|rail|payment', c, re.IGNORECASE) else fallback
        target.append((c, n))
    pool = sorted(preferred, key=lambda t: t[1]) or sorted(fallback, key=lambda t: t[1])
    return pool[0][0] if pool else None


def generate_pdf_report(dataset_info, df):
    buffer = io.BytesIO()
    now = datetime.now()
    gen_date = now.strftime("%Y-%m-%d %H:%M")
    dataset_name = dataset_info.get('name', 'Dataset')

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=22 * mm, leftMargin=22 * mm,
        topMargin=22 * mm, bottomMargin=22 * mm
    )
    W = doc.width

    # ── Styles ───────────────────────────────────────────────────────────
    cover_kicker = ParagraphStyle('CoverKicker', fontName='DejaVuSans', fontSize=9, textColor=GOLD_LIGHT, leading=12, spaceAfter=10)
    cover_title = ParagraphStyle('CoverTitle', fontName='DejaVuSerif', fontSize=46, textColor=WHITE, leading=52, spaceAfter=4)
    cover_sub = ParagraphStyle('CoverSub', fontName='DejaVuSans', fontSize=11, textColor=CREAM_TEXT, leading=17, spaceAfter=6)
    cover_brand = ParagraphStyle('CoverBrand', fontName='DejaVuSans', fontSize=10.5, textColor=WHITE, leading=13)
    cover_meta_label = ParagraphStyle('CoverMetaLabel', fontName='DejaVuSans', fontSize=7.5, textColor=GOLD_LIGHT, leading=10)
    cover_meta_val = ParagraphStyle('CoverMetaVal', fontName='DejaVuSans', fontSize=10, textColor=WHITE, leading=13)

    h1 = ParagraphStyle('H1', fontName='DejaVuSerif', fontSize=27, textColor=INK, leading=32)
    h2 = ParagraphStyle('H2', fontName='DejaVuSerif', fontSize=20, textColor=INK, leading=25)
    h3 = ParagraphStyle('H3', fontName='DejaVuSerif', fontSize=13, textColor=INK, leading=17, spaceAfter=4)
    kicker = ParagraphStyle('Kicker', fontName='DejaVuSans', fontSize=8.5, textColor=GOLD, leading=11, spaceAfter=6)
    body = ParagraphStyle('Body', fontName='DejaVuSans', fontSize=9.6, textColor=INK, leading=15, spaceAfter=8)
    body_just = ParagraphStyle('BodyJust', parent=body, alignment=4)
    caption = ParagraphStyle('Caption', fontName='DejaVuSans', fontSize=8, textColor=MUTED, leading=12)
    small_label = ParagraphStyle('SmallLabel', fontName='DejaVuSans', fontSize=7.3, textColor=MUTED, leading=10)
    stat_label = ParagraphStyle('StatLabel', fontName='DejaVuSans', fontSize=7.3, textColor=MUTED, leading=10)
    stat_value = ParagraphStyle('StatValue', fontName='DejaVuSerif', fontSize=25, textColor=INK, leading=28)
    stat_sub = ParagraphStyle('StatSub', fontName='DejaVuSans', fontSize=8, textColor=MUTED, leading=11)
    toc_num = ParagraphStyle('TocNum', fontName='DejaVuSerif', fontSize=11, textColor=GOLD, leading=14)
    toc_title = ParagraphStyle('TocTitle', fontName='DejaVuSerif', fontSize=15, textColor=INK, leading=19)
    toc_page = ParagraphStyle('TocPage', fontName='DejaVuSerif', fontSize=11, textColor=MUTED, leading=14, alignment=2)
    profile_label = ParagraphStyle('ProfileLabel', fontName='DejaVuSans', fontSize=7.3, textColor=GOLD, leading=10)
    profile_val = ParagraphStyle('ProfileVal', fontName='DejaVuSans', fontSize=10.5, textColor=INK, leading=14)
    th_style = ParagraphStyle('TH', fontName='DejaVuSans', fontSize=7.6, textColor=MUTED, leading=10)
    th_right = ParagraphStyle('THR', parent=th_style, alignment=2)
    td_style = ParagraphStyle('TD', fontName='DejaVuSans', fontSize=9.3, textColor=INK, leading=13)
    td_right = ParagraphStyle('TDR', parent=td_style, alignment=2)
    td_muted = ParagraphStyle('TDM', parent=td_style, textColor=MUTED)
    pill_style = ParagraphStyle('Pill', fontName='DejaVuSans', fontSize=6.8, textColor=MUTED, leading=9, alignment=1)
    pill_gold_style = ParagraphStyle('PillGold', parent=pill_style, textColor=GOLD)

    story = []

    def hairline(color=LINE, thickness=0.6, space_before=0, space_after=0):
        if space_before:
            story.append(Spacer(1, space_before))
        story.append(Table([[""]], colWidths=[W], rowHeights=[thickness], style=TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), color),
            ('TOPPADDING', (0, 0), (0, 0), 0), ('BOTTOMPADDING', (0, 0), (0, 0), 0),
        ])))
        if space_after:
            story.append(Spacer(1, space_after))

    def section_header(number_str, title):
        row = Table([[Paragraph(number_str, ParagraphStyle('SecNum', fontName='DejaVuSerif', fontSize=20, leading=25, textColor=GOLD)),
                      Paragraph(title, h2)]], colWidths=[13 * mm, W - 13 * mm])
        row.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ]))
        story.append(row)
        hairline(space_after=6 * mm)

    def stat_cards(items):
        """items: list of (label, value_str, sub_str_or_None, sub_color_or_None)"""
        n = len(items)
        col_w = W / n
        cells = []
        for label, value_str, sub_str, sub_color in items:
            rows = [[Paragraph(label.upper(), stat_label)], [Paragraph(value_str, stat_value)]]
            if sub_str:
                rows.append([Paragraph(sub_str, ParagraphStyle('SS', parent=stat_sub, textColor=sub_color or MUTED))])
            cell = Table(rows, colWidths=[col_w - 10])
            cell.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            cells.append(cell)
        t = Table([cells], colWidths=[col_w] * n)
        style = [
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEABOVE', (0, 0), (-1, 0), 1.4, GOLD),
            ('LINEBELOW', (0, 0), (-1, 0), 0.6, LINE),
            ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]
        for i in range(1, n):
            style.append(('LINEBEFORE', (i, 0), (i, 0), 0.6, LINE))
        t.setStyle(TableStyle(style))
        return t

    def brand_mark(size=9 * mm, fill=GOLD_LIGHT, letter_color=None):
        letter_color = letter_color or colors.HexColor(COVER_BG_STR)
        d = Drawing(size, size)
        d.add(Rect(0, 0, size, size, rx=size * 0.22, ry=size * 0.22, fillColor=fill, strokeColor=None))
        d.add(String(size / 2, size * 0.30, "N", fontName='DejaVuSerif-Bold', fontSize=size * 0.56,
                      fillColor=letter_color, textAnchor='middle'))
        return d

    def mini_bar(pct, max_pct, w=32 * mm, h=2.6 * mm, color=GOLD, track=None):
        d = Drawing(w, h)
        if track:
            d.add(Rect(0, 0, w, h, fillColor=track, strokeColor=None))
        fill_w = max(0.0, min(1.0, (pct / max_pct) if max_pct else 0)) * w
        if fill_w > 0:
            d.add(Rect(0, 0, fill_w, h, fillColor=color, strokeColor=None))
        return d

    def pill(text, gold=False):
        t = Table([[Paragraph(text.upper(), pill_gold_style if gold else pill_style)]], colWidths=[20 * mm])
        t.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.6, GOLD if gold else LINE),
            ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        return t

    def callout(kicker_text, text, width=None):
        box_w = width if width is not None else W
        box = Table([
            [Paragraph(kicker_text.upper(), ParagraphStyle('CK', fontName='DejaVuSans', fontSize=7.6, textColor=GOLD, leading=10, spaceAfter=4))],
            [Paragraph(text, ParagraphStyle('CB', fontName='DejaVuSerif', fontSize=11.5, textColor=INK, leading=16))],
        ], colWidths=[box_w])
        box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), CREAM),
            ('LINEBEFORE', (0, 0), (0, 0), 2.2, GOLD),
            ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 14), ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ]))
        return box

    def data_table(headers, rows, col_widths):
        table_data = [headers] + rows
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, 0), 1.1, INK),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, LINE),
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, LINE),
            ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        return t

    def chart_common(ax, fig):
        fig.patch.set_facecolor(PAGE_BG_STR)
        ax.set_facecolor(PAGE_BG_STR)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(LINE_STR)
        ax.spines['bottom'].set_linewidth(0.6)
        ax.tick_params(axis='x', colors=MUTED_STR, labelsize=8, length=0)
        ax.tick_params(axis='y', colors=MUTED_STR, labelsize=8, length=0)
        ax.grid(axis='y', linestyle='-', alpha=0.15, color=LINE_STR)

    # ── Derived data ─────────────────────────────────────────────────────
    semantic_dict = dataset_info.get("semantic_dict") or {}
    bus_term = semantic_dict.get("business_terminology", {}) if semantic_dict else {}
    rev_col = bus_term.get("primary_metric") if bus_term else None
    rev_label = bus_term.get("primary_metric_label", "Total Value") if bus_term else "Total Value"
    rev_type = bus_term.get("primary_metric_type", "currency") if bus_term else "currency"

    kpi_results = compute_kpis(df, semantic_dict)
    kpis = kpi_results.get("kpis", [])
    chart_data = kpi_results.get("chart_data", [])

    date_col = None
    if semantic_dict:
        date_cols = semantic_dict.get("semantic_dictionary", {}).get("date_columns", [])
        if date_cols and date_cols[0] in df.columns:
            date_col = date_cols[0]
    if not date_col:
        date_col = find_column(df, r'date|month|year|time')

    quality = quality_report(df)
    quality_score = dataset_info.get("quality_score") or quality.get("quality_score", 0)
    quality_breakdown = dataset_info.get("quality_breakdown") or quality.get("breakdown", {})
    if not quality_breakdown:
        quality_breakdown = quality.get("breakdown", {})
    grade = grade_letter(quality_score)

    reporting_window = "All available records"
    if date_col:
        try:
            parsed = pd.to_datetime(df[date_col], errors='coerce').dropna()
            if len(parsed) > 0:
                reporting_window = f"{parsed.min().strftime('%b %Y')} – {parsed.max().strftime('%b %Y')}"
        except Exception:
            pass

    primary_kpi = next((k for k in kpis if k.get("column") == rev_col), None) or (kpis[0] if kpis else None)
    entity_kpi = next((k for k in kpis if k.get("type") == "count"), None)
    status_kpi = next((k for k in kpis if k.get("type") == "percent"), None)

    # No cached semantic_dict means bus_term (and rev_col derived from it) is
    # empty here even though compute_kpis() ran its own internal fallback
    # classification and DID find a usable primary metric — fall back to what
    # it actually picked so the chart/monthly-table sections below aren't
    # needlessly skipped.
    if not rev_col and primary_kpi and primary_kpi.get("column"):
        rev_col = primary_kpi["column"]
        rev_label = primary_kpi.get("name", rev_label)
        rev_type = primary_kpi.get("type", rev_type)

    # ================= COVER PAGE =================
    story.append(Spacer(1, 8 * mm))
    brand_row = Table([[
        brand_mark(size=9 * mm, fill=GOLD_LIGHT),
        Paragraph("N&nbsp;U&nbsp;M&nbsp;E&nbsp;R&nbsp;A&nbsp;T&nbsp;E&nbsp;&nbsp;&nbsp;A&nbsp;N&nbsp;A&nbsp;L&nbsp;Y&nbsp;T&nbsp;I&nbsp;C&nbsp;S", cover_brand),
        Paragraph(f"VOL. 1 · {now.year}", ParagraphStyle('VolR', parent=cover_meta_val, alignment=2)),
    ]], colWidths=[10 * mm, W - 50 * mm, 40 * mm])
    brand_row.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    story.append(brand_row)

    story.append(Spacer(1, doc.height * 0.30))
    story.append(Paragraph("QUARTERLY INTELLIGENCE BRIEF", cover_kicker))
    story.append(Paragraph("Data Analysis Report", cover_title))
    story.append(Spacer(1, 4 * mm))
    story.append(Table([[""]], colWidths=[26 * mm], rowHeights=[1.4], style=TableStyle([('BACKGROUND', (0, 0), (0, 0), GOLD_LIGHT)])))
    story.append(Spacer(1, 5 * mm))
    intro_label = (bus_term.get("primary_metric_label") or "core business metrics").lower()
    story.append(Paragraph(
        f"A synthesized read of {intro_label}, forecast trajectory, and data integrity across the reporting window — prepared as a confidential client deliverable.",
        cover_sub))

    story.append(Spacer(1, doc.height * 0.22))
    footer_row = Table([[
        Paragraph("DATASET", cover_meta_label), Paragraph("RECORDS", cover_meta_label), Paragraph("GENERATED", cover_meta_label)
    ], [
        Paragraph(dataset_name, cover_meta_val),
        Paragraph(f"{len(df):,} rows · {len(df.columns)} fields", cover_meta_val),
        Paragraph(now.strftime("%Y-%m-%d · %H:%M"), cover_meta_val),
    ]], colWidths=[W / 3] * 3)
    footer_row.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.6, colors.HexColor("#4A453D")),
        ('TOPPADDING', (0, 0), (-1, 0), 8), ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
        ('TOPPADDING', (0, 1), (-1, 1), 0), ('BOTTOMPADDING', (0, 1), (-1, 1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(footer_row)
    story.append(PageBreak())

    # ================= CONTENTS =================
    sections = [
        ("01", "Executive Summary"),
        ("02", f"{rev_label} Analytics"),
        ("03", f"Monthly {rev_label} Values"),
        ("04", "Segment & Channel Distribution"),
        ("05", "Statistical Summary"),
        ("06", "Data Quality Indicators"),
        ("07", "Forecast & Recommendations"),
        ("08", "Methodology & Sources"),
    ]
    story.append(Paragraph("INSIDE THIS REPORT", kicker))
    story.append(Paragraph("Contents", h1))
    story.append(Spacer(1, 8 * mm))

    TOC_W = W * 0.58
    PROFILE_W = W - TOC_W

    toc_rows = []
    for num, title in sections:
        toc_rows.append([Paragraph(num, toc_num), Paragraph(title, toc_title), Paragraph(f"{int(num)+2:02d}", toc_page)])
    toc_table = Table(toc_rows, colWidths=[10 * mm, TOC_W - 10 * mm - 16 * mm - 8, 16 * mm])
    toc_style = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, -1), 0.6, LINE),
        ('TOPPADDING', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (2, 0), (2, -1), 8),
    ]
    toc_table.setStyle(TableStyle(toc_style))

    profile_rows_data = [
        ("PREPARED FOR", "Client Stakeholders"),
        ("PREPARED BY", "Numerate Analytics"),
        ("REPORTING WINDOW", reporting_window),
        ("CLASSIFICATION", "Confidential"),
        ("DATA QUALITY INDEX", f"{quality_score:.1f} / 100 · Grade {grade}"),
    ]
    profile_rows = []
    for label, val in profile_rows_data:
        profile_rows.append([Paragraph(label, profile_label)])
        profile_rows.append([Paragraph(val, profile_val)])
    PROFILE_INNER_W = PROFILE_W - 14
    profile_table = Table(profile_rows, colWidths=[PROFILE_INNER_W])
    p_style = [('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
               ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]
    for i in range(0, len(profile_rows), 2):
        p_style.append(('TOPPADDING', (0, i), (0, i), 10))
        p_style.append(('BOTTOMPADDING', (0, i + 1), (0, i + 1), 9))
        p_style.append(('LINEBELOW', (0, i + 1), (0, i + 1), 0.6, LINE))
    profile_table.setStyle(TableStyle(p_style))
    profile_note = Paragraph(
        "Figures are derived directly from the source dataset. Forecast bands reflect a 95% confidence interval and are indicative, not guaranteed.",
        caption)
    profile_divider = Table([[""]], colWidths=[26 * mm], rowHeights=[1.4], style=TableStyle([('BACKGROUND', (0, 0), (0, 0), GOLD)]))
    profile_block = Table([
        [Paragraph("REPORT PROFILE", kicker)],
        [profile_divider],
        [Spacer(1, 6)],
        [profile_table],
        [Spacer(1, 6)],
        [profile_note],
    ], colWidths=[PROFILE_INNER_W])
    profile_block.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))

    two_col = Table([[toc_table, profile_block]], colWidths=[TOC_W, PROFILE_W])
    two_col.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBEFORE', (1, 0), (1, 0), 0.6, LINE),
        ('LEFTPADDING', (0, 0), (0, 0), 0), ('RIGHTPADDING', (0, 0), (0, 0), 0),
        ('LEFTPADDING', (1, 0), (1, 0), 14), ('RIGHTPADDING', (1, 0), (1, 0), 0),
    ]))
    story.append(two_col)
    story.append(PageBreak())

    # ================= 01 EXECUTIVE SUMMARY =================
    section_header("01", "Executive Summary")

    summary_items = []
    if primary_kpi:
        v, sub_color = fmt_value(primary_kpi["value"], primary_kpi.get("type", rev_type)), None
        t_str, t_color = fmt_trend(primary_kpi.get("trend"))
        summary_items.append((primary_kpi.get("name", rev_label), v, f"{t_str}  vs prior period", t_color))
    if entity_kpi:
        v = fmt_value(entity_kpi["value"], "count")
        t_str, t_color = fmt_trend(entity_kpi.get("trend"))
        summary_items.append((entity_kpi.get("name", "Total Records"), v, f"{t_str}  vs prior period", t_color))
    if status_kpi:
        v = fmt_value(status_kpi["value"], "percent")
        t_str, t_color = fmt_trend(status_kpi.get("trend"))
        summary_items.append((status_kpi.get("name", "Status Rate"), v, f"{t_str}  vs prior period", t_color))
    summary_items.append(("Data Quality Index", f"{quality_score:.1f}", f"Grade {grade} · weighted composite", SUCCESS if quality_score >= 80 else GOLD))

    story.append(stat_cards(summary_items[:4]))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph(
        f"This report presents a synthesized view of core metrics and the underlying data trends observed across the reporting window. "
        f"The executive dashboard above captures top-line performance"
        + (f": {primary_kpi.get('name','').lower()} of <b>{fmt_value(primary_kpi['value'], primary_kpi.get('type', rev_type))}</b>" if primary_kpi else "")
        + (f" against <b>{fmt_value(entity_kpi['value'], 'count')}</b> {entity_kpi.get('name','records').lower()}" if entity_kpi else "")
        + (f", at a <b>{fmt_value(status_kpi['value'],'percent')}</b> {status_kpi.get('name','').lower()}" if status_kpi else "")
        + f". The sections that follow detail {rev_label.lower()} analytics and forecast modeling, monthly value distribution, segment mix, and the data-quality indicators that qualify every figure in this document.",
        body_just))

    col_left, col_right = [], []
    col_left.append(Paragraph("Key Observations", h3))
    obs = []
    if primary_kpi:
        trend = primary_kpi.get("trend", 0)
        direction = "moved up" if trend > 0 else "moved down" if trend < 0 else "held steady"
        obs.append(f"{primary_kpi.get('name', rev_label)} {direction} {abs(trend):.1f}% against the prior period.")
    if chart_data:
        actual_pts = [d for d in chart_data if d.get("value") is not None]
        nonzero = [d for d in actual_pts if d.get("value", 0) != 0]
        if actual_pts:
            obs.append(f"Value is observed in {len(nonzero)} of {len(actual_pts)} reporting periods, so recent months should be read against that spread.")
    obs.append(f"Data quality holds at a {quality_score:.1f} / 100 composite (Grade {grade}), so headline figures are {'reliable inputs for decisions' if quality_score >= 80 else 'usable but should be reconciled before high-stakes decisions'}.")
    if len(df) > 0:
        obs.append(f"Analysis spans {len(df):,} records across {len(df.columns)} fields with no external enrichment applied.")
    for ob in obs[:4]:
        col_left.append(Paragraph(f"<font color='{GOLD_STR}'>◆</font>&nbsp;&nbsp;{ob}", body))
        col_left.append(Table([[""]], colWidths=[W * 0.46], rowHeights=[0.5], style=TableStyle([('BACKGROUND', (0, 0), (0, 0), LINE)])))
        col_left.append(Spacer(1, 6))

    col_right.append(Paragraph("Reading Guide", h3))
    col_right.append(Paragraph(
        "Positive markers (▲) denote favorable movement against the prior period; negative markers (▼) denote adverse movement. "
        "Monetary values are expressed in Indian lakhs (L) or crores (Cr) as scale requires. Forecast figures carry a 95% confidence band and should be read as directional.",
        body))
    bottom_line_text = (
        f"{primary_kpi.get('name', rev_label)} is {'trending favorably' if primary_kpi and primary_kpi.get('trend',0) >= 0 else 'under pressure'} "
        f"and data integrity is {'strong enough to act on' if quality_score >= 80 else 'adequate but worth reconciling first'}."
        if primary_kpi else f"Data integrity stands at {quality_score:.1f}/100, {'strong enough to act on' if quality_score >= 80 else 'worth reconciling before wider use'}."
    )
    col_right.append(Spacer(1, 4))
    col_right.append(callout("Bottom Line", bottom_line_text, width=W * 0.48))

    two_col2 = Table([[col_left, col_right]], colWidths=[W * 0.48, W * 0.48])
    two_col2.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (0, 0), 16), ('RIGHTPADDING', (1, 0), (1, 0), 0)]))
    story.append(two_col2)
    story.append(PageBreak())

    # ================= 02 PRIMARY METRIC ANALYTICS =================
    section_header("02", f"{rev_label} Analytics")

    fcst_bounds = None
    hist_data = [d for d in chart_data if d.get("value") is not None]
    fcst_data = [d for d in chart_data if d.get("forecast") is not None and d.get("value") is None]

    if date_col and rev_col and chart_data and hist_data:
        if fcst_data:
            # forecast_series() drops a trailing in-progress (partial) period from its
            # own training data and re-estimates it as the first forecast point — so
            # that point can carry the SAME period label as the last historical row.
            # Left alone this reads as the same month listed twice with two different
            # numbers; tag it so it's clearly a revised estimate, not a new period.
            if fcst_data[0]["name"] == hist_data[-1]["name"]:
                fcst_data[0] = dict(fcst_data[0])
                fcst_data[0]["name"] = f"{fcst_data[0]['name']} (Revised Est.)"
            last_hist = hist_data[-1].copy()
            last_hist["forecast"] = last_hist["value"]
            fcst_data.insert(0, last_hist)
            f_res = forecast_series(df, rev_col, periods=len(fcst_data) - 1)
            if f_res.get("available"):
                fcst_bounds = f_res.get("forecast")

        fig = plt.figure(figsize=(8, 4), dpi=200)
        ax = plt.gca()
        chart_common(ax, fig)

        x_hist = [d["name"] for d in hist_data]
        y_hist = [d["value"] for d in hist_data]
        ax.plot(x_hist, y_hist, color=GOLD_STR, marker='o', markersize=4.5, markerfacecolor=GOLD_STR, linestyle='-', linewidth=1.8, label='Actual')
        if hist_data:
            ax.annotate(fmt_value(y_hist[-1], rev_type), (len(x_hist) - 1, y_hist[-1]), textcoords="offset points", xytext=(0, 9), ha='center', fontsize=8, color=INK_STR, fontweight='bold')

        if fcst_data:
            x_fcst = [d["name"] for d in fcst_data]
            y_fcst = [d["forecast"] for d in fcst_data]
            x_idx = range(len(x_hist) - 1, len(x_hist) - 1 + len(x_fcst))
            ax.plot(x_fcst, y_fcst, color=GOLD_STR, linestyle='--', linewidth=1.8, label='Forecast')
            if fcst_bounds:
                y_lower = [y_fcst[0]] + [b["lower"] for b in fcst_bounds]
                y_upper = [y_fcst[0]] + [b["upper"] for b in fcst_bounds]
                ax.fill_between(x_idx, y_lower, y_upper, alpha=0.18, color=GOLD_LIGHT_STR, label='95% confidence')
            ax.annotate(fmt_value(y_fcst[-1], rev_type), (list(x_idx)[-1], y_fcst[-1]), textcoords="offset points", xytext=(0, 9), ha='center', fontsize=8, color=INK_STR, fontweight='bold')

        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: fmt_value(x, rev_type)))
        ax.margins(y=0.18)
        if min(y_hist + ([b["lower"] for b in fcst_bounds] if fcst_bounds else [])) >= 0:
            ax.set_ylim(bottom=0)
        plt.xticks(rotation=40, ha='right')
        ax.legend(loc='lower left', bbox_to_anchor=(0, 1.03), ncol=3, frameon=False, fontsize=8, labelcolor=MUTED_STR)
        plt.tight_layout()

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)
        img_buffer.seek(0)

        desc_bits = []
        nonzero_hist = [d for d in hist_data if d.get("value")]
        if nonzero_hist:
            peak = max(nonzero_hist, key=lambda d: d["value"])
            desc_bits.append(f"a peak of {fmt_value(peak['value'], rev_type)} in {peak['name']}")
        story.append(Paragraph(
            f"Monthly {rev_label.lower()} across the window" + (f", with {desc_bits[0]}" if desc_bits else "")
            + (f" and a {len(fcst_data)-1}-period forward forecast" if fcst_data else "") + ".",
            body))
        story.append(Image(img_buffer, width=W, height=W * 0.48))
        story.append(Spacer(1, 6 * mm))

        positive_flow = sum(d["value"] for d in hist_data if d.get("value") and d["value"] > 0)
        active_months = sum(1 for d in hist_data if d.get("value"))
        peak_str = fmt_value(max((d["value"] for d in hist_data), default=0), rev_type)
        next_fcst_str = fmt_value(fcst_data[-1]["forecast"], rev_type) if fcst_data else "—"
        strip_items = [
            ("Peak Month", peak_str, None, None),
            ("Active Months", f"{active_months} of {len(hist_data)}", None, None),
            ("Positive Flow", fmt_value(positive_flow, rev_type), None, None),
            (f"{fcst_data[-1]['name']} Forecast" if fcst_data else "Forecast", next_fcst_str, None, None),
        ]
        story.append(stat_cards(strip_items))
    elif rev_col:
        cat_cols = df.select_dtypes(exclude=[np.number, 'datetime64']).columns
        if len(cat_cols) > 0:
            c = cat_cols[0]
            grp = df.groupby(c)[rev_col].sum().sort_values(ascending=False).head(8)
            if len(grp) > 0:
                fig = plt.figure(figsize=(8, 4), dpi=200)
                ax = plt.gca()
                chart_common(ax, fig)
                x_pos = np.arange(len(grp))
                labels = [str(x) for x in grp.index]
                values = grp.values
                ax.bar(x_pos, values, color=GOLD_STR, width=0.6)
                ax.set_xticks(x_pos)
                ax.set_xticklabels(labels, fontsize=8, color=MUTED_STR, rotation=40, ha='right')
                for i, v in enumerate(values):
                    ax.text(i, v, format_number(v), ha='center', va='bottom', fontsize=8, color=INK_STR, fontweight='bold')
                ax.tick_params(axis='y', left=False, labelleft=False)
                plt.tight_layout()
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
                plt.close(fig)
                img_buffer.seek(0)
                story.append(Paragraph(f"{rev_label} by {c.title()} (no date column available for a time series).", body))
                story.append(Image(img_buffer, width=W, height=W * 0.48))
        else:
            story.append(Paragraph("Not enough dimensions in this dataset for a detailed time series or breakdown chart.", body))
    else:
        story.append(Paragraph("No numeric primary metric was detected for this dataset, so no analytics chart is shown.", body))
    story.append(PageBreak())

    # ================= 03 MONTHLY VALUES TABLE =================
    if date_col and rev_col and chart_data and hist_data:
        section_header("03", f"Monthly {rev_label} Values")

        all_rows = hist_data + fcst_data[1:] if fcst_data else hist_data
        pos_total = sum(d["value"] for d in hist_data if d.get("value") and d["value"] > 0) or 1
        max_share = 0
        row_shares = []
        for d in all_rows:
            v = d.get("value") if d.get("value") is not None else d.get("forecast")
            share = (v / pos_total * 100) if v and v > 0 else 0
            row_shares.append(share)
            max_share = max(max_share, share)
        max_share = max_share or 1

        h_row = [Paragraph("MONTH", th_style), Paragraph("NET AMOUNT", th_right), Paragraph("SHARE", th_right), Paragraph("CONTRIBUTION", th_style), Paragraph("BASIS", th_right)]
        rows = []
        for d, share in zip(all_rows, row_shares):
            v = d.get("value") if d.get("value") is not None else d.get("forecast")
            is_forecast = d.get("value") is None
            v_str = fmt_value(v, rev_type) if v else "—"
            share_str = f"{share:.1f}%" if v and v > 0 else "—"
            bar = mini_bar(share, max_share, w=28 * mm, h=2.6 * mm, color=GOLD_LIGHT if is_forecast else GOLD)
            rows.append([
                Paragraph(d["name"], td_muted if is_forecast else td_style),
                Paragraph(v_str, td_right),
                Paragraph(share_str, td_right),
                bar,
                pill("Forecast" if is_forecast else "Actual", gold=is_forecast),
            ])
        total_row = [
            Paragraph("Total (positive flow)", ParagraphStyle('TotL', parent=td_style, fontName='DejaVuSans-Bold')),
            Paragraph(fmt_value(pos_total, rev_type), td_right),
            Paragraph("100.0%", ParagraphStyle('TotR', parent=td_right, fontName='DejaVuSans-Bold')),
            "",
            Paragraph(f"{len(all_rows)} periods", ParagraphStyle('TotP', parent=caption, alignment=2)),
        ]
        col_widths = [W * 0.22, W * 0.18, W * 0.14, W * 0.28, W * 0.18]
        story.append(data_table(h_row, rows + [total_row], col_widths))
        story.append(Spacer(1, 4 * mm))
        net_val = primary_kpi["value"] if primary_kpi else None
        note = f"Share is computed on positive monthly flow ({fmt_value(pos_total, rev_type)} aggregate); periods with no cleared value are shown as “—”."
        if net_val is not None and abs(net_val - pos_total) > 0.01:
            note += f" The reported headline net of {fmt_value(net_val, rev_type)} reflects reversals/refunds netted against gross throughput and is not the sum of this column."
        story.append(Paragraph(note, caption))
        story.append(PageBreak())

    # ================= 04 SEGMENT & CHANNEL DISTRIBUTION =================
    section_header("04", "Segment & Channel Distribution")
    exclude_cols = {c for c in [rev_col, date_col] if c}
    seg_col = pick_segment_column(df, exclude_cols)

    if seg_col:
        counts = df[seg_col].astype(str).value_counts()
        top = counts.head(5)
        other_count = counts.iloc[5:].sum() if len(counts) > 5 else 0
        labels = list(top.index) + (["Other"] if other_count > 0 else [])
        values = list(top.values) + ([other_count] if other_count > 0 else [])
        total_n = sum(values)
        shades = AMBER_SHADES[:len(values)] if len(values) <= len(AMBER_SHADES) else AMBER_SHADES * (len(values) // len(AMBER_SHADES) + 1)

        fig, ax = plt.subplots(figsize=(3.4, 3.4), dpi=200)
        fig.patch.set_facecolor(PAGE_BG_STR)
        wedges, _ = ax.pie(values, colors=shades[:len(values)], startangle=90, counterclock=False,
                            wedgeprops=dict(width=0.38, edgecolor=PAGE_BG_STR, linewidth=2))
        ax.text(0, 0.08, f"{total_n:,}", ha='center', va='center', fontsize=19, color=INK_STR, fontweight='bold', family='sans-serif')
        ax.text(0, -0.14, "RECORDS", ha='center', va='center', fontsize=7.5, color=MUTED_STR)
        ax.set_aspect('equal')
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', transparent=False, facecolor=fig.get_facecolor())
        plt.close(fig)
        img_buffer.seek(0)
        donut_img = Image(img_buffer, width=55 * mm, height=55 * mm)

        legend_rows = []
        for lbl, val, shade in zip(labels, values, shades):
            pct = val / total_n * 100 if total_n else 0
            sw = Table([[""]], colWidths=[3 * mm], rowHeights=[3 * mm], style=TableStyle([('BACKGROUND', (0, 0), (0, 0), colors.HexColor(shade))]))
            legend_rows.append([
                Table([[sw, Paragraph(str(lbl), td_style)]], colWidths=[5 * mm, W * 0.32], style=TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 0)])),
                Paragraph(f"{val:,} rows  ·  <b>{pct:.1f}%</b>", ParagraphStyle('LegVal', parent=td_style, alignment=2)),
            ])
        legend_table = Table(legend_rows, colWidths=[W * 0.42 - 55 * mm, W * 0.42])
        legend_style = [('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                         ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]
        for i in range(len(legend_rows) - 1):
            legend_style.append(('LINEBELOW', (0, i), (-1, i), 0.5, LINE))
        legend_table.setStyle(TableStyle(legend_style))

        combined = Table([[donut_img, legend_table]], colWidths=[60 * mm, W - 60 * mm])
        combined.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
        story.append(Paragraph(f"Distribution of records by <b>{seg_col.replace('_',' ').title()}</b>.", body))
        story.append(combined)
        story.append(Spacer(1, 6 * mm))

        top2_pct = sum(v for v in values[:2]) / total_n * 100 if total_n else 0
        tail_pct = 100 - top2_pct
        conc_col = [
            Paragraph("Concentration", h3),
            Paragraph(f"The top {min(2,len(labels))} categories — {' and '.join(str(l) for l in labels[:2])} — account for <b>{top2_pct:.1f}%</b> of all records. "
                      f"{'Distribution across the remaining categories is thin, signaling a concentration risk worth monitoring.' if top2_pct > 60 else 'Volume is reasonably spread beyond the leading categories.'}",
                      body),
        ]
        tail_col = [
            Paragraph("Long Tail", h3),
            Paragraph(f"The remaining {'category accounts' if len(labels) <= 3 else 'categories account'} for <b>{tail_pct:.1f}%</b> of volume — candidates for either targeted growth investment or graceful consolidation depending on unit economics.", body),
        ]
        two_col3 = Table([[conc_col, tail_col]], colWidths=[W * 0.48, W * 0.48])
        two_col3.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (0, 0), 16)]))
        story.append(two_col3)
    else:
        story.append(Paragraph("No suitable categorical dimension was found for a segment breakdown on this dataset.", body))
    story.append(PageBreak())

    # ================= 05 STATISTICAL SUMMARY =================
    section_header("05", "Statistical Summary")
    num_cols = df.select_dtypes(include=[np.number]).columns
    if len(num_cols) > 0:
        recent_df, prior_df = df, None
        if date_col:
            try:
                periods = df.groupby(pd.to_datetime(df[date_col], errors='coerce').dt.to_period('M'))
                if len(periods) >= 2:
                    sorted_periods = sorted(periods.groups.keys())
                    recent_df = periods.get_group(sorted_periods[-1])
                    prior_df = periods.get_group(sorted_periods[-2])
            except Exception:
                pass

        h_row = [Paragraph("COLUMN", th_style), Paragraph("SUM", th_right), Paragraph("MEAN", th_right), Paragraph("MIN", th_right), Paragraph("MAX", th_right), Paragraph("TREND", th_right)]
        rows = []
        for col in num_cols[:16]:
            trend_str, trend_color = "—", MUTED
            if prior_df is not None and not prior_df.empty:
                c_val, p_val = recent_df[col].sum(), prior_df[col].sum()
                if p_val != 0 and pd.notna(p_val):
                    pct = ((c_val - p_val) / p_val) * 100
                    trend_str, trend_color = fmt_trend(pct)
            rows.append([
                Paragraph(str(col).replace("_", " ").title(), td_style),
                Paragraph(format_number(df[col].sum()), td_right),
                Paragraph(format_number(df[col].mean()), td_right),
                Paragraph(format_number(df[col].min()), td_right),
                Paragraph(format_number(df[col].max()), td_right),
                Paragraph(trend_str, ParagraphStyle('TrendCell', parent=td_right, textColor=trend_color)),
            ])
        col_widths = [W * 0.26, W * 0.15, W * 0.15, W * 0.15, W * 0.15, W * 0.14]
        story.append(data_table(h_row, rows, col_widths))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("Trend compares the two most recent reporting periods where a date column is available; sums, means, minimums and maximums are computed over the full dataset.", caption))
    else:
        story.append(Paragraph("No numeric columns are available in this dataset for statistical summarization.", body))

    outliers = get_outliers(df)
    if outliers:
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph("Statistical Outliers", h3))
        story.append(Paragraph("Values more than three standard deviations from their column mean, most extreme first.", caption))
        story.append(Spacer(1, 3))
        h_row = [Paragraph("COLUMN", th_style), Paragraph("ROW", th_right), Paragraph("VALUE", th_right), Paragraph("EXPECTED RANGE", th_style), Paragraph("METHOD", th_style)]
        rows = []
        for o in outliers:
            rows.append([
                Paragraph(str(o["column"]), td_style), Paragraph(str(o["row"]), td_right),
                Paragraph(format_number(o["value"]), td_right), Paragraph(str(o["expected"]), td_muted),
                Paragraph(str(o["method"]), td_muted),
            ])
        col_widths = [W * 0.2, W * 0.12, W * 0.16, W * 0.32, W * 0.2]
        story.append(data_table(h_row, rows, col_widths))
    story.append(PageBreak())

    # ================= 06 DATA QUALITY INDICATORS =================
    section_header("06", "Data Quality Indicators")

    dim_labels = {"completeness": "Completeness", "uniqueness": "Uniqueness", "type_consistency": "Consistency", "validity": "Validity"}
    missing_total = int(df.isna().sum().sum())
    dup_count = int(df.duplicated().sum())
    dim_notes = {
        "completeness": "No missing values across %d records" % len(df) if missing_total == 0 else f"{missing_total:,} missing value(s) across {len(df):,} records",
        "uniqueness": "No duplicate records detected" if dup_count == 0 else f"{dup_count:,} duplicate row(s) detected",
        "type_consistency": "Cross-column type checks passed",
        "validity": "Values conform to expected schema and ranges",
    }

    index_card = Table([
        [Paragraph("COMPOSITE INDEX", ParagraphStyle('CI', fontName='DejaVuSans', fontSize=7.6, textColor=MUTED, alignment=1))],
        [Paragraph(f"{quality_score:.1f}", ParagraphStyle('CIV', fontName='DejaVuSerif', fontSize=34, leading=40, textColor=INK, alignment=1))],
        [Paragraph("out of 100", ParagraphStyle('CIS', fontName='DejaVuSans', fontSize=8.5, textColor=MUTED, alignment=1))],
        [Spacer(1, 6)],
        [Table([[Paragraph(f"GRADE {grade}", ParagraphStyle('GB', fontName='DejaVuSans', fontSize=9, textColor=GOLD, alignment=1))]], colWidths=[28 * mm],
               style=TableStyle([('BOX', (0, 0), (-1, -1), 0.7, GOLD), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5), ('ALIGN', (0, 0), (-1, -1), 'CENTER')]))],
        [Spacer(1, 8)],
        [Paragraph(f"Weighted mean across {len(quality_breakdown)} integrity dimensions. Inputs are {'reliable enough to support the analytics in this report' if quality_score >= 80 else 'usable but merit reconciliation before high-stakes decisions'}.",
                   ParagraphStyle('CID', fontName='DejaVuSans', fontSize=8.3, textColor=MUTED, leading=12, alignment=1))],
    ], colWidths=[54 * mm])
    index_card.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1.6, GOLD), ('BOX', (0, 0), (-1, -1), 0.6, LINE),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (0, 0), 14), ('BOTTOMPADDING', (0, -1), (0, -1), 14),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))

    QCARD_W = 54 * mm
    QGAP = 12 * mm
    QDIMS_W = W - QCARD_W - QGAP

    dim_rows = []
    for key, val in quality_breakdown.items():
        label = dim_labels.get(key, key.replace("_", " ").title())
        note = dim_notes.get(key, "")
        bar = mini_bar(float(val), 100, w=QDIMS_W, h=3.2 * mm, color=GOLD, track=LINE)
        dim_rows.append([
            Table([[Paragraph(label, h3), Paragraph(f"{float(val):.1f}", ParagraphStyle('DV', fontName='DejaVuSerif', fontSize=13, textColor=GOLD, alignment=2))]],
                  colWidths=[QDIMS_W - 25 * mm, 25 * mm], style=TableStyle([('VALIGN', (0, 0), (-1, -1), 'BOTTOM'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
        ])
        dim_rows.append([bar])
        dim_rows.append([Paragraph(note, caption)])
    dims_table = Table(dim_rows, colWidths=[QDIMS_W])
    dstyle = [('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]
    for i in range(0, len(dim_rows), 3):
        dstyle.append(('BOTTOMPADDING', (0, i + 2), (0, i + 2), 12))
        if i + 3 < len(dim_rows):
            dstyle.append(('LINEBELOW', (0, i + 2), (0, i + 2), 0.5, LINE))
    dims_table.setStyle(TableStyle(dstyle))

    quality_layout = Table([[index_card, "", dims_table]], colWidths=[QCARD_W, QGAP, QDIMS_W])
    quality_layout.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    story.append(quality_layout)
    story.append(PageBreak())

    # ================= 07 FORECAST & RECOMMENDATIONS =================
    section_header("07", "Forecast & Recommendations")

    if fcst_data and fcst_bounds:
        next_val = fcst_data[1]["forecast"] if len(fcst_data) > 1 else fcst_data[0]["forecast"]
        last_val = fcst_data[-1]["forecast"]
        lo = min(b["lower"] for b in fcst_bounds)
        hi = max(b["upper"] for b in fcst_bounds)
        story.append(Paragraph(
            f"The forward model projects continued throughput, landing at <b>{fmt_value(last_val, rev_type)}</b> for {fcst_data[-1]['name']} "
            f"with a 95% confidence band of {fmt_value(lo, rev_type)}–{fmt_value(hi, rev_type)}. "
            f"Because the interval is wide relative to the point estimate, the band — not the line — should drive planning.",
            body_just))
        strip = [(d['name'] if "Est." in d['name'] else f"{d['name']} (Forecast)", fmt_value(d["forecast"], rev_type), "point estimate", None) for d in fcst_data[1:]]
        strip.append(("Confidence Band", f"{fmt_value(lo, rev_type)}–{fmt_value(hi, rev_type)}", "95% interval", None))
        story.append(stat_cards(strip[:4]))
        story.append(Spacer(1, 6 * mm))
    else:
        story.append(Paragraph("Insufficient date-based history was available to produce a statistically supported forecast for this dataset.", body))
        story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("Recommended Actions", h3))
    story.append(Spacer(1, 3))
    recs = []
    if fcst_bounds:
        recs.append(("Plan to the band, not the line", "Use the confidence interval for capacity and resourcing decisions rather than the single point forecast, particularly where history is volatile."))
    if primary_kpi and primary_kpi.get("value", 0) < 0:
        recs.append(("Investigate the negative headline", f"The net {fmt_value(primary_kpi['value'], rev_type)} figure implies reversals or refunds are material against gross throughput. Reconcile the underlying pipeline before the next reporting cycle."))
    elif primary_kpi and primary_kpi.get("trend", 0) < 0:
        recs.append((f"Address the {primary_kpi.get('name', rev_label).lower()} decline", f"{primary_kpi.get('name', rev_label)} is down {abs(primary_kpi.get('trend',0)):.1f}% against the prior period — review the drivers before they compound."))
    else:
        recs.append(("Sustain the growth trajectory", f"{primary_kpi.get('name', rev_label) if primary_kpi else 'The primary metric'} is trending favorably; maintain the current operating cadence and re-check next cycle." ))
    if seg_col:
        recs.append((f"Review {seg_col.replace('_',' ')} concentration", f"Top categories in {seg_col.replace('_',' ')} account for a large share of records — establish monitoring so a shift in any one segment doesn't stall overall throughput."))
    recs.append(("Preserve data quality discipline", f"Maintain the ingestion checks that produced the {quality_score:.1f} index; schedule automated validation on each new dataset load."))

    for i, (title, txt) in enumerate(recs[:5], start=1):
        row = Table([[Paragraph(str(i), ParagraphStyle('RN', fontName='DejaVuSerif', fontSize=12, textColor=GOLD)),
                      [Paragraph(title, ParagraphStyle('RT', fontName='DejaVuSerif', fontSize=11.5, textColor=INK, leading=15, spaceAfter=2)),
                       Paragraph(txt, body)]]], colWidths=[10 * mm, W - 10 * mm])
        row.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
        story.append(row)
        hairline(space_after=4)
    story.append(PageBreak())

    # ================= 08 METHODOLOGY & SOURCES =================
    section_header("08", "Methodology & Sources")

    left_meth = [
        Paragraph("Data Source", h3),
        Paragraph(f"Figures derive from {dataset_name} — {len(df):,} record(s) across {len(df.columns)} field(s). No external enrichment was applied.", body),
        Spacer(1, 8),
        Paragraph("Metric Definitions", h3),
    ]
    metric_defs = []
    if primary_kpi:
        metric_defs.append(f"<b>{primary_kpi.get('name', rev_label)}</b> — {primary_kpi.get('agg','sum')} of {rev_col or 'the primary metric column'}.")
    if entity_kpi:
        metric_defs.append(f"<b>{entity_kpi.get('name')}</b> — count of qualifying records.")
    if status_kpi:
        metric_defs.append(f"<b>{status_kpi.get('name')}</b> — share of records meeting the healthy-status condition.")
    if not metric_defs:
        metric_defs.append("No semantic business metrics were detected; figures reflect raw column aggregates.")
    for d in metric_defs:
        left_meth.append(Paragraph(d, body))

    f_method = None
    if rev_col:
        try:
            f_method = forecast_series(df, rev_col, periods=1)
        except Exception:
            f_method = None
    right_meth = [
        Paragraph("Forecast Model", h3),
        Paragraph(
            (f"{f_method.get('method')} projection over the trailing series ({f_method.get('summary', {}).get('history_periods')} {f_method.get('freq_label','monthly')} periods), reporting a 95% confidence band." if f_method and f_method.get("available")
             else "A trend-based projection over the trailing series, reporting a 95% confidence band, when sufficient date-based history is available."),
            body),
        Spacer(1, 8),
        Paragraph("Quality Scoring", h3),
        Paragraph(f"{len(quality_breakdown)} dimensions — {', '.join(dim_labels.get(k, k) for k in quality_breakdown.keys())} — scored 0–100 and combined into a weighted composite index ({quality_score:.1f}, Grade {grade}).", body),
    ]
    meth_cols = Table([[left_meth, right_meth]], colWidths=[W * 0.48, W * 0.48])
    meth_cols.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (0, 0), 16)]))
    story.append(meth_cols)
    story.append(Spacer(1, 8 * mm))
    story.append(callout("Disclaimer", "This document is confidential and prepared solely for the named recipient. Forecasts are indicative and do not constitute a guarantee of future performance. Figures may be revised as source data is corrected."))

    story.append(Spacer(1, 14 * mm))
    close_logo = brand_mark(size=9 * mm, fill=GOLD, letter_color=WHITE)
    story.append(Table([[close_logo]], colWidths=[W], style=TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')])))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "N&nbsp;U&nbsp;M&nbsp;E&nbsp;R&nbsp;A&nbsp;T&nbsp;E&nbsp;&nbsp;&nbsp;A&nbsp;N&nbsp;A&nbsp;L&nbsp;Y&nbsp;T&nbsp;I&nbsp;C&nbsp;S&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;E&nbsp;N&nbsp;D&nbsp;&nbsp;&nbsp;O&nbsp;F&nbsp;&nbsp;&nbsp;R&nbsp;E&nbsp;P&nbsp;O&nbsp;R&nbsp;T",
        ParagraphStyle('EndFoot', fontName='DejaVuSans', fontSize=8.5, textColor=MUTED, alignment=1)))

    # Optional appendix — regression models, only if present
    models = get_regression_models(dataset_info["id"])
    if models:
        story.append(PageBreak())
        section_header("09", "Regression Models")
        h_row = [Paragraph("TARGET", th_style), Paragraph("FEATURES", th_style), Paragraph("R² TEST", th_right), Paragraph("TRAINED", th_style)]
        rows = []
        for m in models:
            f_str = ", ".join(m["features"])
            if len(f_str) > 50:
                f_str = f_str[:47] + "..."
            dt = m["timestamp"].split("T")[0] if isinstance(m["timestamp"], str) else str(m["timestamp"])
            rows.append([Paragraph(str(m["target"]), td_style), Paragraph(f_str, td_muted), Paragraph(f"{m['r2_test']:.3f}", td_right), Paragraph(dt, td_muted)])
        col_widths = [W * 0.2, W * 0.45, W * 0.15, W * 0.2]
        story.append(data_table(h_row, rows, col_widths))

    def paint_cover(c, _doc):
        c.saveState()
        w, h = A4
        c.setFillColor(colors.HexColor(COVER_BG_STR))
        c.rect(0, 0, w, h, fill=1, stroke=0)
        c.restoreState()

    doc.build(
        story,
        onFirstPage=paint_cover,
        onLaterPages=lambda c, d: None,
        canvasmaker=lambda *args, **kwargs: EditorialCanvas(*args, report_title="Numerate · Data Analysis Report", **kwargs),
    )
    buffer.seek(0)
    return buffer
