"""
Centralized Ticket Document Generator
Single source of truth for ticket PDF/print layout
Supports 1-4 units per ticket, new layout format
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import os


# ============================================
# HELPER FUNCTIONS
# ============================================

def format_phone(phone: Optional[str]) -> str:
    """Format phone number as (XXX) XXX-XXXX"""
    if not phone:
        return "—"
    
    # Strip non-digits
    digits = ''.join(c for c in phone if c.isdigit())
    
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return as-is if can't parse


def get_company_profile() -> Dict[str, Any]:
    """Get company profile for header (from database or settings)"""
    from core.db import get_conn
    
    default_profile = {
        "company": "GCC TECHNOLOGY",
        "address1": "123 Tech Street",
        "address2": "",
        "city": "Tech City",
        "state": "TC",
        "zip": "12345",
        "phone": "(555) 123-4567",
        "email": "support@gcc.com",
        "service_email": "service@gcc.com",
        "website": "www.gcc.com"
    }
    
    try:
        conn = get_conn()
        # Try CompanyProfile first
        row = conn.execute("SELECT * FROM CompanyProfile LIMIT 1").fetchone()
        if not row:
            # Fallback to CompanyInfo
            row = conn.execute("SELECT * FROM CompanyInfo LIMIT 1").fetchone()
        
        if row:
            row_dict = dict(row)
            return {
                "company": row_dict.get("company_name") or row_dict.get("name") or row_dict.get("company") or default_profile["company"],
                "address1": row_dict.get("address1") or "",
                "address2": row_dict.get("address2") or "",
                "city": row_dict.get("city") or "",
                "state": row_dict.get("state") or "",
                "zip": row_dict.get("zip") or "",
                "phone": row_dict.get("phone") or row_dict.get("fax") or default_profile["phone"],
                "email": row_dict.get("email") or default_profile["email"],
                "service_email": row_dict.get("service_email") or row_dict.get("email") or "",
                "website": row_dict.get("website") or default_profile["website"],
            }
        conn.close()
    except Exception:
        pass
    
    return default_profile


def get_ticket_units(ticket_id: int) -> List[Dict[str, Any]]:
    """
    Get units for a ticket (supports 1-4 units)
    Checks TicketUnits junction table first, falls back to ServiceCalls.unit_id
    Returns list of unit dicts with all specs
    """
    from core.db import get_conn
    
    conn = get_conn()
    units = []
    
    try:
        # First try junction table (multi-unit)
        junction_rows = conn.execute("""
            SELECT u.*
            FROM TicketUnits tu
            JOIN Units u ON tu.unit_id = u.unit_id
            WHERE tu.ticket_id = ?
            ORDER BY tu.sequence_order
            LIMIT 4
        """, (ticket_id,)).fetchall()
        
        if junction_rows:
            units = [dict(r) for r in junction_rows]
        else:
            # Fallback to single unit from ServiceCalls
            call_row = conn.execute("""
                SELECT u.*
                FROM ServiceCalls sc
                JOIN Units u ON sc.unit_id = u.unit_id
                WHERE sc.ID = ?
            """, (ticket_id,)).fetchone()
            
            if call_row:
                units = [dict(call_row)]
        
        conn.close()
    except Exception:
        conn.close()
    
    return units


def build_units_table_html(units: List[Dict[str, Any]]) -> str:
    """
    Generate bordered HTML table for units grid
    Columns: Tag | Type | Make | Model | Tonnage | Refrigerant | Voltage | Serial
    """
    if not units:
        return "<p>No units selected</p>"
    
    html = '''
    <table style="width: 100%; border-collapse: collapse; border: 2px solid #333; margin-top: 10px;">
        <thead>
            <tr style="background-color: #f0f0f0;">
                <th style="border: 1px solid #333; padding: 8px; text-align: left;">Tag</th>
                <th style="border: 1px solid #333; padding: 8px; text-align: left;">Type</th>
                <th style="border: 1px solid #333; padding: 8px; text-align: left;">Make</th>
                <th style="border: 1px solid #333; padding: 8px; text-align: left;">Model</th>
                <th style="border: 1px solid #333; padding: 8px; text-align: center;">Tonnage</th>
                <th style="border: 1px solid #333; padding: 8px; text-align: center;">Refrigerant</th>
                <th style="border: 1px solid #333; padding: 8px; text-align: center;">Voltage</th>
                <th style="border: 1px solid #333; padding: 8px; text-align: left;">Serial</th>
            </tr>
        </thead>
        <tbody>
    '''
    
    for unit in units[:4]:  # Max 4 units
        tag = unit.get('unit_tag') or f"RTU-{unit.get('unit_id', '?')}"
        eq_type = unit.get('equipment_type') or 'RTU'
        make = unit.get('make') or '—'
        model = unit.get('model') or '—'
        tonnage = unit.get('tonnage') or '—'
        refrig = unit.get('refrigerant_type') or '—'
        voltage = unit.get('voltage') or '—'
        serial = unit.get('serial') or '—'
        
        html += f'''
            <tr>
                <td style="border: 1px solid #333; padding: 6px;">{tag}</td>
                <td style="border: 1px solid #333; padding: 6px;">{eq_type}</td>
                <td style="border: 1px solid #333; padding: 6px;">{make}</td>
                <td style="border: 1px solid #333; padding: 6px;">{model}</td>
                <td style="border: 1px solid #333; padding: 6px; text-align: center;">{tonnage}</td>
                <td style="border: 1px solid #333; padding: 6px; text-align: center;">{refrig}</td>
                <td style="border: 1px solid #333; padding: 6px; text-align: center;">{voltage}</td>
                <td style="border: 1px solid #333; padding: 6px;">{serial}</td>
            </tr>
        '''
    
    html += '''
        </tbody>
    </table>
    '''
    
    return html


# ============================================
# PDF GENERATION (NEW LAYOUT)
# ============================================

def generate_ticket_pdf(ticket_id: int) -> Tuple[str, bytes]:
    """
    Generate service ticket PDF with new layout
    Company LEFT | Ticket# RIGHT
    Form title LEFT | Client info RIGHT
    Units table CENTER (bordered, 1-4 units with refrigerant + voltage)
    
    Returns: (pdf_path, pdf_bytes)
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import simpleSplit
    except ImportError:
        raise ImportError("reportlab required: pip install reportlab")
    
    from core.db import get_conn
    from core.tickets_repo import get_service_call
    
    # Get ticket data
    ticket = get_service_call(ticket_id)
    if not ticket:
        raise ValueError(f"Ticket {ticket_id} not found")
    
    # Get company profile
    company = get_company_profile()
    
    # Get units (1-4)
    units = get_ticket_units(ticket_id)
    
    # Get customer/location info
    conn = get_conn()
    customer_name = "—"
    customer_phone = "—"
    customer_email = "—"
    location_address = "—"
    
    if ticket.get('customer_id'):
        cust_row = conn.execute("SELECT * FROM Customers WHERE ID = ?", (ticket['customer_id'],)).fetchone()
        if cust_row:
            cust = dict(cust_row)
            customer_name = cust.get('company') or f"{cust.get('first_name', '')} {cust.get('last_name', '')}".strip() or "—"
            customer_phone = format_phone(cust.get('phone1') or cust.get('mobile'))
            customer_email = cust.get('email') or "—"
    
    if ticket.get('location_id'):
        loc_row = conn.execute("SELECT * FROM PropertyLocations WHERE ID = ?", (ticket['location_id'],)).fetchone()
        if loc_row:
            loc = dict(loc_row)
            parts = [loc.get('address1'), loc.get('city'), loc.get('state'), loc.get('zip')]
            location_address = ', '.join(p for p in parts if p) or "—"
            
            # Add business name if commercial property
            business_name = loc.get('business_name', '').strip()
            commercial = loc.get('commercial', 0)
            if commercial and business_name:
                location_address = f"{business_name}\n{location_address}"
    
    conn.close()
    
    # Create PDF
    os.makedirs("reports/service_orders", exist_ok=True)
    
    # Use ticket ID only (not control fields)
    ticket_no = str(ticket_id)
    unit_label = f"RTU-{units[0].get('unit_id')}" if units else "UNIT"
    filename = f"ServiceOrder_{datetime.now().strftime('%Y%m%d')}-{ticket_no.zfill(4)}_{unit_label}.pdf"
    pdf_path = os.path.join("reports", "service_orders", filename)
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    margin = 40
    left = margin
    right = width - margin
    y = height - margin
    
    # Company profile (LEFT)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left, y, company.get('company', 'GCC TECHNOLOGY'))
    y -= 16
    
    c.setFont("Helvetica", 10)
    if company.get('address1'):
        c.drawString(left, y, company['address1'])
        y -= 12
    
    city_line = f"{company.get('city', '')}, {company.get('state', '')} {company.get('zip', '')}".strip().strip(',')
    if city_line:
        c.drawString(left, y, city_line)
        y -= 12
    
    phone_formatted = format_phone(company.get('phone'))
    c.drawString(left, y, f"Phone: {phone_formatted}")
    
    # Ticket info (RIGHT - aligned with company address)
    y_right = height - margin
    c.setFont("Helvetica", 10)
    c.drawRightString(right, y_right, f"Ticket #: {ticket_no}")
    y_right -= 12
    
    created_date = ticket.get('created', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    date_str = created_date[:10] if len(created_date) >= 10 else created_date
    time_str = created_date[11:19] if len(created_date) >= 19 else "00:00:00"
    
    c.drawRightString(right, y_right, f"Date: {date_str}")
    y_right -= 12
    c.drawRightString(right, y_right, f"Time: {time_str}")
    
    # Move y to lowest point
    y = min(y, y_right) - 20
    
    # Divider
    c.line(left, y, right, y)
    y -= 20
    
    # Form title (LEFT) | Client info (RIGHT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left, y, "WORK ORDER")
    
    # Client info (RIGHT)
    y_client = y
    c.setFont("Helvetica", 10)
    c.drawRightString(right, y_client, f"Customer: {customer_name}")
    y_client -= 12
    
    # Draw location address (handle multi-line for business name)
    location_lines = location_address.split('\n')
    for line in location_lines:
        c.drawRightString(right, y_client, line)
        y_client -= 12
    
    c.drawRightString(right, y_client, f"Phone: {customer_phone}")
    y_client -= 12
    c.drawRightString(right, y_client, f"Email: {customer_email}")
    
    y = min(y - 14, y_client) - 20
    
    # Divider
    c.line(left, y, right, y)
    y -= 20
    
    # UNITS INFORMATION (LEFT aligned, BOLD)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "UNITS INFORMATION")
    y -= 16
    
    # Units table (bordered grid)
    if units:
        col_widths = [60, 60, 80, 60, 50, 70, 50, 80]
        col_headers = ["Tag", "Type", "Make", "Model", "Tons", "Refrig", "V", "Serial"]
        
        # Header row
        c.setFont("Helvetica-Bold", 9)
        x = left
        row_height = 20
        c.rect(left, y - row_height, right - left, row_height, stroke=1, fill=0)
        
        for i, header in enumerate(col_headers):
            c.drawString(x + 4, y - 14, header)
            x += col_widths[i]
        
        y -= row_height
        
        # Data rows
        c.setFont("Helvetica", 9)
        for unit in units[:4]:
            c.rect(left, y - row_height, right - left, row_height, stroke=1, fill=0)
            
            x = left
            values = [
                unit.get('unit_tag') or f"RTU-{unit.get('unit_id', '?')}",
                unit.get('equipment_type') or 'RTU',
                unit.get('make') or '—',
                unit.get('model') or '—',
                str(unit.get('tonnage') or '—'),
                unit.get('refrigerant_type') or '—',
                str(unit.get('voltage') or '—'),
                unit.get('serial') or '—'
            ]
            
            for i, val in enumerate(values):
                c.drawString(x + 4, y - 14, str(val)[:15])  # Truncate if too long
                x += col_widths[i]
            
            y -= row_height
    else:
        c.setFont("Helvetica", 9)
        c.drawString(left, y, "No units assigned")
        y -= 20

    # Add materials and labor sections with boxes like the old form
    y -= 10
    box_width = right - left
    box_height = 60

    # Materials box
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "MATERIALS & SERVICES (TECH TO FILL)")
    y -= 14
    c.rect(left, y - box_height, box_width, box_height, stroke=1, fill=0)
    c.setFont("Helvetica", 10)
    materials_text = ticket.get('materials_services') or "—"
    materials_lines = simpleSplit(materials_text, "Helvetica", 10, box_width - 8)
    y_line = y - 12
    for line in materials_lines:
        if y_line <= y - box_height:
            break
        c.drawString(left + 6, y_line, line)
        y_line -= 12
    y = y - box_height - 16

    # Labor box
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "LABOR DESCRIPTION (TECH TO FILL)")
    y -= 14
    c.rect(left, y - box_height, box_width, box_height, stroke=1, fill=0)
    c.setFont("Helvetica", 10)
    labor_text = ticket.get('labor_description') or "—"
    labor_lines = simpleSplit(labor_text, "Helvetica", 10, box_width - 8)
    y_line = y - 12
    for line in labor_lines:
        if y_line <= y - box_height:
            break
        c.drawString(left + 6, y_line, line)
        y_line -= 12
    y = y - box_height - 20

    # Signature line
    c.setFont("Helvetica", 10)
    c.drawString(left, y, "Customer Signature: ____________________________   Date: ____________")
    
    # Save PDF
    c.save()
    
    # Read bytes
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    return (pdf_path, pdf_bytes)
