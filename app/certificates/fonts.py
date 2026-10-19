from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path

_fonts_registered = False

def ensure_fonts():
    global _fonts_registered
    if _fonts_registered: return
    font_dir = Path(__file__).parent.parent / "resources" / "fonts"
    try:
        pdfmetrics.registerFont(TTFont("CertBody", font_dir / "DejaVuSans.ttf"))
        pdfmetrics.registerFont(TTFont("CertSerif", font_dir / "DejaVuSerif.ttf"))
        pdfmetrics.registerFont(TTFont("CertSerifBold", font_dir / "DejaVuSerif-Bold.ttf"))
    except Exception as e: 
        print(f"⚠️ Font warning: {e} - Falling back to Helvetica")
        pass
    _fonts_registered = True

def unsupported_chars(text, font="CertBody"):
    try:
        cmap = pdfmetrics.getFont(font).face.charToGlyph
        return sorted({c for c in text if ord(c) >= 32 and ord(c) not in cmap})
    except Exception: 
        # Catch all errors (like AttributeError for standard fonts) so it never crashes
        return [] 
