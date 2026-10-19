import io
from dataclasses import dataclass
from datetime import date
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor
from .fonts import ensure_fonts, unsupported_chars

class CertificateRenderError(Exception): pass

@dataclass
class CertificateData:
    name: str; course: str; issuer: str; issue_date: date; verification_code: str; certificate_id: str

def fit_size(text, font, max_width, start, minimum):
    size = start
    while size > minimum and pdfmetrics.stringWidth(text, font, size) > max_width: size -= 1
    return size

def render_certificate(data: CertificateData) -> bytes:
    ensure_fonts()
    font_body = "CertBody" if "CertBody" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    font_bold = "CertSerifBold" if "CertSerifBold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
    
    if unsupported_chars(data.name, font_body): raise CertificateRenderError("name contains unsupported characters")

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # Modern Tech Colors
    primary_blue = HexColor("#1E40AF")   
    secondary_blue = HexColor("#3B82F6") 
    accent_cyan = HexColor("#06B6D4")    
    dark_text = HexColor("#111827")
    gray_text = HexColor("#6B7280")

    c.setTitle(f"Certificate - {data.name}")
    c.setAuthor(data.issuer)

    # --- GEOMETRIC CORNER GRAPHICS ---
    c.setFillColor(primary_blue)
    p = c.beginPath(); p.moveTo(0, height); p.lineTo(250, height); p.lineTo(0, height-250); c.drawPath(p, fill=1, stroke=0)
    c.setFillColor(secondary_blue)
    p = c.beginPath(); p.moveTo(0, height-250); p.lineTo(150, height); p.lineTo(0, height-150); c.drawPath(p, fill=1, stroke=0)
    
    c.setFillColor(accent_cyan)
    p = c.beginPath(); p.moveTo(width, 0); p.lineTo(width-200, 0); p.lineTo(width, 200); c.drawPath(p, fill=1, stroke=0)
    c.setFillColor(primary_blue)
    p = c.beginPath(); p.moveTo(width, 0); p.lineTo(width-100, 0); p.lineTo(width, 100); c.drawPath(p, fill=1, stroke=0)

    # --- HEADER ---
    c.setFillColor(dark_text)
    c.setFont(font_bold, 16)
    c.drawRightString(width - 60, height - 60, data.issuer)

    # --- MAIN CONTENT (Left Aligned) ---
    margin_left = 100
    
    c.setFillColor(primary_blue)
    c.setFont(font_bold, 28)
    c.drawString(margin_left, height - 180, "Certificate of Participation")
    
    c.setFillColor(gray_text)
    c.setFont(font_body, 14)
    c.drawString(margin_left, height - 220, "This certificate is proudly presented to")
    
    # Recipient Name
    c.setFillColor(dark_text)
    name_size = fit_size(data.name, font_bold, width - 200, 48, 24)
    if name_size <= 24 and pdfmetrics.stringWidth(data.name, font_bold, 24) > width - 200: 
        raise CertificateRenderError("name too long to render")
        
    c.setFont(font_bold, name_size)
    c.drawString(margin_left, height - 280, data.name)
    
    # Course Details
    c.setFillColor(gray_text)
    c.setFont(font_body, 12)
    c.drawString(margin_left, height - 330, "For participating and upskilling with the")
    
    c.setFillColor(dark_text)
    course_size = fit_size(data.course, font_bold, width - 200, 18, 12)
    c.setFont(font_bold, course_size)
    c.drawString(margin_left, height - 355, data.course)
    
    # --- FOOTER ---
    # Signature Line
    c.setStrokeColor(HexColor("#D1D5DB"))
    c.setLineWidth(1)
    c.line(margin_left, 120, margin_left + 200, 120)
    
    c.setFillColor(dark_text)
    c.setFont(font_bold, 12)
    c.drawString(margin_left, 100, "Authorized Signature")
    c.setFillColor(gray_text)
    c.setFont(font_body, 10)
    c.drawString(margin_left, 85, data.issuer)

    # Date
    c.line(margin_left + 250, 120, margin_left + 400, 120)
    c.setFillColor(dark_text)
    c.setFont(font_bold, 12)
    c.drawString(margin_left + 250, 100, "Date of Issue")
    c.setFillColor(gray_text)
    c.setFont(font_body, 10)
    c.drawString(margin_left + 250, 85, data.issue_date.strftime('%d %B %Y'))

    # Verification ID (Right Aligned, No QR)
    c.setFillColor(dark_text)
    c.setFont(font_bold, 12)
    c.drawRightString(width - margin_left, 100, "Verification ID")
    c.setFillColor(gray_text)
    c.setFont(font_body, 10)
    c.drawRightString(width - margin_left, 85, data.verification_code)
    
    c.showPage(); c.save()
    return buf.getvalue()
