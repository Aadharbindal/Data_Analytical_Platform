import io
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import os
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether, PageBreak, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.services.stats_service import compute_kpis, find_column, forecast_series
from app.core.config import DB_PATH

# =====================================================================
# DESIGN TOKENS
# =====================================================================
BG_PAGE = colors.HexColor('#0B1020')
BG_CARD = colors.HexColor('#141A28')
BORDER = colors.Color(1, 1, 1, alpha=0.08)
ACCENT = colors.HexColor('#3B82F6')
SUCCESS = colors.HexColor('#22C55E')
DANGER = colors.HexColor('#EF4444')
PURPLE = colors.HexColor('#7C3AED')
TEXT_PRIMARY = colors.HexColor('#FFFFFF')
TEXT_MUTED = colors.HexColor('#9CA3AF') # gray-400
TEXT_DARK = colors.HexColor('#6B7280') # gray-500

# Try to use Helvetica if no custom fonts are available
FONT_REGULAR = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

styles = getSampleStyleSheet()
style_h1 = ParagraphStyle('H1', fontName=FONT_BOLD, fontSize=28, textColor=TEXT_PRIMARY, leading=34)
style_h2 = ParagraphStyle('H2', fontName=FONT_BOLD, fontSize=16, textColor=TEXT_PRIMARY, leading=22)
style_body = ParagraphStyle('Body', fontName=FONT_REGULAR, fontSize=10, textColor=TEXT_MUTED, leading=16)
style_body_white = ParagraphStyle('BodyW', fontName=FONT_REGULAR, fontSize=10, textColor=TEXT_PRIMARY, leading=16)
style_muted_sm = ParagraphStyle('MutedSm', fontName=FONT_REGULAR, fontSize=9, textColor=TEXT_MUTED, leading=12)
style_val_lg = ParagraphStyle('ValLg', fontName=FONT_BOLD, fontSize=24, textColor=TEXT_PRIMARY, leading=28)
style_trend = ParagraphStyle('Trend', fontName=FONT_REGULAR, fontSize=10, leading=14)
style_source = ParagraphStyle('Source', fontName='Courier', fontSize=8, textColor=TEXT_DARK, leading=10)

def format_number(value):
    if value is None or pd.isna(value):
        return "0"
    try:
        val = float(value)
        abs_val = abs(val)
        if abs_val >= 1000000:
            return f"{val / 1000000:.2f}M"
        if abs_val >= 1000:
            return f"{val / 1000:.2f}K"
        if val.is_integer():
            return str(int(val))
        return f"{val:.2f}"
    except:
        return str(value)

def matplotlib_formatter(x, pos):
    return format_number(x)

# =====================================================================
# FLOWABLES & COMPONENTS
# =====================================================================
class Card(Flowable):
    def __init__(self, width, flowables, padding=16):
        Flowable.__init__(self)
        self.width = width
        self.padding = padding
        self.table = Table([[f] for f in flowables], colWidths=[width - 2*padding])
        self.table.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        
    def wrap(self, availWidth, availHeight):
        self.w, self.h = self.table.wrap(self.width - 2*self.padding, availHeight - 2*self.padding)
        self.w = self.width
        self.h += 2*self.padding
        return self.w, self.h
        
    def draw(self):
        self.canv.saveState()
        self.canv.setFillColor(BG_CARD)
        self.canv.setStrokeColor(BORDER)
        self.canv.setLineWidth(1)
        self.canv.roundRect(0, 0, self.w, self.h, 14, fill=1, stroke=1)
        self.canv.restoreState()
        self.table.drawOn(self.canv, self.padding, self.padding)

class SectionHeader(Flowable):
    def __init__(self, text, width):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        self.h = 40
        
    def wrap(self, availWidth, availHeight):
        return self.width, self.h
        
    def draw(self):
        self.canv.saveState()
        self.canv.setFont(FONT_BOLD, 16)
        self.canv.setFillColor(TEXT_PRIMARY)
        self.canv.drawString(0, 15, self.text)
        self.canv.setFillColor(ACCENT)
        self.canv.rect(0, 0, 40, 3, fill=1, stroke=0)
        self.canv.restoreState()

def make_stat_card(label, value_str, trend_val, source_str, width, sparkline_data=None):
    flowables = []
    flowables.append(Paragraph(label, style_muted_sm))
    flowables.append(Spacer(1, 6))
    flowables.append(Paragraph(value_str, style_val_lg))
    flowables.append(Spacer(1, 6))
    
    delta = float(trend_val) if trend_val else 0.0
    t_color = SUCCESS if delta > 0 else DANGER if delta < 0 else TEXT_MUTED
    t_char = u"▲" if delta > 0 else u"▼" if delta < 0 else u"●"
    trend_str = f"<font color='{t_color.hexval().replace('0x', '#')}'>{t_char} {abs(delta):.1f}%</font>"
    flowables.append(Paragraph(trend_str, style_trend))
    
    if sparkline_data and len(sparkline_data) > 1:
        flowables.append(Spacer(1, 10))
        fig_w = max(1, (width - 32) / 72.0)
        plt.figure(figsize=(fig_w, 0.4), dpi=150)
        ax = plt.gca()
        ax.set_facecolor(BG_CARD.hexval().replace('0x', '#'))
        plt.gcf().patch.set_facecolor(BG_CARD.hexval().replace('0x', '#'))
        x = np.arange(len(sparkline_data))
        y = np.array(sparkline_data)
        try:
            from scipy.interpolate import pchip_interpolate
            x_new = np.linspace(x.min(), x.max(), 50)
            y_new = pchip_interpolate(x, y, x_new)
            ax.plot(x_new, y_new, color=t_color.hexval().replace('0x', '#'), linewidth=1.5)
        except:
            ax.plot(x, y, color=t_color.hexval().replace('0x', '#'), linewidth=1.5)
        ax.axis('off')
        plt.tight_layout(pad=0)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
        plt.close()
        buf.seek(0)
        flowables.append(Image(buf, width=width-32, height=0.4*inch))
    
    flowables.append(Spacer(1, 10))
    flowables.append(Paragraph(f"Source: {source_str}", style_source))
    
    return Card(width, flowables, padding=16)

def generate_ring_gauge(pct, label, color_hex, size_inch=1.5):
    plt.figure(figsize=(size_inch, size_inch), dpi=200)
    ax = plt.gca()
    ax.set_facecolor(BG_CARD.hexval().replace('0x', '#'))
    plt.gcf().patch.set_facecolor(BG_CARD.hexval().replace('0x', '#'))
    
    wedges, _ = ax.pie([pct, max(0, 100-pct)], colors=[color_hex, '#20293A'], startangle=90, counterclock=False, wedgeprops=dict(width=0.2, edgecolor='none'))
    
    ax.text(0, 0, f"{int(pct)}%", ha='center', va='center', fontsize=16, fontweight='bold', color='#FFFFFF')
    ax.axis('equal')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    plt.close()
    buf.seek(0)
    return Image(buf, width=size_inch*inch, height=size_inch*inch)

def generate_donut_chart(labels, values, size_inch=3.0):
    plt.figure(figsize=(size_inch, size_inch), dpi=200)
    ax = plt.gca()
    plt.gcf().patch.set_facecolor(BG_CARD.hexval().replace('0x', '#'))
    
    colors_list = [ACCENT.hexval().replace('0x', '#'), PURPLE.hexval().replace('0x', '#'), SUCCESS.hexval().replace('0x', '#'), '#F59E0B', '#10B981', '#6366F1']
    wedges, _ = ax.pie(values, startangle=90, colors=colors_list, wedgeprops=dict(width=0.3, edgecolor=BG_CARD.hexval().replace('0x', '#'), linewidth=2))
    
    total = sum(values)
    ax.text(0, 0.1, "Total", ha='center', va='center', fontsize=10, color=TEXT_MUTED.hexval().replace('0x', '#'))
    ax.text(0, -0.1, format_number(total), ha='center', va='center', fontsize=14, fontweight='bold', color='#FFFFFF')
    
    ax.axis('equal')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    plt.close()
    buf.seek(0)
    return Image(buf, width=size_inch*inch, height=size_inch*inch), colors_list

