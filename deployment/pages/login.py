from nicegui import ui
from core.auth import login, logout, current_user

def page():
    # Automatic logout for security when accessing login page
    if current_user():
        logout()
    
    ui.page_title("Login")

    with ui.card().classes("w-full max-w-md mx-auto mt-16 p-6"):
        ui.label("GCC Monitoring System").classes("text-xl font-bold")

        email = ui.input("Email").props("autocomplete=email")
        password = ui.input("Password", password=True).props("autocomplete=current-password")
        message = ui.label("").classes("text-sm text-red-600")

        def do_login():
            ok = login(email.value, password.value)
            if ok:
                ui.navigate.to("/")
            else:
                message.text = "Invalid email or password"
        ui.button("Login", on_click=do_login).classes("w-full max-w-xs mx-auto mt-2").props('color=green-10')
      