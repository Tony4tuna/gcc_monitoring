# GCC Monitoring System - Production Ready

## Quick Start (Production)

1. **Set environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and set ADMIN_PASSWORD and STORAGE_SECRET
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run:**
   ```bash
   python app.py
   ```

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

## Production Changes

✅ **Security hardened:**
- Requires `ADMIN_PASSWORD` environment variable (no default)
- Requires `STORAGE_SECRET` environment variable
- Test data generator disabled by default
- Configurable host/port via environment

✅ **Environment Variables:**
- `ADMIN_EMAIL` - Admin username (default: admin)
- `ADMIN_PASSWORD` - **REQUIRED** Admin password
- `STORAGE_SECRET` - **REQUIRED** Session encryption key
- `HOST` - Bind address (default: 0.0.0.0)
- `PORT` - Port number (default: 8080)
- `ENABLE_TEST_DATA` - Enable test data generator (default: disabled)

## Development Mode

To run with test data generator (development only):
```bash
export ADMIN_PASSWORD="test123"
export STORAGE_SECRET="dev_secret_key"
export ENABLE_TEST_DATA="1"
python app.py
```

## Features

- Real-time HVAC equipment monitoring
- Health scoring and alert system
- Auto-refresh dashboard (30s interval)
- Role-based access control
- Multi-tenant support (customers, locations, equipment)

## Tech Stack

- **Backend:** NiceGUI 3.5.0, FastAPI, SQLite
- **Frontend:** Quasar (via NiceGUI)
- **Auth:** Argon2 password hashing
- **Database:** SQLite with foreign key constraints

## Documentation

- [Deployment Guide](DEPLOYMENT.md) - Production deployment instructions
- [AI Copilot Instructions](.github/copilot-instructions.md) - Architecture overview
- [Quick Reference](md%20files/QUICK_REF.md) - Developer guide

## License

Proprietary - GCC Company
