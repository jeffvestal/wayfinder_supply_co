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
    Generates a professional PDF trip report with itinerary and suggested gear.
    Styled to match Wayfinder Supply Co. branding.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, KeepTogether
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.lib.colors import HexColor, Color
        
        # Brand colors
        PRIMARY = HexColor('#14b8a6')      # Teal
        PRIMARY_DARK = HexColor('#0d9488')
        SLATE_900 = HexColor('#0f172a')    # Dark navy
        SLATE_700 = HexColor('#334155')
        SLATE_500 = HexColor('#64748b')
        SLATE_300 = HexColor('#cbd5e1')
        SLATE_100 = HexColor('#f1f5f9')
        WHITE = HexColor('#ffffff')
        AMBER = HexColor('#f59e0b')
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=0.6*inch,
            leftMargin=0.6*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Custom styles
        styles = getSampleStyleSheet()
        
        # Main title - large, teal, centered
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=28,
            leading=34,
            alignment=TA_CENTER,
            textColor=PRIMARY,
            fontName='Helvetica-Bold',
            spaceAfter=4
        )
        
        # Subtitle for dates
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            textColor=SLATE_500,
            fontName='Helvetica',
            spaceAfter=24
        )
        
        # Section header - bold, dark
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=18,
            leading=22,
            textColor=SLATE_900,
            fontName='Helvetica-Bold',
            spaceBefore=24,
            spaceAfter=12
        )
        
        # Subsection header
        subsection_style = ParagraphStyle(
            'Subsection',
            parent=styles['Heading3'],
            fontSize=13,
            leading=16,
            textColor=PRIMARY_DARK,
            fontName='Helvetica-Bold',
            spaceBefore=12,
            spaceAfter=6
        )
        
        # Body text
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=SLATE_700,
            fontName='Helvetica'
        )
        
        # Activity bullet style
        activity_style = ParagraphStyle(
            'Activity',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=SLATE_700,
            fontName='Helvetica',
            leftIndent=15,
            spaceBefore=2,
            spaceAfter=2
        )
        
        # Weather label style
        weather_style = ParagraphStyle(
            'Weather',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=SLATE_500,
            fontName='Helvetica-Oblique',
            leftIndent=15,
            spaceBefore=4
        )
        
        # Table header style
        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            textColor=WHITE,
            fontName='Helvetica-Bold'
        )
        
        # Table cell style
        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=10,
            leading=13,
            textColor=SLATE_700,
            fontName='Helvetica'
        )
        
        # Footer style
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=SLATE_500,
            fontName='Helvetica',
            spaceBefore=30
        )
        
        story = []
        
        # === HEADER SECTION ===
        story.append(Paragraph(
            f"{request.user_name}'s Trip to {request.destination}",
            title_style
        ))
        story.append(Paragraph(request.dates, subtitle_style))
        
        # Divider line
        story.append(HRFlowable(
            width="100%",
            thickness=2,
            color=PRIMARY,
            spaceAfter=20
        ))
        
        # === TRIP OVERVIEW TABLE ===
        story.append(Paragraph("Trip Overview", section_style))
        
        # Calculate duration from itinerary
        duration = f"{len(request.itinerary)} day{'s' if len(request.itinerary) != 1 else ''}" if request.itinerary else "N/A"
        
        overview_data = [
            [Paragraph("<b>Destination:</b>", body_style), Paragraph(request.destination, body_style)],
            [Paragraph("<b>Dates:</b>", body_style), Paragraph(request.dates, body_style)],
            [Paragraph("<b>Duration:</b>", body_style), Paragraph(duration, body_style)],
        ]
        
        overview_table = Table(overview_data, colWidths=[1.5*inch, 4.5*inch])
        overview_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(overview_table)
        
        # === ITINERARY SECTION ===
        if request.itinerary:
            story.append(Paragraph("Day-by-Day Itinerary", section_style))
            
            for day in request.itinerary:
                day_num = day.get('day', '?')
                day_title = day.get('title', 'Day')
                weather = day.get('weather', '')
                activities = day.get('activities', [])
                
                # Day header
                day_content = []
                day_content.append(Paragraph(
                    f"Day {day_num}: {day_title}",
                    subsection_style
                ))
                
                # Activities as numbered list
                for i, activity in enumerate(activities, 1):
                    day_content.append(Paragraph(
                        f"{i}. {activity}",
                        activity_style
                    ))
                
                # Weather info
                if weather:
                    day_content.append(Paragraph(
                        f"<b>Weather:</b> {weather}",
                        weather_style
                    ))
                
                # Keep day content together
                story.append(KeepTogether(day_content))
                story.append(Spacer(1, 8))
        
        # === RECOMMENDED GEAR SECTION ===
        if request.suggested_products or request.other_recommended_items:
            story.append(Paragraph("Recommended Gear", section_style))
            
            if request.suggested_products:
                # Build table data with Paragraph objects for proper rendering
                gear_data = [[
                    Paragraph("Item", table_header_style),
                    Paragraph("Price", table_header_style),
                    Paragraph("Reason", table_header_style)
                ]]
                
                total_price = 0.0
                
                for product in request.suggested_products:
                    title = product.get('title', product.get('name', 'Product'))
                    price = float(product.get('price', 0))
                    reason = product.get('reason', '')
                    total_price += price
                    
                    gear_data.append([
                        Paragraph(str(title), table_cell_style),
                        Paragraph(f"${price:.2f}", table_cell_style),
                        Paragraph(str(reason), table_cell_style)
                    ])
                
                # Total row
                gear_data.append([
                    Paragraph("<b>TOTAL</b>", table_cell_style),
                    Paragraph(f"<b>${total_price:.2f}</b>", table_cell_style),
                    Paragraph("", table_cell_style)
                ])
                
                gear_table = Table(gear_data, colWidths=[3*inch, 1*inch, 2.5*inch])
                gear_table.setStyle(TableStyle([
                    # Header row styling
                    ('BACKGROUND', (0, 0), (-1, 0), SLATE_900),
                    ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    
                    # All cells
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    
                    # Alternating row colors (skip header and total)
                    ('BACKGROUND', (0, 1), (-1, -2), SLATE_100),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -2), [WHITE, SLATE_100]),
                    
                    # Total row styling
                    ('BACKGROUND', (0, -1), (-1, -1), SLATE_300),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    
                    # Grid
                    ('GRID', (0, 0), (-1, -1), 0.5, SLATE_300),
                    ('LINEBELOW', (0, 0), (-1, 0), 2, PRIMARY),
                    
                    # Alignment
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ]))
                story.append(gear_table)
            
            # Other recommended items
            if request.other_recommended_items:
                story.append(Spacer(1, 16))
                story.append(Paragraph(
                    "Additional Items to Consider:",
                    subsection_style
                ))
                
                for item in request.other_recommended_items:
                    story.append(Paragraph(
                        f"• {item}",
                        activity_style
                    ))
        
        # === FOOTER ===
        story.append(Spacer(1, 30))
        story.append(HRFlowable(
            width="100%",
            thickness=1,
            color=SLATE_300,
            spaceAfter=12
        ))
        story.append(Paragraph(
            "Generated by Wayfinder Supply Co | Powered by Elastic",
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