def make_cover_bg(width_inch, height_inch):
    plt.figure(figsize=(width_inch, height_inch), dpi=150)
    ax = plt.gca()
    plt.gcf().patch.set_facecolor(BG_PAGE.hexval().replace('0x', '#'))
    ax.set_facecolor(BG_PAGE.hexval().replace('0x', '#'))
    x = np.linspace(0, 10, 500)
    for i in range(5):
        y = np.sin(x + i) * np.exp(-x/5) + (i * 0.2)
        ax.fill_between(x, -2, y, color=PURPLE.hexval().replace('0x', '#') if i%2==0 else ACCENT.hexval().replace('0x', '#'), alpha=0.03 + i*0.01)
    ax.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    plt.close()
    buf.seek(0)
    return Image(buf, width=width_inch*inch, height=height_inch*inch)

def get_ai_summary(facts):
    try:
        from litellm import completion
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise Exception("No API Key")
        prompt = f"Write a 2-3 sentence executive summary based on the following facts. DO NOT invent any numbers. Facts: {facts}"
        response = completion(
            model="groq/llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key
        )
        llm_summary = response.choices[0].message.content.strip()
        
        def extract_nums(text): return re.findall(r'-?\d+\.?\d*', text.replace(',', ''))
        llm_nums = extract_nums(llm_summary)
        fact_nums = extract_nums(str(facts))
        
        verified = True
        for num in llm_nums:
            found = False
            try:
                num_float = float(num)
                for f_num in fact_nums:
                    if abs(float(f_num) - num_float) < 1.0:
                        found = True
                        break
            except: pass
            if not found:
                verified = False
                break
        if verified:
            return llm_summary, "groq/llama-3.3-70b-versatile"
    except Exception:
        pass
    
    summary = f"Based on the recently uploaded dataset '{facts.get('dataset_name', 'Unknown')}' which contains {facts.get('row_count', 0)} records."
    if "total_value" in facts:
         summary += f" The total {facts.get('metric_name', 'metric')} is {format_number(facts['total_value'])}."
    if "percent_change" in facts:
         change_dir = "increase" if facts["percent_change"] > 0 else "decrease"
         summary += f" There is a {abs(facts['percent_change'])}% {change_dir} in the recent period."
    return summary, "Deterministic Template"

# =====================================================================
# PDF GENERATION
# =====================================================================
def on_page_cb(canvas, doc, dataset_name):
    canvas.saveState()
    canvas.setFillColor(BG_PAGE)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    if doc.page > 1:
        canvas.setStrokeColor(BORDER)
        canvas.line(18*mm, 15*mm, A4[0]-18*mm, 15*mm)
        canvas.setFont(FONT_REGULAR, 8)
        canvas.setFillColor(TEXT_DARK)
        canvas.drawString(18*mm, 10*mm, "DataMind OS")
        canvas.drawRightString(A4[0]-18*mm, 10*mm, f"Page {doc.page}")
    canvas.restoreState()

