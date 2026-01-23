import os
try:
    from dotenv import load_dotenv
    load_dotenv()  # loads .env into environment variables
except Exception:
    pass
from nicegui import ui
from fastapi import Request, Response
import subprocess
import threading
from pathlib import Path

from core.auth import current_user, ensure_admin, is_admin, logout

from pages import login as login_page
from pages import dashboard
from pages import clients
from pages import locations
from pages import equipment
from pages import admin
from pages import client_home
from pages import profile
from pages import settings
from pages import tickets
import asyncio
import logging

# Silence the annoying Windows connection lost warning
logging.getLogger("asyncio").setLevel(logging.WARNING)
# Or even stricter:
# logging.getLogger("proactor").setLevel(logging.ERROR)

#-----------------------------*/
###import warnings
###warnings.filterwarnings(
###    "ignore",
###    message="Exception in callback _ProactorBasePipeTransport._call_connection_lost",
###    category=RuntimeWarning
###)
#------------------------------/*



@ui.page("/login")
def login():
    login_page.page()

# API endpoint for logout on browser close
from nicegui import app as nicegui_app

@nicegui_app.post("/api/logout-on-close")
async def logout_on_close():
    """Handle logout when browser/tab closes"""
    logout()
    return {"status": "logged_out"}

#----------------------------------------------
#Here should go to dashboard for administrator 
# or dashboard of clients




#-----------------------------------------------
@ui.page("/")
def home():
    if is_admin():
        dashboard.page()
    else:
        client_home.page()
#----------------------------------------------

@ui.page("/clients")
def clients_route():
    clients.page()

@ui.page("/locations")
def locations_route():
    locations.page()

@ui.page("/equipment")
def equipment_route():
    equipment.page()

# Admin page is now folded into Settings; keep route for back-compat but redirect.
@ui.page("/admin")
def admin_route():
    ui.navigate.to("/settings")

@ui.page("/profile")
def profile_route():
    profile.page()

@ui.page("/settings")
def settings_route():
    settings.page()

if __name__ in {"__main__", "__mp_main__"}:
    # Disable test data generator in production
    # Set ENABLE_TEST_DATA=1 environment variable to enable for development
    if os.getenv("ENABLE_TEST_DATA") == "1":
        def start_test_data_generator():
            """Start test data generator in background thread"""
            try:
                generator_path = Path(__file__).parent / "test_data_generator.py"
                if generator_path.exists():
                    # Run in background subprocess
                    process = subprocess.Popen(
                        [Path(__file__).parent / "venv" / "Scripts" / "python.exe", str(generator_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                    )
                    logging.info(f"Test data generator started (PID: {process.pid})")
            except Exception as e:
                logging.warning(f"Could not start test data generator: {e}")
        
        threading.Thread(target=start_test_data_generator, daemon=True).start()
    
    # Use environment variables for production credentials
    admin_email = os.getenv("ADMIN_EMAIL", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if not admin_password:
        raise ValueError("ADMIN_PASSWORD environment variable must be set for production")
    
    ensure_admin(admin_email, admin_password)

    ui.add_head_html('''
        <style>
            body { background: var(--bg) !important; }
            :root { --bg: #07150f; --card: #0b231a; }
        </style>
    ''', shared=True)
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    storage_secret = os.getenv("STORAGE_SECRET")
    
    if not storage_secret:
        raise ValueError("STORAGE_SECRET environment variable must be set for production")
     
    ui.run(
        title="GCC Monitoring System",
        host=host,
        port=port,
        storage_secret=storage_secret,
        reload=False,
        dark=True,
    )

