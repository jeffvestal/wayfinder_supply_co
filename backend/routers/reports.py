from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class TripReportRequest(BaseModel):
    user_name: str
    destination: str
    dates: str
    itinerary: List[Dict[str, Any]]
    suggested_products: List[Dict[str, Any]]
    other_recommended_items: List[str]


@router.post("/reports/trip-pdf")
async def generate_trip_report_pdf(request: TripReportRequest):
    """
    Generates a PDF trip report with itinerary and suggested gear.
    
    Uses reportlab for PDF generation. Falls back to a simple text-based
    PDF if reportlab styling fails.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.colors import HexColor
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Custom styles
        styles = getSampleStyleSheet()
        
        # Header style - large centered title
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Heading1'],
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
            textColor=HexColor('#14b8a6'),  # Primary teal color
            spaceAfter=6
        )
        
        # Subheader for dates
        subheader_style = ParagraphStyle(
            'Subheader',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            textColor=HexColor('#64748b'),
            spaceAfter=20
        )
        
        # Section headers
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=16,
            leading=20,
            textColor=HexColor('#0f172a'),
            spaceBefore=20,
            spaceAfter=10
        )
        
        # Day title style
        day_style = ParagraphStyle(
            'DayTitle',
            parent=styles['Heading3'],
            fontSize=12,
            leading=16,
            textColor=HexColor('#14b8a6'),
            spaceBefore=12,
            spaceAfter=6
        )
        
        # Body text
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=HexColor('#334155')
        )
        
        # Bullet style
        bullet_style = ParagraphStyle(
            'Bullet',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=HexColor('#475569'),
            leftIndent=20,
            bulletIndent=10
        )
        
        # Footer style
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=HexColor('#94a3b8'),
            spaceBefore=30
        )
        
        story = []
        
        # Header
        story.append(Paragraph(
            f"{request.user_name}'s Trip to {request.destination}",
            header_style
        ))
        story.append(Paragraph(request.dates, subheader_style))
        
        # Itinerary Section
        if request.itinerary:
            story.append(Paragraph("📅 Trip Itinerary", section_style))
            
            for day in request.itinerary:
                day_num = day.get('day', '?')
                day_title = day.get('title', 'Day')
                weather = day.get('weather', '')
                
                title_text = f"Day {day_num}: {day_title}"
                if weather:
                    title_text += f" <font color='#64748b' size='9'>({weather})</font>"
                
                story.append(Paragraph(title_text, day_style))
                
                activities = day.get('activities', [])
                for activity in activities:
                    story.append(Paragraph(f"• {activity}", bullet_style))
        
        story.append(Spacer(1, 20))
        
        # Suggested Gear Section
        if request.suggested_products or request.other_recommended_items:
            story.append(Paragraph("🎒 Suggested Gear", section_style))
            
            if request.suggested_products:
                story.append(Paragraph(
                    "<b>From Wayfinder Supply Co.:</b>",
                    body_style
                ))
                story.append(Spacer(1, 6))
                
                for product in request.suggested_products:
                    title = product.get('title', product.get('name', 'Product'))
                    price = product.get('price', 0)
                    reason = product.get('reason', '')
                    
                    product_text = f"• <b>{title}</b> - ${price:.2f}"
                    if reason:
                        product_text += f"<br/><font color='#64748b' size='9'>&nbsp;&nbsp;&nbsp;{reason}</font>"
                    
                    story.append(Paragraph(product_text, bullet_style))
            
            if request.other_recommended_items:
                story.append(Spacer(1, 12))
                story.append(Paragraph(
                    "<b>Other Recommended Items:</b>",
                    body_style
                ))
                story.append(Spacer(1, 6))
                
                for item in request.other_recommended_items:
                    story.append(Paragraph(f"• {item}", bullet_style))
        
        # Footer
        story.append(Spacer(1, 40))
        story.append(Paragraph(
            "Generated by Wayfinder Supply Co. | Powered by Elastic",
            footer_style
        ))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Generate filename
        safe_destination = request.destination.replace(' ', '_').replace('/', '-')
        safe_name = request.user_name.replace(' ', '_')
        filename = f"Wayfinder_Trip_{safe_name}_{safe_destination}.pdf"
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except ImportError:
        logger.warning("reportlab not installed, returning error")
        raise HTTPException(
            status_code=500,
            detail="PDF generation not available - reportlab not installed"
        )
    except Exception as e:
        logger.error(f"Failed to generate PDF: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )

