# pages/dashboard.py
# Dashboard + Action dialog includes Service Order buttons:
# - Client (hierarchy=4): Email Service Order ONLY (blocked if same unit within last 24h)
# - Tech/Admin (1/2/3/5): Email to Client + Print (Download PDF)
# Stores orders in DB using ServiceCalls + Reports
# Shows role debug line inside dialog so you can confirm the update is live.

from __future__ import annotations

from nicegui import ui
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import os
import json
import smtplib
from email.message import EmailMessage

from core.auth import require_login, current_user
from core.db import get_conn
from core.equipment_analysis import calculate_equipment_health_score
from core.alert_system import evaluate_all_alerts
from ui.layout import layout
from core.stats import get_summary_counts


# ----------------------------
# Helpers
# ----------------------------

def _now() -> datetime:
    return datetime.now()

def _as_bool(v: Any, default: bool = False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    return default

def _trim(s: str, max_len: int = 80) -> str:
    s = (s or "").strip()
    return s if len(s) <= max_len else (s[: max_len - 1].rstrip() + "…")

def format_time_ago(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts)
        diff = _now() - dt
        s = diff.total_seconds()
        if s < 60:
            return f"{int(s)}s ago"
        if s < 3600:
            return f"{int(s/60)}m ago"
        if s < 86400:
            return f"{int(s/3600)}h ago"
        return f"{int(s/86400)}d ago"
    except Exception:
        return "—"

def _get_customer_filter_for_user() -> Optional[int]:
    user = current_user() or {}
    hierarchy = int(user.get("hierarchy", 5) or 5)
    if hierarchy == 4:
        return user.get("customer_id")
    return None

def _show_error_dialog(title: str, err: Exception | str):
    text = str(err)
    with ui.dialog(value=True) as d:
        with ui.card().classes("gcc-card p-4 w-full max-w-3xl"):
            ui.label(title).classes("text-lg font-bold text-red-400")
            ui.separator().classes("my-2")
            ui.textarea(value=text).props("readonly autogrow").classes("w-full")
            with ui.row().classes("justify-end mt-2"):
                ui.button("Close", on_click=d.close).props("color=red")

def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


# ----------------------------
# 24h Client lockout
# ----------------------------

def client_can_open_service_call(unit_id: int, customer_id: int) -> tuple[bool, str]:
    """
    Client restriction: cannot open a new ServiceCall for same unit within last 24 hours.
    Returns (ok, message).
    """
    conn = get_conn()
    try:
        row = conn.execute("""
            SELECT ID, created, status, title
            FROM ServiceCalls
            WHERE customer_id = ?
              AND unit_id = ?
              AND created >= datetime('now', '-24 hours')
            ORDER BY created DESC
            LIMIT 1
        """, (int(customer_id), int(unit_id))).fetchone()

        if not row:
            return True, ""

        sc_id = row["ID"]
        created = row["created"]
        status = (row["status"] or "").strip() or "—"
        return False, f"Already submitted in the last 24 hours for this unit. Ticket ID {sc_id} (Created: {created}, Status: {status})."

    finally:
        conn.close()


# ----------------------------
# DB Queries (filtered)
# ----------------------------

def get_unit_details(unit_id: int, customer_id: Optional[int] = None) -> Optional[dict]:
    conn = get_conn()
    try:
        cursor = conn.cursor()

        extra = ""
        params = [int(unit_id)]
        if customer_id is not None:
            extra = " AND c.ID = ?"
            params.append(int(customer_id))

        cursor.execute(f"""
            SELECT ur.*,
                   u.make, u.model, u.serial, u.location_id,
                   pl.ID as location_id_real,
                   pl.address1 as location,
                   pl.city as location_city,
                   pl.state as location_state,
                   pl.zip as location_zip,
                   c.company as customer,
                   c.email as customer_email,
                   c.phone1 as customer_phone,
                   c.ID as customer_id
            FROM UnitReadings ur
            JOIN Units u ON ur.unit_id = u.unit_id
            JOIN PropertyLocations pl ON u.location_id = pl.ID
            JOIN Customers c ON pl.customer_id = c.ID
            WHERE ur.unit_id = ? {extra}
            ORDER BY ur.reading_id DESC
            LIMIT 1
        """, tuple(params))

        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_unit_stats(customer_id: Optional[int] = None) -> dict:
    conn = get_conn()
    try:
        cursor = conn.cursor()

        filters = [
            """
            ur.reading_id IN (
                SELECT MAX(reading_id) FROM UnitReadings GROUP BY unit_id
            )
            """
        ]
        params: list = []

        if customer_id is not None:
            filters.append("c.ID = ?")
            params.append(int(customer_id))

        where_clause = "WHERE " + " AND ".join(filters)

        cursor.execute(f"""
            SELECT
                u.unit_id,
                u.make,
                u.model,
                ur.mode,
                ur.supply_temp,
                ur.return_temp,
                ur.delta_t,
                ur.discharge_psi,
                ur.suction_psi,
                ur.superheat,
                ur.subcooling,
                ur.fault_code,
                ur.unit_status,
                ur.ts,
                ur.v_1,
                ur.v_2,
                ur.v_3,
                ur.compressor_amps,
                pl.ID as location_id,
                pl.address1 as location,
                c.company as customer,
                c.email as customer_email,
                c.ID as customer_id
            FROM UnitReadings ur
            JOIN Units u ON ur.unit_id = u.unit_id
            JOIN PropertyLocations pl ON u.location_id = pl.ID
            JOIN Customers c ON pl.customer_id = c.ID
            {where_clause}
            ORDER BY u.unit_id
        """, tuple(params))

        units = cursor.fetchall()

        online_count = 0
        warning_count = 0
        fault_count = 0
        temps: list[float] = []
        alerts_count = 0
        health_data: dict[int, dict] = {}

        for row in units:
            reading = dict(row)

            health = calculate_equipment_health_score(reading)
            unit_alerts = evaluate_all_alerts(reading)
            alerts_count += int(unit_alerts.get("count", 0) or 0)

            uid = int(row["unit_id"])
            health_data[uid] = {
                "score": health.get("score", 0),
                "status": health.get("status", "Unknown"),
                "issues": health.get("issues", []),
            }

            score = int(health_data[uid]["score"] or 0)
            if score >= 80:
                online_count += 1
            elif score >= 60:
                warning_count += 1
            else:
                fault_count += 1

            temps.append(float(row["supply_temp"]) if row["supply_temp"] else 0.0)

        avg_temp = int(sum(temps) / len(temps)) if temps else 0

        return {
            "units": units,
            "online_count": online_count,
            "warning_count": warning_count,
            "fault_count": fault_count,
            "avg_temp": avg_temp,
            "health_data": health_data,
            "alerts_count": alerts_count,
        }
    finally:
        conn.close()


# ----------------------------
# Company + Email Settings
# ----------------------------

def get_company_info() -> dict:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM CompanyInfo ORDER BY ID LIMIT 1").fetchone()
        return dict(row) if row else {}
    except Exception:
        return {}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_email_settings() -> dict:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM EmailSettings ORDER BY id LIMIT 1").fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


# ----------------------------
# ServiceCalls + Reports storage
# ----------------------------

def _generate_ticket_no(service_call_id: int) -> str:
    return f"{_now().strftime('%Y%m%d')}-{service_call_id:04d}"

def _build_location_text(data: dict) -> str:
    parts = []
    if data.get("location"):
        parts.append(str(data.get("location")))
    c = (data.get("location_city") or "").strip()
    s = (data.get("location_state") or "").strip()
    z = (data.get("location_zip") or "").strip()
    cs = ", ".join([p for p in [c, s] if p])
    if cs:
        if z:
            cs = f"{cs} {z}"
        parts.append(cs)
    return ", ".join([p for p in parts if p]).strip() or "—"

def _compose_autodesc(data: dict, alerts: dict) -> str:
    supply = data.get("supply_temp") or "—"
    ret = data.get("return_temp") or "—"
    dt = data.get("delta_t") or "—"
    discharge = data.get("discharge_psi") or "—"
    suction = data.get("suction_psi") or "—"
    superheat = data.get("superheat") or "—"
    subcool = data.get("subcooling") or "—"
    amps = data.get("compressor_amps") or "—"
    v1 = data.get("v_1") or "—"
    v2 = data.get("v_2") or "—"
    v3 = data.get("v_3") or "—"
    primary_issue = data.get("fault_code") or "None"

    lines = [
        f"Primary Issue: {primary_issue}",
        "Snapshot:",
        f"Supply: {supply} F   Return: {ret} F   ∆T: {dt} F",
        f"Discharge: {discharge} PSI   Suction: {suction} PSI",
        f"Superheat: {superheat} F   Subcool: {subcool} F",
        f"Amps: {amps} A   V1/V2/V3: {v1}/{v2}/{v3}",
        "",
        "Top Alerts:",
    ]

    all_alerts = alerts.get("all") or []
    if not all_alerts:
        lines.append("—")
    else:
        for a in all_alerts[:6]:
            sev = str(a.get("severity") or "warning").upper()
            code = _trim(str(a.get("code") or "—"), 24)
            msg = _trim(str(a.get("message") or "—"), 70)
            lines.append(f"[{sev}] {code}: {msg}")

    return "\n".join(lines)


# ----------------------------
# PDF generation (ReportLab)
# ----------------------------

def _require_reportlab():
    try:
        import reportlab  # noqa
    except Exception as e:
        raise RuntimeError(f"ReportLab not installed. Run: pip install reportlab (error: {e})")

def generate_service_order_pdf(ticket_no: str, data: dict, health: dict, alerts: dict, company: dict,
                               out_dir: str = "reports/service_orders") -> Tuple[str, bytes]:
    _require_reportlab()

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    os.makedirs(out_dir, exist_ok=True)
    unit_id = int(data.get("unit_id") or 0)
    unit_name = f"RTU-{unit_id}"
    filename = f"ServiceOrder_{ticket_no}_{unit_name}.pdf"
    pdf_path = os.path.join(out_dir, filename)

    c = canvas.Canvas(pdf_path, pagesize=letter)
    w, h = letter
    left = 40
    right = w - 40
    y = h - 40

    def text(x, y, s, size=10, bold=False):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(x, y, s)

    # Company header
    comp_name = company.get("company") or company.get("name") or "GCC Technology"
    text(left, y, comp_name, 14, True); y -= 16
    for line in [
        company.get("address1") or "",
        company.get("address2") or "",
        " ".join([p for p in [(company.get("city") or "").strip(),
                              (company.get("state") or "").strip(),
                              (company.get("zip") or "").strip()] if p]).strip()
    ]:
        if line.strip():
            text(left, y, line.strip(), 10); y -= 12

    contact_line = " | ".join([p for p in [(company.get("phone") or "").strip(),
                                          (company.get("email") or "").strip(),
                                          (company.get("website") or "").strip()] if p]).strip()
    if contact_line:
        text(left, y, contact_line, 9); y -= 14

    c.line(left, y, right, y); y -= 18
    text(left, y, "HVAC Service Order Invoice", 12, True)
    dt = _now()
    text(right - 260, y, f"Ticket #: {ticket_no}   Date: {dt.date()}   Time: {dt.strftime('%H:%M:%S')}", 9)
    y -= 14
    c.line(left, y, right, y); y -= 18

    mid = (left + right) / 2

    # Left column: customer/unit
    lx = left
    ly = y
    text(lx, ly, "CONTACT INFORMATION", 10, True); ly -= 12
    text(lx, ly, f"Customer: {data.get('customer','—')}", 9); ly -= 11
    text(lx, ly, f"Location: {_build_location_text(data)}", 9); ly -= 11
    text(lx, ly, f"Phone: {data.get('customer_phone') or '—'}", 9); ly -= 11
    text(lx, ly, f"Email: {data.get('customer_email') or '—'}", 9); ly -= 14

    text(lx, ly, "UNIT INFORMATION", 10, True); ly -= 12
    text(lx, ly, f"Unit: RTU-{unit_id}", 9); ly -= 11
    text(lx, ly, f"Make/Model: {data.get('make','—')} {data.get('model','—')}", 9); ly -= 11
    text(lx, ly, f"Serial #: {data.get('serial','—')}", 9); ly -= 11
    score = int(health.get("score", 0) or 0)
    text(lx, ly, f"Mode: {data.get('mode','—')}   Health: {score}% ({health.get('status','Unknown')})", 9); ly -= 11
    text(lx, ly, f"Fault Code: {data.get('fault_code') or 'None'}", 9); ly -= 14

    # Right column: snapshot/alerts
    rx = mid + 18
    ry = y
    text(rx, ry, "DESCRIPTION (AUTO)", 10, True); ry -= 12
    c.setFont("Helvetica", 8.7)
    for line in _compose_autodesc(data, alerts).splitlines()[:20]:
        c.drawString(rx, ry, line)
        ry -= 10

    # Divider
    c.line(mid, y + 10, mid, min(ly, ry) - 20)

    # Bottom fill sections
    y2 = min(ly, ry) - 25
    c.line(left, y2, right, y2); y2 -= 14

    text(left, y2, "MATERIALS & SERVICES (TECH TO FILL)", 10, True); y2 -= 12
    c.rect(left, y2 - 48, right - left, 52, stroke=1, fill=0)
    y2 -= 70

    text(left, y2, "LABOR DESCRIPTION (TECH TO FILL)", 10, True); y2 -= 12
    c.rect(left, y2 - 48, right - left, 52, stroke=1, fill=0)
    y2 -= 70

    text(left, y2, "Customer Signature: ____________________________   Date: ____________", 9)

    c.showPage()
    c.save()

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    if not pdf_bytes or len(pdf_bytes) < 500:
        raise RuntimeError(f"PDF generation failed (too small): {pdf_path} ({len(pdf_bytes)} bytes)")

    return pdf_path, pdf_bytes


# ----------------------------
# Email sending
# ----------------------------

def send_service_order_email(subject: str, body: str, recipients: List[str], pdf_bytes: bytes, pdf_filename: str) -> Tuple[bool, str]:
    es = get_email_settings()
    smtp_host = (es.get("smtp_host") or "").strip()
    smtp_port = _safe_int(es.get("smtp_port") or 587, 587)
    use_tls = _as_bool(es.get("use_tls"), default=True)
    smtp_user = (es.get("smtp_user") or "").strip()
    smtp_pass = (es.get("smtp_pass") or "").strip()
    smtp_from = (es.get("smtp_from") or "").strip() or smtp_user

    if not smtp_host or not smtp_user or not smtp_pass or not smtp_from:
        return False, "EmailSettings incomplete (smtp_host/smtp_user/smtp_pass/smtp_from)."

    recips = [r.strip() for r in recipients if (r or "").strip()]
    recips = list(dict.fromkeys(recips))
    if not recips:
        return False, "No recipients available (client email or company email missing)."

    msg = EmailMessage()
    msg["From"] = smtp_from
    msg["To"] = ", ".join(recips)
    msg["Subject"] = subject
    msg.set_content(body)

    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=pdf_filename)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=25) as s:
            s.ehlo()
            if use_tls:
                s.starttls()
                s.ehlo()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        return True, f"Email sent to: {', '.join(recips)}"
    except Exception as e:
        return False, f"Email failed: {e}"


