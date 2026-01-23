# pages/profile.py
# My Profile page - allows users to edit their customer information

from nicegui import ui
from core.auth import current_user, require_login
from ui.layout import layout
from core.customers_repo import get_customer, update_customer


def page():
    if not require_login():
        return

    user = current_user()
    hierarchy = user.get("hierarchy", 5)
    customer_id = user.get("customer_id")

    # Pass hierarchy to layout for proper sidebar
    with layout("My Profile", hierarchy=hierarchy):

        if not customer_id:
            ui.label("Error: No customer assigned to your account").classes("text-red-500 text-xl")
            ui.label("Please contact your administrator.").classes("text-sm gcc-muted")
            return

        # Fetch customer details
        customer = get_customer(customer_id)
        if not customer:
            ui.label("Customer not found").classes("text-red-500 text-xl")
            return

        # Profile header
        customer_name = customer.get("company") or f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or f"Customer {customer_id}"
        with ui.card().classes("gcc-card p-4 mb-4"):
            ui.label("My Profile").classes("text-2xl font-bold")
            ui.label(f"Editing information for: {customer_name}").classes("text-sm gcc-muted")

        # Profile editing form (ALL customer fields)
        with ui.card().classes("gcc-card p-5"):
            ui.label("Company Information").classes("text-lg font-bold mb-3")
            
            company_input = ui.input("Company Name", value=customer.get("company", "")).classes("w-full")
            
            with ui.row().classes("w-full gap-4"):
                first_name_input = ui.input("First Name", value=customer.get("first_name", "")).classes("flex-1")
                last_name_input = ui.input("Last Name", value=customer.get("last_name", "")).classes("flex-1")
            
            ui.separator().classes("my-4")
            ui.label("Contact Information").classes("text-lg font-bold mb-3")
            
            email_input = ui.input("Email", value=customer.get("email", "")).classes("w-full")
            
            with ui.row().classes("w-full gap-4"):
                phone1_input = ui.input("Phone 1", value=customer.get("phone1", "")).classes("flex-1")
                phone2_input = ui.input("Phone 2", value=customer.get("phone2", "")).classes("flex-1")
            
            with ui.row().classes("w-full gap-4"):
                mobile_input = ui.input("Mobile", value=customer.get("mobile", "")).classes("flex-1")
                fax_input = ui.input("Fax", value=customer.get("fax", "")).classes("flex-1")
            
            with ui.row().classes("w-full gap-4"):
                extension1_input = ui.input("Extension 1", value=customer.get("extension1", "")).classes("flex-1")
                extension2_input = ui.input("Extension 2", value=customer.get("extension2", "")).classes("flex-1")
            
            ui.separator().classes("my-4")
            ui.label("Address").classes("text-lg font-bold mb-3")
            
            address1_input = ui.input("Address Line 1", value=customer.get("address1", "")).classes("w-full")
            address2_input = ui.input("Address Line 2", value=customer.get("address2", "")).classes("w-full")
            
            with ui.row().classes("w-full gap-4"):
                city_input = ui.input("City", value=customer.get("city", "")).classes("flex-1")
                state_input = ui.input("State", value=customer.get("state", "")).classes("w-32")
                zip_input = ui.input("ZIP", value=customer.get("zip", "")).classes("w-40")
            
            ui.separator().classes("my-4")
            ui.label("Additional Information").classes("text-lg font-bold mb-3")
            
            website_input = ui.input("Website", value=customer.get("website", "")).classes("w-full")
            idstring_input = ui.input("ID String", value=customer.get("idstring", "")).classes("w-full")
            
            with ui.row().classes("w-full gap-4"):
                csr_input = ui.input("CSR", value=customer.get("csr", "")).classes("flex-1")
                referral_input = ui.input("Referral", value=customer.get("referral", "")).classes("flex-1")
            
            credit_status_input = ui.input("Credit Status", value=customer.get("credit_status", "")).classes("w-full")
            
            flag_and_lock_checkbox = ui.checkbox("Flag and Lock", value=bool(customer.get("flag_and_lock", 0))).classes("mt-2")
            
            ui.separator().classes("my-4")
            ui.label("Notes").classes("text-lg font-bold mb-3")
            
            notes_input = ui.textarea("Notes", value=customer.get("notes", "")).classes("w-full").props("rows=3")
            extended_notes_input = ui.textarea("Extended Notes", value=customer.get("extended_notes", "")).classes("w-full").props("rows=5")
            
            # Save button
            def save_profile():
                try:
                    update_data = {
                        "company": company_input.value,
                        "first_name": first_name_input.value,
                        "last_name": last_name_input.value,
                        "email": email_input.value,
                        "phone1": phone1_input.value,
                        "phone2": phone2_input.value,
                        "mobile": mobile_input.value,
                        "fax": fax_input.value,
                        "extension1": extension1_input.value,
                        "extension2": extension2_input.value,
                        "address1": address1_input.value,
                        "address2": address2_input.value,
                        "city": city_input.value,
                        "state": state_input.value,
                        "zip": zip_input.value,
                        "website": website_input.value,
                        "idstring": idstring_input.value,
                        "csr": csr_input.value,
                        "referral": referral_input.value,
                        "credit_status": credit_status_input.value,
                        "flag_and_lock": flag_and_lock_checkbox.value,
                        "notes": notes_input.value,
                        "extended_notes": extended_notes_input.value,
                    }
                    update_customer(customer_id, update_data)
                    ui.notify("Profile updated successfully", type="positive")
                except Exception as e:
                    ui.notify(f"Error updating profile: {e}", type="negative")
            
            with ui.row().classes("w-full justify-end gap-3 mt-5"):
                ui.button("Cancel", on_click=lambda: ui.navigate.to("/")).props("flat")
                ui.button("Save Profile", on_click=save_profile).props("color=positive")
