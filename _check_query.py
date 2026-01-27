from core.tickets_repo import list_service_calls

calls = list_service_calls(limit=3)
print('Testing customer_name field in list_service_calls:')
print('-' * 80)
for call in calls:
    print(f"Ticket #{call.get('ID')}")
    print(f"  customer_id: {call.get('customer_id')}")
    print(f"  customer_name (from query): {call.get('customer_name')}")
    print(f"  customer (field): {call.get('customer')}")
    print()