# ----------------------------
# Dashboard UI
# ----------------------------

def render_dashboard(customer_id: Optional[int] = None):
    stats = get_unit_stats(customer_id=customer_id)
    summary = get_summary_counts()

    with ui.grid(columns=4).classes("gap-2 mb-2"):
        with ui.card().classes("text-center p-3 gcc-card"):
            ui.label("Clients").classes("text-xs").style("color: var(--muted)")
            clients_value = ui.label(str(summary.get("clients", 0))).classes("text-xl font-bold").style("color: var(--accent)")
        with ui.card().classes("text-center p-3 gcc-card"):
            ui.label("Locations").classes("text-xs").style("color: var(--muted)")
            locations_value = ui.label(str(summary.get("locations", 0))).classes("text-xl font-bold").style("color: var(--accent)")
        with ui.card().classes("text-center p-3 gcc-card"):
            ui.label("Equipment").classes("text-xs").style("color: var(--muted)")
            equipment_value = ui.label(str(summary.get("equipment", 0))).classes("text-xl font-bold").style("color: var(--accent)")
        with ui.card().classes("text-center p-3 gcc-card"):
            ui.label("Alerts (latest)").classes("text-xs").style("color: var(--muted)")
            alerts_value = ui.label(str(stats.get("alerts_count", 0))).classes("text-xl font-bold text-yellow-400")

    with ui.grid(columns=4).classes("gap-2 mb-2"):
        with ui.card().classes("text-center p-3 gcc-card"):
            ui.label("Online").classes("text-xs").style("color: var(--muted)")
            online_value = ui.label(f"{stats['online_count']}/{len(stats['units'])}").classes("text-xl font-bold").style("color: var(--accent)")
        with ui.card().classes("text-center p-3 gcc-card"):
            ui.label("Warnings").classes("text-xs").style("color: var(--muted)")
            warnings_value = ui.label(stats["warning_count"]).classes("text-xl font-bold text-orange-400")
        with ui.card().classes("text-center p-3 gcc-card"):
            ui.label("Alarms").classes("text-xs").style("color: var(--muted)")
            alarms_value = ui.label(stats["fault_count"]).classes("text-xl font-bold text-red-500")
        with ui.card().classes("text-center p-3 gcc-card"):
            ui.label("Avg Supply").classes("text-xs").style("color: var(--muted)")
            avg_value = ui.label(f"{stats['avg_temp']} °F").classes("text-xl font-bold text-blue-400")

    columns = [
        {"name": "unit", "label": "Unit", "field": "unit", "align": "left", "sortable": True},
        {"name": "model", "label": "Make/Model", "field": "model", "align": "left", "sortable": True},
        {"name": "location", "label": "Location", "field": "location", "align": "left", "sortable": True},
        {"name": "customer", "label": "Customer", "field": "customer", "align": "left", "sortable": True},
        {"name": "mode", "label": "Mode", "field": "mode", "align": "center", "sortable": True},
        {"name": "health", "label": "Health", "field": "health", "align": "center", "sortable": True},
        {"name": "temp", "label": "Supply Temp", "field": "temp", "align": "center", "sortable": True},
        {"name": "fault", "label": "Fault", "field": "fault", "align": "center", "sortable": True},
        {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
    ]

    rows = []
    for row in stats["units"]:
        d = dict(row)
        uid = int(d["unit_id"])
        health = stats["health_data"].get(uid, {"score": 0, "status": "Unknown"})
        score = int(health.get("score", 0) or 0)
        rows.append({
            "unit": f"RTU-{uid}",
            "model": f"{d.get('make','—')} {d.get('model','—')}",
            "location": d.get("location", "—"),
            "customer": d.get("customer", "—"),
            "mode": d.get("mode", "—"),
            "health": f"{score}% ({health.get('status','Unknown')})",
            "temp": f"{d.get('supply_temp','—')} °F",
            "fault": d.get("fault_code", "—"),
            "actions": uid,
            "_health_score": score,
            "_fault": d.get("fault_code"),
        })

    table = ui.table(
        columns=columns,
        rows=rows,
        row_key="unit",
        pagination={"rowsPerPage": 10, "sortBy": "unit", "descending": False},
    ).classes("w-full gcc-card rounded-lg overflow-hidden")
    table.props("dense bordered")

    table.add_slot("body-cell-actions", """
        <q-td :props="props">
            <q-btn flat dense icon="info" color="green" size="sm" @click="$parent.$emit('details', props.row.actions)" />
        </q-td>
    """)

    table.on("details", lambda e: show_unit_details(e.args, customer_id))


def show_unit_details(unit_id: int, customer_id: Optional[int] = None):
    data = get_unit_details(unit_id, customer_id=customer_id)
    if not data:
        ui.notify("No data / Access denied", type="negative")
        return

    user = current_user() or {}
    hierarchy = int(user.get("hierarchy", 5) or 5)

    health = calculate_equipment_health_score(data)
    alerts = evaluate_all_alerts(data)

    company = get_company_info()
    company_service = (company.get("service_email") or company.get("email") or "").strip()
    company_owner = (company.get("owner_email") or "").strip()
    client_email = (data.get("customer_email") or "").strip()

    unit_id_real = int(data.get("unit_id") or unit_id)
    unit_name = f"RTU-{unit_id_real}"
    location_text = _build_location_text(data)

    with ui.dialog(value=True) as dlg:
        with ui.card().classes("w-full max-w-4xl gcc-card p-4"):

            ui.label(f"{unit_name} – {data.get('make','—')} {data.get('model','—')}").classes("text-base font-bold")
            ui.label(f"ROLE DEBUG: hierarchy={hierarchy} (client=4, tech=3, admin=2, master=1)").classes("text-xs text-yellow-400")
            ui.separator().classes("my-2")

            with ui.row().classes("justify-between items-center"):
                ui.label(f"Customer: {data.get('customer','—')}").classes("text-sm font-semibold")
                ui.label(f"Location: {location_text}").classes("text-sm font-semibold")

            if alerts.get("all"):
                ui.separator().classes("my-2")
                ui.label("Top Alerts").classes("text-sm font-bold")
                for a in (alerts.get("all") or [])[:4]:
                    sev = str(a.get("severity") or "warning").upper()
                    ui.label(f"[{sev}] {_trim(str(a.get('code','—')), 22)}: {_trim(str(a.get('message','—')), 80)}").classes("text-xs")

            ui.separator().classes("my-3")
            ui.label("Service Order").classes("text-sm font-bold")

            def _build_pdf_store_get_ticket() -> Tuple[str, bytes, str]:
                try:
                    conn = get_conn()
                    try:
                        cur = conn.cursor()
                        cust_id = _safe_int(data.get("customer_id"), 0)
                        loc_id = _safe_int(data.get("location_id_real") or data.get("location_id"), 0) or None
                        requested_by = user.get("id")
                        requested_by = _safe_int(requested_by, 0) or None

                        temp_title = f"Service Order (pending) - {unit_name}"
                        desc = _compose_autodesc(data, alerts)

                        cur.execute("""
                            INSERT INTO ServiceCalls (customer_id, location_id, unit_id, title, description, priority, status, requested_by_login_id, created)
                            VALUES (?, ?, ?, ?, ?, 'Normal', 'Open', ?, datetime('now'))
                        """, (cust_id, int(loc_id) if loc_id else None, unit_id_real, temp_title, desc, requested_by))
                        service_call_id = int(cur.lastrowid)

                        ticket_no = _generate_ticket_no(service_call_id)
                        pdf_path, pdf_bytes = generate_service_order_pdf(ticket_no, data, health, alerts, company)

                        final_title = f"{ticket_no} - {unit_name} - {data.get('customer','')}"
                        cur.execute("UPDATE ServiceCalls SET title = ? WHERE ID = ?", (final_title, service_call_id))

                        params = {"ticket_no": ticket_no, "service_call_id": service_call_id, "unit_id": unit_id_real}
                        cur.execute("""
                            INSERT INTO Reports (customer_id, location_id, unit_id, report_type, params_json, status, created, output_path, requested_by_login_id)
                            VALUES (?, ?, ?, 'ServiceOrder', ?, 'Done', datetime('now'), ?, ?)
                        """, (cust_id, int(loc_id) if loc_id else None, unit_id_real, json.dumps(params), pdf_path, requested_by))

                        conn.commit()
                        return pdf_path, pdf_bytes, ticket_no
                    finally:
                        conn.close()
                except Exception as e:
                    raise

            def _email(recipients: List[str], ticket_no: str, pdf_bytes: bytes, pdf_filename: str):
                subject = f"Service Order {ticket_no} - {unit_name}"
                body = "\n".join([
                    f"Service Order: {ticket_no}",
                    f"Customer: {data.get('customer','—')}",
                    f"Location: {location_text}",
                    f"Unit: {unit_name} ({data.get('make','—')} {data.get('model','—')})",
                    "",
                    "Attached: Service Order PDF",
                ])
                ok, msg = send_service_order_email(subject, body, recipients, pdf_bytes, pdf_filename)
                ui.notify(msg, type="positive" if ok else "negative")

            def _download(pdf_path: str):
                with open(pdf_path, "rb") as f:
                    b = f.read()
                ui.download(b, filename=os.path.basename(pdf_path))

            # ----------------------------
            # ROLE-BASED BUTTONS
            # ----------------------------
            with ui.row().classes("gap-2 justify-end w-full"):
                if hierarchy == 4:
                    # Client: email only + 24-hour lockout
                    def client_email_order():
                        try:
                            cust_id = _safe_int(data.get("customer_id"), 0)
                            if not cust_id:
                                ui.notify("Cannot submit: customer_id missing.", type="negative")
                                return

                            ok, msg = client_can_open_service_call(unit_id_real, cust_id)
                            if not ok:
                                ui.notify(msg, type="warning")
                                return

                            pdf_path, pdf_bytes, ticket_no = _build_pdf_store_get_ticket()

                            recipients = [company_service, company_owner, client_email]
                            recipients = [r for r in recipients if (r or "").strip()]
                            if not recipients:
                                ui.notify("No recipient emails found (company/client).", type="negative")
                                return

                            _email(recipients, ticket_no, pdf_bytes, os.path.basename(pdf_path))
                        except Exception as e:
                            _show_error_dialog("Client Email Service Order failed", e)

                    ui.button("Email Service Order", on_click=client_email_order).props("color=green dense")

                else:
                    # Admin/Tech: email to client + print
                    def email_to_client():
                        try:
                            if not client_email:
                                ui.notify("Client has no email on file.", type="negative")
                                return
                            pdf_path, pdf_bytes, ticket_no = _build_pdf_store_get_ticket()
                            recipients = [client_email, company_service, company_owner]
                            recipients = [r for r in recipients if (r or "").strip()]
                            _email(recipients, ticket_no, pdf_bytes, os.path.basename(pdf_path))
                        except Exception as e:
                            _show_error_dialog("Email to Client failed", e)

                    def print_pdf():
                        try:
                            pdf_path, pdf_bytes, ticket_no = _build_pdf_store_get_ticket()
                            _download(pdf_path)
                            ui.notify(f"PDF ready: {ticket_no}", type="positive")
                        except Exception as e:
                            _show_error_dialog("Print (PDF) failed", e)

                    ui.button("Email to Client", on_click=email_to_client).props("outline dense color=green")
                    ui.button("Print (PDF)", on_click=print_pdf).props("dense color=green")

            ui.separator().classes("my-2")
            ui.button("Close", on_click=dlg.close).props("flat dense size=sm")


# ----------------------------
# Page entrypoint
# ----------------------------

def page():
    if not require_login():
        return

    customer_filter = _get_customer_filter_for_user()

    with layout("HVAC Dashboard", show_logout=True):
        if customer_filter is None:
            render_dashboard(customer_id=None)
        else:
            if not customer_filter:
                ui.label("Error: your login has no customer assigned.").classes("text-red-500 text-lg")
                return
            render_dashboard(customer_id=int(customer_filter))
