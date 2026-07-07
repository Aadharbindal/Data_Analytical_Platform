from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import datetime

router = APIRouter()

@router.get("/pdf", summary="Export Dashboard to PDF")
def export_dashboard_pdf():
    buffer = io.BytesIO()
    
    # Create the PDF object, using the buffer as its "file."
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Draw things on the PDF
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, "AI BI OS - Executive Dashboard Report")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    p.drawString(50, height - 120, "Key Insights:")
    p.setFont("Helvetica", 10)
    p.drawString(70, height - 140, "- Mobile users generated 35% of Revenue (+12.5%)")
    p.drawString(70, height - 160, "- Referral traffic grew by 4% over the last 30 days.")
    p.drawString(70, height - 180, "- Overall Conversion Rate stands strong at 55.8%")

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 230, "Current KPIs:")
    p.setFont("Helvetica", 10)
    p.drawString(70, height - 250, "Total Revenue: $130,800")
    p.drawString(70, height - 270, "Active Customers: 8,492")
    p.drawString(70, height - 290, "Customer Acquisition Cost: $124")

    # Close the PDF object cleanly
    p.showPage()
    p.save()

    buffer.seek(0)
    return StreamingResponse(
        buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": "attachment; filename=executive_report.pdf"}
    )
