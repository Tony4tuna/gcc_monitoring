import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.db import get_conn
from datetime import datetime


def test_pdf_generation():
    """Test PDF generation with sample ticket data"""
    conn = get_conn()
    
    # Get a real service call
    ticket = conn.execute("""
        SELECT sc.*, 
               c.company as customer,
               pl.address1 || ' ' || pl.city as location
        FROM ServiceCalls sc
        LEFT JOIN Customers c ON sc.customer_id = c.ID
        LEFT JOIN PropertyLocations pl ON sc.location_id = pl.ID
        ORDER BY sc.ID DESC
        LIMIT 1
    """).fetchone()
    
    if not ticket:
        print("No service calls found in database!")
        conn.close()
        return
    
    ticket = dict(ticket)
    print("\n=== TICKET DATA ===")
    for k, v in ticket.items():
        print(f"{k}: {v}")
    
    # Get company info
    company_row = conn.execute("SELECT * FROM CompanyProfile LIMIT 1").fetchone()
    if company_row is None:
        company_row = conn.execute("SELECT * FROM CompanyInfo LIMIT 1").fetchone()
    
    print("\n=== COMPANY DATA ===")
    if company_row:
        company_row = dict(company_row)
        for k, v in company_row.items():
            if v:
                print(f"{k}: {v}")
    else:
        print("No company profile found!")
    
    conn.close()
    
    print("\n=== PDF WOULD SHOW ===")
    print(f"Company: {company_row.get('company_name') or company_row.get('name') or 'N/A' if company_row else 'N/A'}")
    print(f"Phone: {company_row.get('phone') or 'N/A' if company_row else 'N/A'}")
    print(f"Customer: {ticket.get('customer') or 'N/A'}")
    print(f"Location: {ticket.get('location') or 'N/A'}")
    print(f"Status: {ticket.get('status')}")
    print(f"Priority: {ticket.get('priority')}")
    print(f"Materials: {ticket.get('materials_services') or 'N/A'}")
    print(f"Labor: {ticket.get('labor_description') or 'N/A'}")


if __name__ == "__main__":
    test_pdf_generation()