def generate_pdf_report(dataset_info, df):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )
    story = []
    content_width = A4[0] - 36*mm
    
    # Pre-computation
    kpi_data = compute_kpis(df)
    kpis = kpi_data.get("kpis", [])
    date_col = find_column(df, r'date|month|year|time')
    rev_col = find_column(df, r'revenue|sales|amount')
    cat_cols = df.select_dtypes(exclude=[np.number, 'datetime64']).columns
    num_cols = df.select_dtypes(include=[np.number]).columns
    
    # ---------------- PAGE 1: COVER ----------------
    story.append(make_cover_bg(A4[0]/inch, 6))
    story.append(Spacer(1, -1.5*inch))
    
    cover_flowables = [
        Paragraph("AI Executive Report", style_h1), Spacer(1, 10),
        Paragraph(dataset_info["name"], style_h2), Spacer(1, 20),
        Paragraph(f"Rows: {len(df)} | Columns: {len(df.columns)}", style_body),
        Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}", style_body), Spacer(1, 30),
        Paragraph("DATAMIND OS", style_muted_sm)
    ]
    story.append(Card(content_width, cover_flowables))
    story.append(PageBreak())
    
    # ---------------- PAGE 2: EXECUTIVE SUMMARY ----------------
    story.append(SectionHeader("Executive Summary", content_width))
    exec_flowables = []
    for k in kpis:
        val = format_number(k["value"])
        delta = k.get("trend", 0)
        t_char = u"▲" if delta > 0 else u"▼" if delta < 0 else u"●"
        t_color = SUCCESS.hexval().replace('0x', '#') if delta > 0 else DANGER.hexval().replace('0x', '#') if delta < 0 else TEXT_MUTED.hexval().replace('0x', '#')
        line = f"<b>{k['name']}</b> ....... <font color='{t_color}'>{t_char} {val} ({abs(delta):.1f}%)</font>"
        exec_flowables.append(Paragraph(line, style_body_white))
        exec_flowables.append(Spacer(1, 6))
        
    exec_flowables.append(Spacer(1, 10))
    exec_flowables.append(Paragraph("<b>AI Summary</b>", style_h2))
    exec_flowables.append(Spacer(1, 6))
    
    facts = {"dataset_name": dataset_info["name"], "row_count": len(df)}
    recent, prior = None, None
    if rev_col and pd.api.types.is_numeric_dtype(df[rev_col]):
        facts["total_value"] = float(df[rev_col].sum())
        facts["metric_name"] = rev_col
        if date_col:
            try:
                df_temp = df.copy()
                df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
                df_temp = df_temp.dropna(subset=[date_col])
                if not df_temp.empty:
                    periods = df_temp.groupby(df_temp[date_col].dt.to_period('M'))
                    if len(periods) >= 2:
                        sorted_periods = sorted(periods.groups.keys())
                        recent = float(periods.get_group(sorted_periods[-1])[rev_col].sum())
                        prior = float(periods.get_group(sorted_periods[-2])[rev_col].sum())
                        if prior > 0: facts["percent_change"] = round(((recent - prior) / prior) * 100, 1)
            except: pass
            
    ai_summary_text, ai_model_used = get_ai_summary(facts)
    exec_flowables.append(Paragraph(ai_summary_text, style_body))
    
    exec_flowables.append(Spacer(1, 10))
    exec_flowables.append(Paragraph("<b>Recommendations</b>", style_h2))
    exec_flowables.append(Spacer(1, 6))
    
    recs = []
    rev_kpi = next((k for k in kpis if "Revenue" in k["name"] or "Sales" in k["name"]), None)
    if rev_kpi:
        if rev_kpi["trend"] < 0:
            recs.append(f"u\"●\" {rev_kpi['name']} declined by {abs(rev_kpi['trend']):.1f}%. Immediate review of recent period drivers required.")
        else:
            recs.append(f"u\"●\" {rev_kpi['name']} grew by {rev_kpi['trend']:.1f}%. Capitalize on the current momentum.")
            
    if len(cat_cols) > 0 and rev_col:
        for c in cat_cols:
            if 'id' not in c.lower() and 2 <= df[c].nunique() <= 50 and c != date_col:
                grp = df.groupby(c)[rev_col].sum()
                if len(grp) > 0:
                    best = grp.idxmax()
                    share = (grp[best] / grp.sum()) * 100
                    recs.append(f"u\"●\" {c} '{best}' drives {share:.1f}% of {rev_col}. Protect inventory and maintain focus here.")
                    break
                    
    if len(recs) < 3 and rev_kpi and len(cat_cols) > 0:
        for c in cat_cols:
            if 'id' not in c.lower() and 2 <= df[c].nunique() <= 50 and c != date_col:
                grp = df.groupby(c)[rev_kpi["column"]].sum()
                if len(grp) > 1:
                    worst = grp.idxmin()
                    recs.append(f"u\"●\" {c} '{worst}' is underperforming. Investigate root causes to mitigate losses.")
                    break
                    
    while len(recs) < 3: recs.append(u"● Maintain current data collection cadence to improve future analytics accuracy.")
        
    for r in recs[:3]:
        exec_flowables.append(Paragraph(r.replace('u"●"', u"●"), style_body))
        exec_flowables.append(Spacer(1, 4))
        
    story.append(Card(content_width, exec_flowables))
    story.append(PageBreak())
    
    # ---------------- PAGE 3: KPI DASHBOARD ----------------
    story.append(SectionHeader("KPI Dashboard", content_width))
    if not kpis:
        story.append(Paragraph("No KPIs available for this dataset.", style_body))
    else:
        stat_cards = []
        for k in kpis:
            spark_data = None
            if date_col:
                try:
                    df_t = df.copy()
                    df_t[date_col] = pd.to_datetime(df_t[date_col], errors='coerce')
                    df_t = df_t.dropna(subset=[date_col])
                    if not df_t.empty:
                        m_data = df_t.groupby(df_t[date_col].dt.to_period('M'))[k['column']].sum()
                        spark_data = m_data.values.tolist()
                except: pass
            sc = make_stat_card(k['name'], format_number(k['value']), k['trend'], k['column'], content_width/2 - 10, sparkline_data=spark_data)
            stat_cards.append(sc)
            
        grid_data = []
        for i in range(0, len(stat_cards), 2):
            row = [stat_cards[i]]
            if i+1 < len(stat_cards): row.append(stat_cards[i+1])
            else: row.append(Spacer(1,1))
            grid_data.append(row)
            
        if grid_data:
            t_grid = Table(grid_data, colWidths=[content_width/2]*2)
            t_grid.setStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 10)])
            story.append(t_grid)
    story.append(PageBreak())
    
    # ---------------- PAGE 4: REVENUE ANALYTICS ----------------
    story.append(SectionHeader("Revenue Analytics", content_width))
    if date_col and rev_col:
        chart_data = kpi_data.get("chart_data", [])
        if chart_data:
            plt.figure(figsize=(content_width/inch, 4), dpi=200)
            ax = plt.gca()
            ax.set_facecolor(BG_PAGE.hexval().replace('0x', '#'))
            plt.gcf().patch.set_facecolor(BG_PAGE.hexval().replace('0x', '#'))
            
            x_hist = [d["name"] for d in chart_data if d.get("value") is not None]
            y_hist = [d["value"] for d in chart_data if d.get("value") is not None]
            
            if len(y_hist) > 0:
                try:
                    from scipy.interpolate import pchip_interpolate
                    x_idx = np.arange(len(x_hist))
                    x_new = np.linspace(0, len(x_hist)-1, 100)
                    y_new = pchip_interpolate(x_idx, y_hist, x_new)
                    ax.plot(x_new, y_new, color=ACCENT.hexval().replace('0x', '#'), linewidth=2, label="Actual")
                except:
                    ax.plot(range(len(x_hist)), y_hist, color=ACCENT.hexval().replace('0x', '#'), linewidth=2, label="Actual")
                ax.fill_between(range(len(x_hist)), y_hist, min(y_hist), color=ACCENT.hexval().replace('0x', '#'), alpha=0.1)
                ax.annotate(format_number(y_hist[-1]), (len(x_hist)-1, y_hist[-1]), textcoords="offset points", xytext=(0,10), ha='center', color=TEXT_PRIMARY.hexval().replace('0x', '#'), fontsize=9, fontweight='bold')
            
            x_fcst = [d["name"] for d in chart_data if d.get("forecast") is not None]
            y_fcst = [d["forecast"] for d in chart_data if d.get("forecast") is not None]
            
            if len(y_fcst) > 0:
                start_x = len(x_hist) - 1
                fcst_x_range = range(start_x, start_x + len(x_fcst))
                try:
                    x_idx = np.arange(start_x, start_x + len(x_fcst))
                    x_new = np.linspace(start_x, start_x + len(x_fcst) - 1, 100)
                    y_new = pchip_interpolate(x_idx, y_fcst, x_new)
                    ax.plot(x_new, y_new, color=PURPLE.hexval().replace('0x', '#'), linestyle='--', linewidth=2, label="Forecast")
                except:
                    ax.plot(fcst_x_range, y_fcst, color=PURPLE.hexval().replace('0x', '#'), linestyle='--', linewidth=2, label="Forecast")
                ax.annotate(format_number(y_fcst[-1]), (fcst_x_range[-1], y_fcst[-1]), textcoords="offset points", xytext=(0,10), ha='center', color=TEXT_PRIMARY.hexval().replace('0x', '#'), fontsize=9, fontweight='bold')
                
                f_res = forecast_series(df, rev_col, periods=len(x_fcst)-1)
                if f_res.get("available") and f_res.get("forecast"):
                    bounds = f_res.get("forecast", [])
                    if bounds:
                        y_lower = [y_fcst[0]] + [b["lower"] for b in bounds]
                        y_upper = [y_fcst[0]] + [b["upper"] for b in bounds]
                        ax.fill_between(fcst_x_range, y_lower, y_upper, color=PURPLE.hexval().replace('0x', '#'), alpha=0.15)
                        
            ax.yaxis.set_major_formatter(FuncFormatter(matplotlib_formatter))
            ax.grid(axis='y', linestyle='-', alpha=0.06, color='#FFFFFF')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color(BORDER.hexval().replace('0x', '#'))
            ax.spines['bottom'].set_color(BORDER.hexval().replace('0x', '#'))
            ax.tick_params(colors=TEXT_MUTED.hexval().replace('0x', '#'))
            if len(x_hist) > 0:
                plt.xticks(range(len(x_hist)), x_hist, rotation=45, ha='right', fontsize=8)
            ax.legend(loc='upper left', frameon=False, labelcolor=TEXT_PRIMARY.hexval().replace('0x', '#'))
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
            plt.close()
            buf.seek(0)
            story.append(Image(buf, width=content_width, height=4*inch))
            story.append(Spacer(1, 15))
            
            top_driver_text = "Not enough categorical data."
            key_mov_text = "No prior period to compare."
            if prior and recent:
                km = ((recent - prior) / prior) * 100
                key_mov_text = f"{abs(km):.1f}% {'increase' if km>0 else 'decrease'} vs last month."
            top_cat_name = "Derived from data"
            if len(cat_cols) > 0:
                for c in cat_cols:
                    if 'id' not in c.lower() and 2 <= df[c].nunique() <= 50 and c != date_col:
                        grp = df.groupby(c)[rev_col].sum()
                        if len(grp) > 0:
                            top_driver_text = str(grp.idxmax())
                            top_cat_name = c
                            break
            
            c1 = Card(content_width/2 - 10, [Paragraph("Key Movement", style_muted_sm), Spacer(1, 4), Paragraph(key_mov_text, style_body_white)])
            c2 = Card(content_width/2 - 10, [Paragraph(f"Top Driver ({top_cat_name})", style_muted_sm), Spacer(1, 4), Paragraph(top_driver_text, style_body_white)])
            story.append(Table([[c1, c2]], colWidths=[content_width/2]*2, style=[('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5)]))
    else:
        story.append(Paragraph("Time series data not available for Revenue Analytics.", style_body))
    story.append(PageBreak())
    
    # ---------------- PAGE 5: FORECAST & TREND ----------------
    story.append(SectionHeader("Forecast & Trend", content_width))
    if date_col and rev_col:
        f_res = forecast_series(df, rev_col, periods=3)
        if f_res.get("available") and f_res.get("forecast"):
            last_fcst = f_res["forecast"][-1]
            c1 = Card(content_width/3 - 10, [Paragraph("Worst Case", style_muted_sm), Spacer(1,6), Paragraph(format_number(last_fcst["lower"]), style_val_lg)])
            c2 = Card(content_width/3 - 10, [Paragraph("Projection", style_muted_sm), Spacer(1,6), Paragraph(format_number(last_fcst["forecast"]), style_val_lg)])
            c3 = Card(content_width/3 - 10, [Paragraph("Best Case", style_muted_sm), Spacer(1,6), Paragraph(format_number(last_fcst["upper"]), style_val_lg)])
            story.append(Table([[c1, c2, c3]], colWidths=[content_width/3]*3, style=[('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5)]))
            story.append(Spacer(1, 15))
            story.append(Paragraph(f"Method: Linear trend projection bounds for {last_fcst['date']}", style_body))
            story.append(Spacer(1, 15))
            
            story.append(Paragraph("<b>Metric Trends</b>", style_h2))
            story.append(Spacer(1, 10))
            df_temp = df.copy()
            df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
            df_temp = df_temp.dropna(subset=[date_col])
            
            for num_col in df_temp.select_dtypes(include=[np.number]).columns[:8]:
                monthly = df_temp.groupby(df_temp[date_col].dt.to_period('M'))[num_col].sum().reset_index()
                if len(monthly) < 2: continue
                y = monthly[num_col].values
                x = np.arange(len(y))
                p = np.polyfit(x, y, 1)
                slope = p[0]
                direction = u"▲ UP" if slope > 0 else u"▼ DOWN"
                color = SUCCESS.hexval().replace('0x', '#') if slope > 0 else DANGER.hexval().replace('0x', '#')
                r2 = np.corrcoef(x, y)[0,1]**2 if len(x) > 1 else 0
                row_str = f"<b>{num_col}</b> ..... <font color='{color}'>{direction}</font> ..... R² = {r2:.2f}"
                story.append(Paragraph(row_str, style_body_white))
                story.append(Spacer(1, 6))
    else:
         story.append(Paragraph("Not enough chronological data for forecasting.", style_body))
    story.append(PageBreak())
    
    # ---------------- PAGE 6: SEGMENT ANALYSIS ----------------
    story.append(SectionHeader("Segment Analysis", content_width))
    if len(cat_cols) > 0 and rev_col:
        drawn = 0
        for c in cat_cols:
            if drawn >= 3: break
            if 'id' in c.lower() or not (2 <= df[c].nunique() <= 20): continue
            grp = df.groupby(c)[rev_col].sum().sort_values(ascending=False)
            if len(grp) == 0: continue
            top5 = grp.head(5)
            other = grp.iloc[5:].sum() if len(grp) > 5 else 0
            labels = [str(x) for x in top5.index]
            values = top5.values.tolist()
            if other > 0:
                labels.append("Other")
                values.append(other)
            img, colors_list = generate_donut_chart(labels, values, 2.5)
            list_flowables = [Paragraph(f"<b>{c} Share</b>", style_h2), Spacer(1, 10)]
            for i, (l, v) in enumerate(zip(labels, values)):
                pct = (v / sum(values)) * 100
                col_hex = colors_list[i % len(colors_list)]
                list_flowables.append(Paragraph(f"<font color='{col_hex}'>u\"●\"</font> {l}: {format_number(v)} ({pct:.1f}%)", style_body_white))
                list_flowables.append(Spacer(1, 4))
            row_table = Table([[img, list_flowables]], colWidths=[3*inch, content_width - 3*inch])
            row_table.setStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')])
            story.append(Card(content_width, [row_table]))
            story.append(Spacer(1, 15))
            drawn += 1
        if drawn == 0: story.append(Paragraph("No suitable categorical segments found.", style_body))
    else:
        story.append(Paragraph("No segmentation data available.", style_body))
    story.append(PageBreak())
    
    # ---------------- PAGE 7: EXECUTIVE INSIGHTS ----------------
    story.append(SectionHeader("Executive Insights", content_width))
    pos_flowables = [Paragraph("<b>Positive Findings</b>", style_h2), Spacer(1, 10)]
    neg_flowables = [Paragraph("<b>Attention Needed</b>", style_h2), Spacer(1, 10)]
    pos_count = 0
    neg_count = 0
    for k in kpis:
        if k["trend"] > 0:
            pos_flowables.append(Paragraph(f"<font color='{SUCCESS.hexval().replace('0x', '#')}'>u\"✓\"</font> {k['name']} grew by {k['trend']:.1f}%", style_body_white))
            pos_flowables.append(Spacer(1, 6))
            pos_count += 1
        elif k["trend"] < 0:
            neg_flowables.append(Paragraph(f"<font color='{DANGER.hexval().replace('0x', '#')}'>u\"⚠\"</font> {k['name']} dropped by {abs(k['trend']):.1f}%", style_body_white))
            neg_flowables.append(Spacer(1, 6))
            neg_count += 1
            
    if pos_count == 0: pos_flowables.append(Paragraph("No positive metric trends detected.", style_body))
    if neg_count == 0: neg_flowables.append(Paragraph("No negative metric trends detected.", style_body))
    story.append(Table([[pos_flowables, neg_flowables]], colWidths=[content_width/2]*2, style=[('VALIGN',(0,0),(-1,-1),'TOP')]))
    story.append(Spacer(1, 20))
    clean_recs = [r.replace('u"●"', u"●") for r in recs]
    story.append(Card(content_width, [Paragraph("<b>Recommendations</b>", style_h2), Spacer(1, 10)] + [Paragraph(r, style_body_white) for r in clean_recs]))
    story.append(PageBreak())
    
    # ---------------- PAGE 8: DATA QUALITY ----------------
    story.append(SectionHeader("Data Quality", content_width))
    q_score = dataset_info.get('quality_score', 0)
    q_color = SUCCESS if q_score >= 85 else colors.HexColor('#F59E0B') if q_score >= 60 else DANGER
    story.append(Paragraph(f"<font color='{q_color.hexval().replace('0x', '#')}'>{q_score:.1f}</font> / 100 Overall Score", style_h1))
    story.append(Spacer(1, 20))
    breakdown = dataset_info.get('quality_breakdown', {})
    if isinstance(breakdown, str):
        try: breakdown = json.loads(breakdown)
        except: breakdown = {}
    gauge_imgs = []
    gauge_labels = []
    for k in ["completeness", "uniqueness", "type_consistency", "validity"]:
        val = breakdown.get(k, 0)
        c = SUCCESS.hexval().replace('0x', '#') if val >= 85 else '#F59E0B' if val >= 60 else DANGER.hexval().replace('0x', '#')
        gauge_imgs.append(generate_ring_gauge(val, k, c, size_inch=1.5))
        gauge_labels.append(Paragraph(k.replace('type_', '').capitalize(), ParagraphStyle('c', alignment=1, fontName=FONT_BOLD, textColor=TEXT_PRIMARY)))
    g_table = Table([gauge_imgs, gauge_labels], colWidths=[content_width/4]*4)
    g_table.setStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')])
    story.append(Card(content_width, [g_table]))
    story.append(PageBreak())
    
    # ---------------- PAGE 9: STATISTICAL SUMMARY ----------------
    story.append(SectionHeader("Statistical Summary", content_width))
    if len(num_cols) > 0:
        stat_cards = []
        for col in num_cols[:8]:
            c_flowables = [
                Paragraph(f"<b>{col}</b>", style_h2), Spacer(1, 10),
                Paragraph(f"Sum: {format_number(df[col].sum())}", style_body_white),
                Paragraph(f"Mean: {format_number(df[col].mean())}", style_body_white),
                Paragraph(f"Min: {format_number(df[col].min())}", style_body_white),
                Paragraph(f"Max: {format_number(df[col].max())}", style_body_white),
            ]
            stat_cards.append(Card(content_width/2 - 10, c_flowables))
        grid_data = []
        for i in range(0, len(stat_cards), 2):
            row = [stat_cards[i]]
            if i+1 < len(stat_cards): row.append(stat_cards[i+1])
            else: row.append(Spacer(1,1))
            grid_data.append(row)
        t_grid = Table(grid_data, colWidths=[content_width/2]*2)
        t_grid.setStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 10)])
        story.append(t_grid)
    else:
        story.append(Paragraph("No numeric columns.", style_body))
    story.append(PageBreak())
    
    # ---------------- PAGE 10: APPENDIX ----------------
    story.append(SectionHeader("Appendix & Metadata", content_width))
    meta_flowables = [
        Paragraph(f"<b>Dataset:</b> {dataset_info['name']}", style_body_white), Spacer(1, 6),
        Paragraph(f"<b>Rows:</b> {len(df)}", style_body_white), Spacer(1, 6),
        Paragraph(f"<b>Columns:</b> {len(df.columns)}", style_body_white), Spacer(1, 6),
        Paragraph(f"<b>Generated At:</b> {datetime.now().isoformat()}", style_body_white), Spacer(1, 6),
        Paragraph("<b>Engine:</b> DataMind OS Computation Engine", style_body_white), Spacer(1, 6),
        Paragraph(f"<b>AI Model:</b> {ai_model_used}", style_body_white), Spacer(1, 6),
        Paragraph("<b>Export Theme:</b> Premium Enterprise Dark", style_body_white), Spacer(1, 6),
    ]
    story.append(Card(content_width, meta_flowables))
    
    cb = lambda canv, d: on_page_cb(canv, d, dataset_info["name"])
    doc.build(story, onFirstPage=cb, onLaterPages=cb)
    buffer.seek(0)
    return buffer
