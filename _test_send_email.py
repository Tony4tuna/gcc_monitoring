#!/usr/bin/env python3
"""Test sending email for ticket #33"""

from core.tickets_repo import send_ticket_email

print("Attempting to send email for ticket #33...")
print("Recipient: work-orders@gcchvacr.com (admin)")
print()

try:
    success, msg = send_ticket_email(
        call_id=33,
        to_email="work-orders@gcchvacr.com"
    )
    
    if success:
        print(f"✓ SUCCESS: {msg}")
    else:
        print(f"✗ FAILED: {msg}")
        
except Exception as e:
    print(f"✗ EXCEPTION: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
