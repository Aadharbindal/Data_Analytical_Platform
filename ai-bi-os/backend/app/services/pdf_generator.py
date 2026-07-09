import io
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.services.stats_service import compute_kpis

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

def generate_pdf_report(dataset_info, df):
    buffer = io.BytesIO()
    
    # SimpleDocTemplate
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=10
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20
    )
    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#333333'),
        spaceBefore=15,
        spaceAfter=10
    )
    normal_style = styles['Normal']
    
    story = []
    
    # Page 1: Cover / Header
    story.append(Paragraph("DataMind OS — Data Report", title_style))
    
    gen_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Quality Score Badge
    q_score = dataset_info.get('quality_score', 0)
    if q_score >= 85:
        q_color = "#10b981" # Green
    elif q_score >= 60:
        q_color = "#f59e0b" # Amber
    else:
        q_color = "#ef4444" # Red
        
    meta_text = (
        f"<b>Dataset:</b> {dataset_info['name']}<br/>"
        f"<b>Generated:</b> {gen_date}<br/>"
        f"<b>Rows:</b> {len(df)} | <b>Columns:</b> {len(df.columns)}<br/>"
        f"<b>Quality Score:</b> <font color='{q_color}'><b>{q_score}/100</b></font>"
    )
    story.append(Paragraph(meta_text, subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    # KPI Row
    story.append(Paragraph("Key Performance Indicators", h2_style))
    kpi_results = compute_kpis(df)
    kpis = kpi_results.get("kpis", [])
    
    if kpis:
        kpi_table_data = [[]]
        for k in kpis:
            name = k.get('name', '')
            value = k.get('value', 0)
            if isinstance(value, (int, float)):
                fmt_val = format_number(value)
            else:
                fmt_val = str(value)
                
            delta = k.get('delta', 0)
            delta_pct = k.get('delta_pct', 0)
            
            trend_char = "+" if delta > 0 else ""
            trend_color = "green" if delta > 0 else "red" if delta < 0 else "black"
            
            cell_text = f"<b>{name}</b><br/><font size=16>{fmt_val}</font><br/><font color='{trend_color}' size=10>{trend_char}{format_number(delta)} ({trend_char}{delta_pct:.1f}%)</font>"
            kpi_table_data[0].append(Paragraph(cell_text, styles['Normal']))
            
        kpi_table = Table(kpi_table_data, colWidths=[(doc.width) / len(kpis)] * len(kpis))
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.HexColor('#e2e8f0')),
            ('BOX', (0,0), (-1,-1), 0.25, colors.HexColor('#e2e8f0')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(kpi_table)
    else:
        story.append(Paragraph("No KPIs available.", normal_style))
        
    story.append(Spacer(1, 0.3*inch))
    
    # Page 2: Revenue Chart
    chart_data = kpi_results.get("chart_data", [])
    story.append(Paragraph("Revenue / Metric Chart", h2_style))
    
    if chart_data and len(chart_data) > 0:
        plt.figure(figsize=(7, 4))
        
        hist_data = [d for d in chart_data if d.get("value") is not None]
        fcst_data = [d for d in chart_data if d.get("forecast") is not None and d.get("value") is None]
        
        # We need a connecting point for the forecast line
        if hist_data and fcst_data:
            last_hist = hist_data[-1].copy()
            last_hist["forecast"] = last_hist["value"]
            fcst_data.insert(0, last_hist)
            
        if hist_data:
            x_hist = [d["name"] for d in hist_data]
            y_hist = [d["value"] for d in hist_data]
            plt.plot(x_hist, y_hist, 'b-', label='Historical', linewidth=2)
            
        if fcst_data:
            x_fcst = [d["name"] for d in fcst_data]
            y_fcst = [d["forecast"] for d in fcst_data]
            plt.plot(x_fcst, y_fcst, 'b--', label='Forecast', linewidth=2)
            
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150)
        plt.close()
        img_buffer.seek(0)
        
        img = Image(img_buffer, width=6.5*inch, height=3.7*inch)
        story.append(img)
        
        # Monthly values table
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Monthly Values", h2_style))
        
        table_data = [["Period", "Value", "Type"]]
        for d in chart_data:
            if d.get("value") is not None:
                table_data.append([
                    d["name"],
                    format_number(d["value"]),
                    "Actual"
                ])
            elif d.get("forecast") is not None:
                table_data.append([
                    d["name"],
                    format_number(d["forecast"]),
                    "Forecast"
                ])
            
        t = Table(table_data, colWidths=[2.5*inch, 2*inch, 2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No time dimension available.", normal_style))
        
    # Page break for other tables
    story.append(Spacer(1, 0.5*inch))
    
    # Numeric Columns Summary
    story.append(Paragraph("Numeric Columns Summary", h2_style))
    num_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(num_cols) > 0:
        table_data = [["Column", "Sum", "Mean", "Min", "Max"]]
        for col in num_cols[:15]:
            c_sum = format_number(df[col].sum())
            c_mean = format_number(df[col].mean())
            c_min = format_number(df[col].min())
            c_max = format_number(df[col].max())
            table_data.append([str(col), c_sum, c_mean, c_min, c_max])
            
        t2 = Table(table_data, colWidths=[2*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
        ]))
        story.append(t2)
    else:
        story.append(Paragraph("No numeric columns available.", normal_style))
        
    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.gray)
        canvas.drawRightString(doc.pagesize[0] - 40, 20, f"Page {doc.page}")
        canvas.drawString(40, 20, f"Generated by DataMind OS | {gen_date}")
        canvas.restoreState()
        
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    
    buffer.seek(0)
    return buffer
