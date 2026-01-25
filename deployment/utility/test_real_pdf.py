import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.db import get_conn
from pages.dashboard import generate_service_order_pdf
from datetime import datetime


def test_real_pdf():
    """Generate actual PDF with real data"""
    conn = get_conn()
    
    # Get a real service call with joins
    ticket = conn.execute("""
        SELECT
            sc.ID,
            sc.created,
            sc.status,
            sc.priority,
            sc.title,
            sc.description,
            sc.materials_services,
            sc.labor_description,
            sc.customer_id,
            sc.location_id,
            sc.unit_id,
            c.company AS customer,
            pl.address1 || ' ' || pl.city AS location,
            u.make,
            u.model,
            u.serial,
            u.equipment_type,
            u.refrigerant_type,
            u.voltage,
            u.amperage,
            u.btu_rating,
            u.tonnage,
            u.breaker_size,
            u.inst_date,
            u.warranty_end_date
        FROM ServiceCalls sc
        LEFT JOIN Customers c ON c.ID = sc.customer_id
        LEFT JOIN PropertyLocations pl ON pl.ID = sc.location_id
        LEFT JOIN Units u ON u.unit_id = sc.unit_id
        ORDER BY sc.ID DESC
        LIMIT 1
    """).fetchone()
    
    if not ticket:
        print("No service calls found!")
        conn.close()
        return
    
    ticket = dict(ticket)
    
    # Get company info - try CompanyProfile first, fallback to CompanyInfo
    try:
        company_row = conn.execute("SELECT * FROM CompanyProfile LIMIT 1").fetchone()
        if not company_row:
            company_row = conn.execute("SELECT * FROM CompanyInfo LIMIT 1").fetchone()
        
        if company_row:
            company = dict(company_row)
        else:
            company = {"company": "Test Company", "phone": "(555) 123-4567"}
    except:
        company = {"company": "Test Company", "phone": "(555) 123-4567"}
    
    conn.close()
    
    # Prepare data
    data = {
        "customer": ticket.get('customer', '—'),
        "location": ticket.get('location', '—'),
        "unit_id": ticket.get('unit_id', 0),
        "equipment_type": ticket.get('equipment_type', 'RTU'),
        "make": ticket.get('make', '—'),
        "model": ticket.get('model', '—'),
        "serial": ticket.get('serial', '—'),
        "refrigerant_type": ticket.get('refrigerant_type', '—'),
        "voltage": ticket.get('voltage', '—'),
        "amperage": ticket.get('amperage', '—'),
        "btu_rating": ticket.get('btu_rating', '—'),
        "tonnage": ticket.get('tonnage', '—'),
        "breaker_size": ticket.get('breaker_size', '—'),
        "inst_date": ticket.get('inst_date', '—'),
        "warranty_end_date": ticket.get('warranty_end_date', '—'),
        "status": ticket.get('status', '—'),
        "priority": ticket.get('priority', '—'),
        "title": ticket.get('title', '—'),
        "description": ticket.get('description', '—'),
        "materials_services": ticket.get('materials_services') or "Test materials - Refrigerant R410A, Compressor",
        "labor_description": ticket.get('labor_description') or "Test labor - Diagnosed and replaced faulty compressor",
        "created": ticket.get('created', ''),
    }
    
    health = {"score": 85}
    alerts = {"alerts": ["High discharge pressure", "Low superheat"]}
    
    # Use same ticket number format as production: YYYYMMDD-####
    from datetime import datetime
    ticket_no = f"{datetime.now().strftime('%Y%m%d')}-{ticket.get('ID', 0):04d}"
    
    print(f"\nGenerating PDF: {ticket_no}")
    print(f"Company: {company.get('company_name') or company.get('name') or company.get('company', '—')}")
    print(f"Phone: {company.get('phone', '—')}")
    print(f"Customer: {data['customer']}")
    print(f"Location: {data['location']}")
    print(f"Unit: RTU-{data['unit_id']} - Make: {data['make']} Model: {data['model']} Serial: {data['serial']}")
    print(f"Materials: {data['materials_services'][:50]}...")
    print(f"Labor: {data['labor_description'][:50]}...")
    
    try:
        pdf_path, pdf_bytes = generate_service_order_pdf(ticket_no, data, health, alerts, company)
        print(f"\n✓ PDF generated successfully!")
        print(f"Path: {pdf_path}")
        print(f"Size: {len(pdf_bytes)} bytes")
    except Exception as e:
        print(f"\n✗ PDF generation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_real_pdf()
