# GCC Monitoring - Security Notes

## Implemented
- Login required for protected pages (require_login -> redirect to /login)
- Password hashing (argon2 via passlib)
- Session stored in NiceGUI app.storage.user

## TODO (before production)
- Move admin email/password to environment variables (.env), no hardcoded secrets
- Use HTTPS (reverse proxy: Caddy or Nginx)
- Add login rate limiting / lockout
- Add roles/permissions per page (admin vs user)
- Add audit log (login, logout, user changes)
'-----------------------------------------------------------------
before production, you will:
1️⃣ Create a .env file
STORAGE_SECRET=super_long_random_string_here
ADMIN_EMAIL=admin@gcchvacr.com
ADMIN_PASSWORD=ChangeThisNow123!

2️⃣ Load it (later)
from dotenv import load_dotenv
load_dotenv()


We will do this later, not now.
