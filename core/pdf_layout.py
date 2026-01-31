"""Shared PDF layout helpers for GCC Monitoring reports."""

from datetime import datetime
from typing import Iterable, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from core.settings_repo import get_company_profile


def fit_text_to_width(text: str, width_inches: float, font_size: int = 8) -> str:
    """Fit text to column width by truncating with ellipsis if needed.
    
    Estimates character count that fits based on font size and width.
    Returns text truncated to fit within width, with '...' if truncated.
    """
    if not text or not text.strip():
        return "—"
    
    text = str(text).strip()
    
    # Approximate characters per inch for Helvetica at given font size
    # At 8pt: ~17 chars per inch, 7pt: ~19 chars per inch, 9pt: ~15 chars per inch
    chars_per_inch = 17 + (8 - font_size) * 0.5
    max_chars = int(width_inches * chars_per_inch) - 1
    
    if len(text) <= max_chars:
        return text
    
    # Truncate and add ellipsis
    return text[:max_chars - 3] + "..."


PDF_BRANDING: dict = {}
_BRANDING_LOADED = False


def set_pdf_branding(data: dict) -> None:
    """Override PDF branding globally (used by header/footer)."""
    global PDF_BRANDING, _BRANDING_LOADED
    PDF_BRANDING = dict(data or {})
    _BRANDING_LOADED = True


def _build_branding(profile: dict) -> dict:
    name = (profile.get("name") or profile.get("company") or "GCC Technology").strip()
    website = (profile.get("website") or "").strip()
    phone = (profile.get("phone") or "").strip()
    email = (profile.get("email") or "").strip()
    address1 = (profile.get("address1") or "").strip()
    address2 = (profile.get("address2") or "").strip()
    city = (profile.get("city") or "").strip()
    state = (profile.get("state") or "").strip()
    zip_code = (profile.get("zip") or "").strip()

    address_lines = [line for line in [address1, address2] if line]
    city_line = ", ".join([p for p in [city, state] if p])
    if zip_code:
        city_line = f"{city_line} {zip_code}".strip()
    if city_line:
        address_lines.append(city_line)

    contact_line = website or phone or email
    footer_line = " | ".join([p for p in [name, ", ".join(address_lines), phone or email or website] if p])

    return {
        "company_name": name,
        "website": website,
        "phone": phone,
        "email": email,
        "address_lines": address_lines,
        "contact_line": contact_line,
        "footer_text": footer_line or f"{name} | HVAC Monitoring System",
    }


def load_pdf_branding(force: bool = False) -> dict:
    """Load branding from CompanyInfo (settings) into a global cache."""
    global PDF_BRANDING, _BRANDING_LOADED
    if _BRANDING_LOADED and not force:
        return PDF_BRANDING

    profile = get_company_profile() or {}
    PDF_BRANDING = _build_branding(profile)
    _BRANDING_LOADED = True
    return PDF_BRANDING


def _get_page_size(c):
    try:
        return c._pagesize
    except Exception:
        return letter


def create_pdf_header(c, title: str, subtitle: str = "", max_width: float = 6.5) -> float:
    """Draw common PDF header and return y start position.
    
    Args:
        c: Canvas object
        title: Report title (trimmed to max_width if needed)
        subtitle: Optional subtitle (trimmed to max_width if needed)
        max_width: Maximum width in inches for title/subtitle (default 6.5")
    """
    branding = load_pdf_branding()
    width, height = _get_page_size(c)

    center_x = width / 2
    
    # Trim title to max width (18pt font size considered)
    trimmed_title = fit_text_to_width(title, max_width, 18)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(center_x, height - 0.55 * inch, branding.get("company_name", "GCC Technology"))

    c.setFont("Helvetica", 9)
    contact_line = branding.get("contact_line") or ""
    if contact_line:
        c.drawCentredString(center_x, height - 0.72 * inch, contact_line)

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(center_x, height - 0.98 * inch, trimmed_title)

    if subtitle:
        # Trim subtitle to max width (11pt font size considered)
        trimmed_subtitle = fit_text_to_width(subtitle, max_width, 11)
        c.setFont("Helvetica", 11)
        c.drawCentredString(center_x, height - 1.14 * inch, trimmed_subtitle)

    c.setFont("Helvetica", 8)
    date_str = f"Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}"
    c.drawCentredString(center_x, height - 1.28 * inch, date_str)

    c.setLineWidth(1)
    c.line(0.75 * inch, height - 1.45 * inch, width - 0.75 * inch, height - 1.45 * inch)

    return height - 1.6 * inch


def create_pdf_footer(c, page_num: int) -> None:
    """Draw common PDF footer."""
    branding = load_pdf_branding()
    width, height = _get_page_size(c)
    center_x = width / 2

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)

    c.drawCentredString(center_x, 0.45 * inch, branding.get("footer_text", "GCC Technology | HVAC Monitoring System"))
    c.drawCentredString(center_x, 0.28 * inch, f"Page {page_num}")


