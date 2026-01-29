# core/email_settings.py
# Centralized SMTP settings loader for the app.
# Ensures EmailSettings table exists AND required columns exist (including smtp_pass).

from __future__ import annotations

from typing import Dict, Any

from core.db import get_conn


def _table_columns(conn, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {r["name"] for r in rows} if rows else set()


def ensure_email_settings_table() -> None:
    """Create EmailSettings table if missing and ensure required columns exist."""
    conn = get_conn()
    try:
        # Create table if it doesn't exist (includes smtp_pass)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS EmailSettings (
          id INTEGER PRIMARY KEY CHECK (id = 1),
          smtp_host TEXT,
          smtp_port INTEGER DEFAULT 2525,
          use_tls INTEGER DEFAULT 1,
          smtp_user TEXT,
          smtp_pass TEXT,
          smtp_from TEXT,
          use_sendgrid INTEGER DEFAULT 0,
          sendgrid_api_key TEXT
        )
        """)
        conn.commit()

        # If table existed before, make sure all columns exist
        cols = _table_columns(conn, "EmailSettings")
        
        # Ensure record exists first
        conn.execute("INSERT OR IGNORE INTO EmailSettings (id) VALUES (1)")
        
        if "smtp_pass" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN smtp_pass TEXT")
        if "smtp_from" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN smtp_from TEXT")
        if "use_tls" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN use_tls INTEGER DEFAULT 1")
        if "smtp_port" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN smtp_port INTEGER DEFAULT 2525")
        if "smtp_host" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN smtp_host TEXT")
        if "smtp_user" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN smtp_user TEXT")
        if "use_sendgrid" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN use_sendgrid INTEGER DEFAULT 0")
        if "sendgrid_api_key" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN sendgrid_api_key TEXT")

        conn.commit()
    finally:
        conn.close()


def get_email_settings() -> Dict[str, Any]:
    """Returns the single EmailSettings row (id=1)."""
    ensure_email_settings_table()
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM EmailSettings WHERE id=1").fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def update_email_settings(payload: Dict[str, Any]) -> None:
    """Update the EmailSettings row (id=1)."""
    ensure_email_settings_table()
    conn = get_conn()
    try:
        conn.execute("""
        UPDATE EmailSettings
        SET smtp_host=?,
            smtp_port=?,
            use_tls=?,
            smtp_user=?,
            smtp_pass=?,
            smtp_from=?
        WHERE id=1
        """, (
            (payload.get("smtp_host") or "").strip(),
            int(payload.get("smtp_port") or 2525),
            1 if payload.get("use_tls") else 0,
            (payload.get("smtp_user") or "").strip(),
            (payload.get("smtp_pass") or "").strip(),
            (payload.get("smtp_from") or "").strip(),
        ))
        conn.commit()
    finally:
        conn.close()


def send_email(to_email: str, subject: str, body: str, html_body: str = None, pdf_attachment: bytes = None, pdf_filename: str = None, from_email: str = None) -> tuple[bool, str]:
    """
    Send email via configured SMTP settings or SendGrid API.
    Returns (success: bool, message: str)
    
    Args:
        from_email: Optional override for sender address (defaults to smtp_from from settings)
    """
    settings = get_email_settings()
    
    # Check if SendGrid is enabled
    if settings.get("use_sendgrid"):
        return _send_via_sendgrid(to_email, subject, body, html_body, pdf_attachment, pdf_filename, from_email, settings)
    else:
        return _send_via_smtp(to_email, subject, body, html_body, pdf_attachment, pdf_filename, from_email, settings)


def _send_via_sendgrid(to_email: str, subject: str, body: str, html_body: str, pdf_attachment: bytes, pdf_filename: str, from_email: str, settings: dict) -> tuple[bool, str]:
    """Send email via SendGrid API"""
    import base64
    import json
    try:
        import urllib.request
    except ImportError:
        return False, "urllib not available"
    
    api_key = settings.get("sendgrid_api_key")
    sender = from_email if from_email else settings.get("smtp_from")
    
    if not api_key:
        return False, "SendGrid API key not configured"
    if not sender:
        return False, "From email address not provided and not configured in settings"
    if not to_email or "@" not in to_email:
        return False, "Invalid recipient email address"
    
    try:
        # Build SendGrid API payload
        payload = {
            "personalizations": [{
                "to": [{"email": to_email}],
                "subject": subject
            }],
            "from": {"email": sender},
            "content": [
                {"type": "text/plain", "value": body}
            ]
        }
        
        # Add HTML if provided
        if html_body:
            payload["content"].append({"type": "text/html", "value": html_body})
        
        # Add PDF attachment if provided
        if pdf_attachment and pdf_filename:
            payload["attachments"] = [{
                "content": base64.b64encode(pdf_attachment).decode(),
                "filename": pdf_filename,
                "type": "application/pdf",
                "disposition": "attachment"
            }]
        
        # Send request
        req = urllib.request.Request(
            "https://api.sendgrid.com/v3/mail/send",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 202:
                return True, f"Email sent successfully to {to_email} via SendGrid"
            else:
                return False, f"SendGrid API returned status {response.status}"
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        return False, f"SendGrid API error ({e.code}): {error_body}"
    except Exception as e:
        return False, f"SendGrid error: {str(e)}"


def _send_via_smtp(to_email: str, subject: str, body: str, html_body: str, pdf_attachment: bytes, pdf_filename: str, from_email: str, settings: dict) -> tuple[bool, str]:
    """Send email via SMTP"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.application import MIMEApplication
    
    # Use provided from_email or fall back to settings
    sender = from_email if from_email else settings.get("smtp_from")
    
    # Validate settings
    if not all([settings.get("smtp_host"), settings.get("smtp_user"), settings.get("smtp_pass")]):
        return False, "SMTP settings incomplete (missing host, user, or password)"
    
    if not sender:
        return False, "From email address not provided and not configured in settings"
    
    if not to_email or "@" not in to_email:
        return False, "Invalid recipient email address"
    
    try:
        # Create message
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to_email
        
        # Add text/html body
        if html_body:
            body_part = MIMEMultipart("alternative")
            body_part.attach(MIMEText(body, "plain"))
            body_part.attach(MIMEText(html_body, "html"))
            msg.attach(body_part)
        else:
            msg.attach(MIMEText(body, "plain"))
        
        # Add PDF attachment if provided
        if pdf_attachment and pdf_filename:
            pdf_part = MIMEApplication(pdf_attachment, _subtype="pdf")
            pdf_part.add_header("Content-Disposition", f"attachment; filename={pdf_filename}")
            msg.attach(pdf_part)
        
        # Connect and send
        port = int(settings.get("smtp_port", 587))
        use_tls = settings.get("use_tls", 1)
        
        if use_tls:
            smtp = smtplib.SMTP(settings.get("smtp_host"), port, timeout=10)
            smtp.starttls()
        else:
            smtp = smtplib.SMTP_SSL(settings.get("smtp_host"), port, timeout=10)
        
        smtp.login(settings.get("smtp_user"), settings.get("smtp_pass"))
        smtp.send_message(msg)
        smtp.quit()
        
        return True, f"Email sent successfully to {to_email}"
    
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed - check username/password"
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        return False, f"Email error: {str(e)}"
