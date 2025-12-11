from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

router = APIRouter()


class ItineraryDay(BaseModel):
    day: int
    title: str
    activities: List[str]
    distance: Optional[str] = None


class SuggestedProduct(BaseModel):
    name: str
    price: float
    category: str
    reason: str


class TripReportRequest(BaseModel):
    user_name: str
    destination: str
    dates: str
    itinerary: List[ItineraryDay]
    suggested_products: List[SuggestedProduct]
    other_recommended_items: List[str]


@router.post("/reports/trip-pdf")
async def generate_trip_report_pdf(request: TripReportRequest):
    """
    Generate a professional PDF trip report.
    """
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=6,
        textColor=colors.HexColor('#0ea5e9'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subheader_style = ParagraphStyle(
        'CustomSubheader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=20,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#1e293b'),
        fontName='Helvetica-Bold'
    )
    
    day_title_style = ParagraphStyle(
        'DayTitle',
        parent=styles['Heading3'],
        fontSize=13,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor('#0ea5e9'),
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        textColor=colors.HexColor('#374151'),
        leading=14
    )
    
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=body_style,
        leftIndent=20,
        bulletIndent=10,
        spaceBefore=2,
        spaceAfter=2
    )
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER,
        spaceBefore=30
    )
    
    # Build the document content
    story = []
    
    # Header
    story.append(Paragraph(f"{request.user_name}'s Trip to {request.destination}", header_style))
    story.append(Paragraph(request.dates, subheader_style))
    story.append(Spacer(1, 20))
    
    # Itinerary Section
    if request.itinerary:
        story.append(Paragraph("📅 Your Itinerary", section_title_style))
        
        for day in request.itinerary:
            day_header = f"Day {day.day}: {day.title}"
            if day.distance:
                day_header += f" ({day.distance})"
            story.append(Paragraph(day_header, day_title_style))
            
            for activity in day.activities:
                # Clean up any HTML-like tags
                clean_activity = activity.replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(f"• {clean_activity}", bullet_style))
        
        story.append(Spacer(1, 15))
    
    # Suggested Gear Section
    if request.suggested_products:
        story.append(Paragraph("🎒 Suggested Gear", section_title_style))
        
        # Create a table for products
        table_data = [['Product', 'Category', 'Price', 'Why']]
        
        for product in request.suggested_products:
            table_data.append([
                product.name[:40] + ('...' if len(product.name) > 40 else ''),
                product.category,
                f"${product.price:.2f}",
                product.reason[:50] + ('...' if len(product.reason) > 50 else '')
            ])
        
        table = Table(table_data, colWidths=[2.2*inch, 1.2*inch, 0.8*inch, 2.3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#374151')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ]))
        story.append(table)
        story.append(Spacer(1, 15))
    
    # Other Recommended Items
    if request.other_recommended_items:
        story.append(Paragraph("📋 Additional Recommendations", section_title_style))
        
        for item in request.other_recommended_items:
            clean_item = item.replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"• {clean_item}", bullet_style))
        
        story.append(Spacer(1, 15))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("Generated by Wayfinder Supply Co | Powered by Elastic", footer_style))
    
    # Build PDF
    doc.build(story)
    
    # Return the PDF
    buffer.seek(0)
    
    filename = f"trip-to-{request.destination.lower().replace(' ', '-')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