def build_report_table(
    headers: List[str],
    rows: Iterable[Iterable[str]],
    col_widths: List[float],
    *,
    header_font_size: int = 9,
    body_font_size: int = 8,
    header_bg=colors.HexColor("#111827"),
    header_text=colors.white,
    grid_width: float = 0.35,
    grid_color=colors.HexColor("#D1D5DB"),
    row_backgrounds=(colors.white, colors.HexColor("#F9FAFB")),
    align_left_until: Optional[int] = None,
    align_right_from: Optional[int] = None,
    align_center_cols: Optional[List[int]] = None,
    padding: int = 4,
    wordwrap: bool = True,
    valign: str = "TOP",
):
    """Build a reusable, wrapped table with consistent styling."""
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        "pdf_header",
        parent=styles["Normal"],
        fontSize=header_font_size,
        leading=header_font_size + 1,
        textColor=header_text,
    )
    body_style = ParagraphStyle(
        "pdf_body",
        parent=styles["Normal"],
        fontSize=body_font_size,
        leading=body_font_size + 1,
        textColor=colors.HexColor("#111827"),
    )

    def normalize(value, col_idx: int = 0, is_header: bool = False) -> str:
        if value is None:
            return "—"
        text = str(value).strip()
        if not text:
            return "—"
        
        # Get column width (convert from inches if needed)
        col_width = col_widths[min(col_idx, len(col_widths) - 1)]
        if not isinstance(col_width, (int, float)) or col_width > 100:
            col_width = col_width / inch if col_width > 100 else col_width
        
        font_sz = header_font_size if is_header else body_font_size
        return fit_text_to_width(text, col_width, font_sz)

    table_data = [[Paragraph(normalize(h, i, True), header_style) for i, h in enumerate(headers)]]
    for row in rows:
        table_data.append([Paragraph(normalize(cell, j, False), body_style) for j, cell in enumerate(row)])

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), header_text),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), header_font_size),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), body_font_size),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), padding),
        ('RIGHTPADDING', (0, 0), (-1, -1), padding),
        ('LINEBELOW', (0, 0), (-1, 0), 0.75, colors.HexColor("#111827")),
        ('GRID', (0, 0), (-1, -1), grid_width, grid_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), list(row_backgrounds)),
        ('VALIGN', (0, 0), (-1, -1), valign),
    ]

    if wordwrap:
        style_cmds.append(('WORDWRAP', (0, 0), (-1, -1), True))

    if align_left_until is not None:
        style_cmds.append(('ALIGN', (0, 0), (align_left_until, -1), 'LEFT'))
    else:
        style_cmds.append(('ALIGN', (0, 0), (-1, -1), 'LEFT'))

    if align_right_from is not None:
        style_cmds.append(('ALIGN', (align_right_from, 0), (-1, -1), 'RIGHT'))

    if align_center_cols:
        for col in align_center_cols:
            style_cmds.append(('ALIGN', (col, 0), (col, -1), 'CENTER'))

    table.setStyle(TableStyle(style_cmds))
    table.hAlign = 'LEFT'
    return table


def draw_table_paged(
    c,
    table,
    *,
    x: float,
    y: float,
    available_width: float,
    bottom_margin: float,
    page_num: int,
    header_title: str,
    header_subtitle: str,
    header_fn,
    footer_fn,
    continuation_title: Optional[str] = None,
    header_max_width: float = 6.5,
):
    """Draw a table across pages without leaving empty first pages or overwriting.

    Args:
        c: Canvas object
        table: ReportLab Table object to draw
        x: X position to draw table
        y: Y position to draw table
        available_width: Width available for table
        bottom_margin: Bottom margin in inches
        page_num: Starting page number
        header_title: Report title
        header_subtitle: Report subtitle
        header_fn: Function to draw header (must accept c, title, subtitle, max_width)
        footer_fn: Function to draw footer
        continuation_title: Title for continuation pages (default: header_title)
        header_max_width: Max width in inches for header titles (default 6.5")

    Returns (page_num, last_y) where last_y is the y-position after the table.
    """
    if continuation_title is None:
        continuation_title = header_title

    y_cursor = y
    available_height = y_cursor - bottom_margin
    
    # Get all table splits upfront
    parts = table.split(available_width, available_height)
    if not parts:
        parts = [table]

    for idx, part in enumerate(parts):
        # Calculate space needed for this part
        part_w, part_h = part.wrapOn(c, available_width, available_height)
        
        # Check if part fits on current page
        if y_cursor - part_h < bottom_margin:
            # Need a new page (don't draw footer on intermediate pages)
            c.showPage()
            page_num += 1
            y_cursor = header_fn(c, continuation_title, f"Page {page_num}", header_max_width)
            available_height = y_cursor - bottom_margin
            # Recalculate height on new page
            part_w, part_h = part.wrapOn(c, available_width, available_height)
        
        # Draw the part
        part.drawOn(c, x, y_cursor - part_h)
        y_cursor = y_cursor - part_h

    return page_num, y_cursor
