"""
Report PDF Generator
Generates PDF exports for various report types
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from pathlib import Path
from core.pdf_layout import create_pdf_header, create_pdf_footer, build_report_table, draw_table_paged
from core.settings_repo import get_report_settings


def get_pdf_dir() -> Path:
    """Get or create reports PDF directory from settings"""
    # Try to get settings, fall back to default if table doesn't exist yet
    try:
        settings = get_report_settings()
        
        # Check if external storage is enabled
        if settings.get("is_enabled") and settings.get("storage_type") != "local":
            # External storage configured - for now just log it
            # Full implementation would handle S3, Azure, SFTP, etc.
            print(f"Note: External report storage configured ({settings.get('storage_type')})")
        
        # Use configured path or default
        path_str = settings.get("storage_path") or "reports/pdfs"
    except Exception:
        # ReportSettings table doesn't exist yet - use default
        path_str = "reports/pdfs"
    
    # If relative path, make it relative to project root
    pdf_dir = Path(path_str) if Path(path_str).is_absolute() else Path(__file__).parent.parent / path_str
    pdf_dir.mkdir(parents=True, exist_ok=True)
    return pdf_dir





# ============================================
# EQUIPMENT INVENTORY PDF
# ============================================

def generate_equipment_inventory_pdf(data: List[Dict[str, Any]], customer_id: Optional[int] = None) -> Tuple[str, bytes]:
    """Generate Equipment Inventory Report PDF - Crew-Friendly Format"""
    
    filename = f"equipment_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = get_pdf_dir() / filename
    
    c = canvas.Canvas(str(filepath), pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Calculate usable dimensions
    usable_width = width - 0.5 * inch  # 0.25" left + 0.25" right
    header_height = 1.8 * inch  # Header + subtitle space
    footer_space = 0.4 * inch  # Space for page number
    bottom_margin = 0.2 * inch
    available_height_per_page = height - header_height - footer_space - bottom_margin
    
    # Table headers - crew-focused columns (Make and Model separate)
    headers = ["Customer", "Location Address", "Unit Tag", "Make", "Model", "Serial Number", "Install Date"]
    
    # Prepare table data with full location info
    table_data = [headers]
    for row in data:
        # Build full location string with proper trimming
        location_parts = []
        if row.get("location_address"):
            location_parts.append(str(row["location_address"]).strip())
        if row.get("location_city"):
            location_parts.append(str(row["location_city"]).strip())
        if row.get("location_state"):
            location_parts.append(str(row["location_state"]).strip())
        full_location = ", ".join(filter(None, location_parts))
        
        # Trim all fields properly
        customer_name = (row.get("customer_name") or "N/A").strip()
        unit_tag = (row.get("unit_tag") or f"Unit {row.get('unit_id', '')}").strip()
        make = (row.get("make") or "—").strip()
        model = (row.get("model") or "—").strip()
        serial = (row.get("serial") or "—").strip()
        inst_date = (row.get("inst_date") or "—").strip()
        
        table_data.append([
            customer_name,
            full_location,
            unit_tag,
            make,
            model,
            serial,
            inst_date,
        ])
    
    # Create table with adjusted column widths (7 columns now)
    col_widths = [1.5*inch, 2.5*inch, 1.0*inch, 1.2*inch, 1.2*inch, 1.3*inch, 0.9*inch]
    
    # Validate table fits usable width
    total_width = sum(col_widths)
    if total_width > usable_width:
        raise ValueError(f"Table width {total_width/inch:.2f}\" exceeds usable width {usable_width/inch:.2f}\"")
    
    # Split data into pages
    rows_per_page = max(5, int(available_height_per_page / (0.2 * inch)))
    header_row = table_data[0]
    data_rows = table_data[1:]
    
    page_num = 1
    row_idx = 0
    
    while row_idx < len(data_rows):
        # Draw header
        y = create_pdf_header(c, "Equipment Inventory - Crew Guide", f"{len(data_rows)} Units", max_width=6.5)
        
        # Add subtitle
        c.setFont("Helvetica-Bold", 10)
        c.drawString(0.25 * inch, y, "Customer → Location → Equipment Details")
        y -= 0.3 * inch
        
        # On first page, subtract 2 rows for footer space; on subsequent pages use full rows_per_page
        rows_for_this_page = rows_per_page - 2 if page_num == 1 else rows_per_page
        rows_to_draw = data_rows[row_idx:row_idx + rows_for_this_page]
        
        if rows_to_draw:
            page_table = build_report_table(
                header_row,
                rows_to_draw,
                col_widths,
                header_font_size=9,
                body_font_size=8,
                header_bg=colors.HexColor('#1a1a1a'),
                header_text=colors.white,
                grid_width=0.75,
                row_backgrounds=(colors.white, colors.HexColor('#f0f0f0')),
                align_left_until=6,
            )
            
            table_w, table_h = page_table.wrapOn(c, usable_width, available_height_per_page)
            page_table.drawOn(c, 0.25 * inch, y - table_h)
            
            # Draw page number at bottom right only
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawRightString(width - 0.25 * inch, 0.3 * inch, f"Page {page_num}")
        
        row_idx += rows_for_this_page
        
        # If more rows to draw, create new page
        if row_idx < len(data_rows):
            c.showPage()
            page_num += 1
    
    c.save()
    
    with open(filepath, "rb") as f:
        pdf_bytes = f.read()
    
    return str(filepath), pdf_bytes


# ============================================
# EQUIPMENT AGE ANALYSIS PDF
# ============================================

def generate_equipment_age_pdf(data: List[Dict[str, Any]]) -> Tuple[str, bytes]:
    """Generate Equipment Age Analysis PDF"""
    
    filename = f"equipment_age_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = get_pdf_dir() / filename
    
    c = canvas.Canvas(str(filepath), pagesize=letter)
    width, height = letter
    
    # Calculate usable width (page width - margins)
    usable_width = width - 0.5 * inch  # 0.25" left + 0.25" right
    
    page_num = 1
    y = create_pdf_header(c, "Equipment Age Analysis", f"{len(data)} Units", max_width=5.5)
    
    # Summary stats
    total = len(data)
    under_warranty = sum(1 for d in data if d.get("warranty_status") == "Under Warranty")
    out_warranty = sum(1 for d in data if d.get("warranty_status") == "Out of Warranty")
    
    c.setFont("Helvetica-Bold", 11)
    y -= 0.3 * inch
    c.drawString(0.25 * inch, y, "Summary:")
    
    c.setFont("Helvetica", 10)
    y -= 0.2 * inch
    c.drawString(1 * inch, y, f"Total Units: {total}")
    y -= 0.15 * inch
    c.drawString(1 * inch, y, f"Under Warranty: {under_warranty}")
    y -= 0.15 * inch
    c.drawString(1 * inch, y, f"Out of Warranty: {out_warranty}")
    
    y -= 0.4 * inch
    
    # Table headers
    headers = ["Customer", "Unit", "Make", "Model", "Install Date", "Age Group", "Warranty"]
    
    # Prepare table data
    table_data = [headers]
    for row in data[:50]:  # Limit to 50 rows for single page
        table_data.append([
            (row.get("customer_name") or "").strip(),
            (row.get("unit_tag") or "").strip(),
            (row.get("make") or "—").strip(),
            (row.get("model") or "—").strip(),
            (row.get("inst_date") or "—").strip(),
            (row.get("age_group") or "—").strip(),
            (row.get("warranty_status") or "—").strip(),
        ])
    
    # Create table
    col_widths = [1.4*inch, 1*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch, 1*inch]
    
    # Validate table fits usable width
    total_width = sum(col_widths)
    if total_width > usable_width:
        raise ValueError(f"Table width {total_width/inch:.2f}\" exceeds usable width {usable_width/inch:.2f}\"")
    
    table = build_report_table(
        headers,
        table_data[1:],
        col_widths,
        header_font_size=9,
        body_font_size=8,
        align_left_until=6,
    )
    
    # Draw table (use consistent margins)
    table_width, table_height = table.wrapOn(c, usable_width, height)
    table.drawOn(c, 0.25 * inch, y - table_height)
    
    if len(data) > 50:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(0.25 * inch, 1 * inch, f"Showing first 50 of {len(data)} units")
    
    create_pdf_footer(c, page_num)
    c.save()
    
    with open(filepath, "rb") as f:
        pdf_bytes = f.read()
    
    return str(filepath), pdf_bytes


# ============================================
# SERVICE TICKETS PDF
# ============================================

def generate_tickets_report_pdf(data: List[Dict[str, Any]], status: Optional[str] = None) -> Tuple[str, bytes]:
    """Generate Service Tickets Report PDF"""
    
    filename = f"tickets_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = get_pdf_dir() / filename
    
    c = canvas.Canvas(str(filepath), pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Calculate usable width (page width - margins)
    usable_width = width - 0.5 * inch  # 0.25" left + 0.25" right
    
    page_num = 1
    subtitle = f"{len(data)} Tickets"
    if status:
        subtitle += f" - Status: {status}"
    
    y = create_pdf_header(c, "Service Tickets Report", subtitle, max_width=6.5)
    
    # Table headers
    headers = ["ID", "Created", "Status", "Priority", "Customer", "Description", "Hrs to Close"]
    
    # Prepare table data
    table_data = [headers]
    for row in data[:60]:  # Limit to 60 rows
        resolution = row.get("resolution_hours") or ""
        if resolution:
            try:
                resolution = f"{float(resolution):.1f}"
            except:
                pass
        
        table_data.append([
            str(row.get("ticket_id") or ""),
            (row.get("created") or "").strip(),
            (row.get("status") or "").strip(),
            (row.get("priority") or "").strip(),
            (row.get("customer_name") or "").strip(),
            (row.get("title") or "").strip(),
            resolution,
        ])
    
    # Create table
    col_widths = [0.5*inch, 1*inch, 0.8*inch, 0.6*inch, 1.4*inch, 2.2*inch, 0.7*inch]
    
    # Validate table fits usable width
    total_width = sum(col_widths)
    if total_width > usable_width:
        raise ValueError(f"Table width {total_width/inch:.2f}\" exceeds usable width {usable_width/inch:.2f}\"")
    
    table = build_report_table(
        headers,
        table_data[1:],
        col_widths,
        header_font_size=9,
        body_font_size=8,
        align_right_from=6,
        align_center_cols=[0],
    )
    
    # Draw table (use consistent margins)
    table_width, table_height = table.wrapOn(c, usable_width, height)
    table.drawOn(c, 0.25 * inch, y - table_height)
    
    if len(data) > 60:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(0.25 * inch, 0.9 * inch, f"Showing first 60 of {len(data)} tickets")
    
    create_pdf_footer(c, page_num)
    c.save()
    
    with open(filepath, "rb") as f:
        pdf_bytes = f.read()
    
    return str(filepath), pdf_bytes


# ============================================
# OPEN TICKETS SUMMARY PDF
# ============================================

def generate_open_tickets_pdf(data: List[Dict[str, Any]]) -> Tuple[str, bytes]:
    """Generate Open Tickets Summary PDF"""
    
    filename = f"open_tickets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = get_pdf_dir() / filename
    
    c = canvas.Canvas(str(filepath), pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Calculate usable width (page width - margins)
    usable_width = width - 0.5 * inch  # 0.25" left + 0.25" right
    
    page_num = 1
    y = create_pdf_header(c, "Open Tickets Summary", f"{len(data)} Open Tickets", max_width=6.5)
    
    # Table headers
    headers = ["ID", "Priority", "Description", "Customer", "Location", "Days Open"]
    
    # Prepare table data
    table_data = [headers]
    for row in data:
        table_data.append([
            str(row.get("ticket_id") or ""),
            (row.get("priority") or "").strip(),
            (row.get("title") or "").strip(),
            (row.get("customer_name") or "").strip(),
            (row.get("location_address") or "").strip(),
            str(row.get("days_open") or "0"),
        ])
    
    # Create table
    col_widths = [0.5*inch, 0.8*inch, 2.5*inch, 1.6*inch, 1.6*inch, 0.8*inch]
    
    # Validate table fits usable width
    total_width = sum(col_widths)
    if total_width > usable_width:
        raise ValueError(f"Table width {total_width/inch:.2f}\" exceeds usable width {usable_width/inch:.2f}\"")
    
    table = build_report_table(
        headers,
        table_data[1:],
        col_widths,
        header_font_size=9,
        body_font_size=8,
        align_right_from=5,
        align_center_cols=[0],
    )
    
    # Draw table (use consistent margins)
    table_width, table_height = table.wrapOn(c, usable_width, height)
    table.drawOn(c, 0.25 * inch, y - table_height)
    
    create_pdf_footer(c, page_num)
    c.save()
    
    with open(filepath, "rb") as f:
        pdf_bytes = f.read()
    
    return str(filepath), pdf_bytes


# ============================================
# CUSTOMER SUMMARY PDF
# ============================================

def generate_customer_summary_pdf(data: List[Dict[str, Any]]) -> Tuple[str, bytes]:
    """Generate Customer Summary Report PDF"""
    
    filename = f"customer_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = get_pdf_dir() / filename
    
    c = canvas.Canvas(str(filepath), pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Calculate usable width (page width - margins)
    usable_width = width - 0.5 * inch  # 0.25" left + 0.25" right
    
    page_num = 1
    y = create_pdf_header(c, "Customer Summary Report", f"{len(data)} Customers", max_width=6.5)
    
    # Table headers
    headers = ["Company", "Email", "Phone", "Locations", "Equipment", "Open", "Total Tickets"]
    
    # Prepare table data
    table_data = [headers]
    for row in data:
        table_data.append([
            (row.get("customer_name") or "").strip(),
            (row.get("customer_email") or "").strip(),
            (row.get("customer_phone") or "").strip(),
            str(row.get("location_count") or "0"),
            str(row.get("equipment_count") or "0"),
            str(row.get("open_tickets") or "0"),
            str(row.get("total_tickets") or "0"),
        ])
    
    # Create table
    col_widths = [2*inch, 1.8*inch, 1*inch, 0.7*inch, 0.7*inch, 0.6*inch, 0.9*inch]
    
    # Validate table fits usable width
    total_width = sum(col_widths)
    if total_width > usable_width:
        raise ValueError(f"Table width {total_width/inch:.2f}\" exceeds usable width {usable_width/inch:.2f}\"")
    
    table = build_report_table(
        headers,
        table_data[1:],
        col_widths,
        header_font_size=9,
        body_font_size=8,
        align_left_until=2,
        align_right_from=3,
    )
    
    # Draw table (use consistent margins)
    table_width, table_height = table.wrapOn(c, usable_width, height)
    table.drawOn(c, 0.25 * inch, y - table_height)
    
    create_pdf_footer(c, page_num)
    c.save()
    
    with open(filepath, "rb") as f:
        pdf_bytes = f.read()
    
    return str(filepath), pdf_bytes


# ============================================
# LOCATION INVENTORY PDF
# ============================================

def generate_location_inventory_pdf(data: List[Dict[str, Any]]) -> Tuple[str, bytes]:
    """Generate Location Inventory Report PDF"""
    
    filename = f"location_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = get_pdf_dir() / filename
    
    c = canvas.Canvas(str(filepath), pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Calculate usable width (page width - margins)
    usable_width = width - 0.5 * inch  # 0.25" left + 0.25" right
    
    page_num = 1
    y = create_pdf_header(c, "Location Inventory Report", f"{len(data)} Locations", max_width=6.5)
    
    # Table headers
    headers = ["Customer", "Address", "City", "State", "Total Units", "Active", "Alerts"]
    
    # Prepare table data
    table_data = [headers]
    for row in data:
        table_data.append([
            (row.get("customer_name") or "—").strip(),
            (row.get("address1") or "—").strip(),
            (row.get("city") or "—").strip(),
            (row.get("state") or "—").strip(),
            str(row.get("equipment_count") or "0"),
            str(row.get("active_units") or "0"),
            str(row.get("alert_units") or "0"),
        ])
    
    # Create table
    # Optimized widths for landscape (10.5" usable width)
    col_widths = [2.2*inch, 2.8*inch, 1.3*inch, 0.6*inch, 0.9*inch, 0.7*inch, 0.7*inch]
    
    # Validate table fits usable width
    total_width = sum(col_widths)
    if total_width > usable_width:
        raise ValueError(f"Table width {total_width/inch:.2f}\" exceeds usable width {usable_width/inch:.2f}\"")
    
    table = build_report_table(
        headers,
        table_data[1:],
        col_widths,
        header_font_size=8,
        body_font_size=7,
        align_left_until=3,
        align_right_from=4,
    )
    
    # Draw table (use consistent margins)
    table_width, table_height = table.wrapOn(c, usable_width, height)
    table.drawOn(c, 0.25 * inch, y - table_height)
    
    create_pdf_footer(c, page_num)
    c.save()
    
    with open(filepath, "rb") as f:
        pdf_bytes = f.read()
    
    return str(filepath), pdf_bytes


# ============================================
# CURRENT ALERTS PDF
# ============================================

def generate_current_alerts_pdf(data: List[Dict[str, Any]]) -> Tuple[str, bytes]:
    """Generate Current Alerts Report PDF"""
    
    filename = f"current_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = get_pdf_dir() / filename
    
    c = canvas.Canvas(str(filepath), pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Calculate usable width (page width - margins)
    usable_width = width - 0.5 * inch  # 0.25" left + 0.25" right
    
    page_num = 1
    y = create_pdf_header(c, "Current Alerts Report", f"{len(data)} Active Alerts", max_width=6.5)
    
    # Table headers
    headers = ["Status", "Customer", "Location", "Unit", "Make", "Model", "Fault", "Last Reading"]
    
    # Prepare table data
    table_data = [headers]
    for row in data:
        table_data.append([
            (row.get("status") or "").strip(),
            (row.get("customer_name") or "").strip(),
            (row.get("location_address") or "").strip(),
            (row.get("unit_tag") or "").strip(),
            (row.get("make") or "—").strip(),
            (row.get("model") or "—").strip(),
            (row.get("fault_code") or "—").strip(),
            (row.get("last_reading") or "—").strip(),
        ])
    
    # Create table
    col_widths = [0.6*inch, 1.3*inch, 1.4*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.7*inch, 1.1*inch]
    
    # Validate table fits usable width
    total_width = sum(col_widths)
    if total_width > usable_width:
        raise ValueError(f"Table width {total_width/inch:.2f}\" exceeds usable width {usable_width/inch:.2f}\"")
    
    table = build_report_table(
        headers,
        table_data[1:],
        col_widths,
        header_font_size=9,
        body_font_size=8,
        align_left_until=7,
    )
    
    # Draw table (use consistent margins)
    table_width, table_height = table.wrapOn(c, usable_width, height)
    table.drawOn(c, 0.25 * inch, y - table_height)
    
    create_pdf_footer(c, page_num)
    c.save()
    
    with open(filepath, "rb") as f:
        pdf_bytes = f.read()
    
    return str(filepath), pdf_bytes


# ============================================
# HIERARCHICAL COMPANY REPORT PDF
# ============================================

def generate_hierarchical_company_pdf(data: Dict[str, Any]) -> Tuple[str, bytes]:
    """
    Generate Hierarchical Company Report PDF
    Shows Company → Customers → Locations → Equipment structure
    """
    
    filename = f"hierarchical_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = get_pdf_dir() / filename
    
    c = canvas.Canvas(str(filepath), pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Calculate usable dimensions
    usable_width = width - 0.5 * inch  # 0.25" left + 0.25" right
    header_height = 1.6 * inch  # Approximate header size from create_pdf_header
    footer_space = 0.4 * inch  # Space for page number + footer line
    bottom_margin = 0.2 * inch  # Margin below footer
    available_height_per_page = height - header_height - footer_space - bottom_margin
    
    # Build hierarchical table data
    table_data = [["Customer", "Location", "Unit Tag", "Make", "Model", "Serial Number"]]
    
    for customer in data.get("customers", []):
        customer_name = customer.get("company") or f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "Unknown"
        
        for location in customer.get("locations", []):
            loc_parts = []
            if location.get("address1"):
                loc_parts.append(str(location["address1"]).strip())
            if location.get("city"):
                loc_parts.append(str(location["city"]).strip())
            if location.get("state"):
                loc_parts.append(str(location["state"]).strip())
            location_display = ", ".join(filter(None, loc_parts)) or "Location"
            
            equipment = location.get("equipment", [])
            if equipment:
                for unit in equipment[:20]:  # Max 20 units per location
                    unit_tag = (unit.get("unit_tag") or "—").strip()
                    make = (unit.get("make") or "").strip()
                    model = (unit.get("model") or "").strip()
                    serial = (unit.get("serial") or "—").strip()
                    table_data.append([customer_name, location_display, unit_tag, make, model, serial])
                if len(equipment) > 20:
                    table_data.append(["", location_display, f"({len(equipment) - 20} more units)", "", "", ""])
            else:
                table_data.append([customer_name, location_display, "(No equipment)", "", "", ""])
    
    # Build table
    col_widths = [2*inch, 2.2*inch, 1.2*inch, 1*inch, 1*inch, 1.3*inch]
    
    # Validate table fits usable width
    total_width = sum(col_widths)
    if total_width > usable_width:
        raise ValueError(f"Table width {total_width/inch:.2f}\" exceeds usable width {usable_width/inch:.2f}\"")
    
    # Split data into pages - calculate exactly what fits
    rows_per_page = max(5, int(available_height_per_page / (0.2 * inch)))  # Estimate ~0.2" per row
    header_row = table_data[0]
    data_rows = table_data[1:]
    
    page_num = 1
    row_idx = 0
    
    while row_idx < len(data_rows):
        # Draw header
        y = create_pdf_header(c, "Hierarchical Company Report", "Customer → Location → Equipment", max_width=6.5)
        
        # On first page, subtract 2 rows for footer space; on subsequent pages use full rows_per_page
        rows_for_this_page = rows_per_page - 2 if page_num == 1 else rows_per_page
        rows_to_draw = data_rows[row_idx:row_idx + rows_for_this_page]
        
        if rows_to_draw:
            page_table = build_report_table(
                header_row,
                rows_to_draw,
                col_widths,
                header_font_size=9,
                body_font_size=7,
            )
            
            table_w, table_h = page_table.wrapOn(c, usable_width, available_height_per_page)
            page_table.drawOn(c, 0.25 * inch, y - table_h)
            
            # Draw page number at bottom right
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawRightString(width - 0.25 * inch, 0.3 * inch, f"Page {page_num}")
        
        row_idx += rows_for_this_page
        
        # If more rows to draw, create new page
        if row_idx < len(data_rows):
            c.showPage()
            page_num += 1
    
    c.save()
    
    with open(filepath, "rb") as f:
        pdf_bytes = f.read()
    
    return str(filepath), pdf_bytes
