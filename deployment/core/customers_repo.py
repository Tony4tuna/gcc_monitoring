# core/customers_repo.py
from typing import Any, Dict, List
from .db import get_conn


def _dicts(rows) -> List[Dict[str, Any]]:
    return [dict(r) for r in rows]


def list_customers(search: str = "") -> List[Dict[str, Any]]:
    search = (search or "").strip()
    like = f"%{search}%"

    sql = """
    SELECT
        ID,
        company,
        first_name,
        last_name,
        email,
        phone1,
        phone2,
        mobile,
        fax,
        extension1,
        extension2,
        address1,
        address2,
        city,
        state,
        zip,
        website,
        notes,
        extended_notes,
        idstring,
        csr,
        referral,
        credit_status,
        flag_and_lock,
        created
    FROM Customers
    """

    params = ()
    if search:
        sql += """
        WHERE
            company         LIKE ?
            OR first_name   LIKE ?
            OR last_name    LIKE ?
            OR email        LIKE ?
            OR phone1       LIKE ?
            OR phone2       LIKE ?
            OR mobile       LIKE ?
            OR fax          LIKE ?
            OR extension1   LIKE ?
            OR extension2   LIKE ?
            OR address1     LIKE ?
            OR address2     LIKE ?
            OR city         LIKE ?
            OR state        LIKE ?
            OR zip          LIKE ?
            OR website      LIKE ?
            OR notes        LIKE ?
            OR extended_notes LIKE ?
            OR idstring     LIKE ?
            OR csr          LIKE ?
            OR referral     LIKE ?
            OR credit_status LIKE ?
        """
        params = (
            like, like, like, like, like, like,
            like, like, like, like,
            like, like, like, like, like,
            like, like, like, like, like,
            like, like
        )

    sql += " ORDER BY ID DESC;"

    conn = get_conn()
    try:
        rows = conn.execute(sql, params).fetchall()
        return _dicts(rows)
    finally:
        conn.close()


def get_customer(customer_id: int):
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM Customers WHERE ID = ?",
            (customer_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def create_customer(data: Dict[str, Any]) -> int:
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO Customers (
                company, first_name, last_name, email,
                phone1, phone2, mobile, fax,
                extension1, extension2,
                address1, address2, city, state, zip,
                website, idstring, csr, referral, credit_status,
                flag_and_lock,
                notes, extended_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (data.get("company") or "").strip(),
                (data.get("first_name") or "").strip(),
                (data.get("last_name") or "").strip(),
                (data.get("email") or "").strip(),
                (data.get("phone1") or "").strip(),
                (data.get("phone2") or "").strip(),
                (data.get("mobile") or "").strip(),
                (data.get("fax") or "").strip(),
                (data.get("extension1") or "").strip(),
                (data.get("extension2") or "").strip(),
                (data.get("address1") or "").strip(),
                (data.get("address2") or "").strip(),
                (data.get("city") or "").strip(),
                (data.get("state") or "").strip(),
                (data.get("zip") or "").strip(),
                (data.get("website") or "").strip(),
                (data.get("idstring") or "").strip(),
                (data.get("csr") or "").strip(),
                (data.get("referral") or "").strip(),
                (data.get("credit_status") or "").strip(),
                1 if data.get("flag_and_lock") else 0,
                (data.get("notes") or "").strip(),
                (data.get("extended_notes") or "").strip(),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def update_customer(customer_id: int, data: Dict[str, Any]) -> None:
    conn = get_conn()
    try:
        conn.execute(
            """
            UPDATE Customers SET
                company=?,
                first_name=?,
                last_name=?,
                email=?,
                phone1=?,
                phone2=?,
                mobile=?,
                fax=?,
                extension1=?,
                extension2=?,
                address1=?,
                address2=?,
                city=?,
                state=?,
                zip=?,
                website=?,
                idstring=?,
                csr=?,
                referral=?,
                credit_status=?,
                flag_and_lock=?,
                notes=?,
                extended_notes=?
            WHERE ID=?
            """,
            (
                (data.get("company") or "").strip(),
                (data.get("first_name") or "").strip(),
                (data.get("last_name") or "").strip(),
                (data.get("email") or "").strip(),
                (data.get("phone1") or "").strip(),
                (data.get("phone2") or "").strip(),
                (data.get("mobile") or "").strip(),
                (data.get("fax") or "").strip(),
                (data.get("extension1") or "").strip(),
                (data.get("extension2") or "").strip(),
                (data.get("address1") or "").strip(),
                (data.get("address2") or "").strip(),
                (data.get("city") or "").strip(),
                (data.get("state") or "").strip(),
                (data.get("zip") or "").strip(),
                (data.get("website") or "").strip(),
                (data.get("idstring") or "").strip(),
                (data.get("csr") or "").strip(),
                (data.get("referral") or "").strip(),
                (data.get("credit_status") or "").strip(),
                1 if data.get("flag_and_lock") else 0,
                (data.get("notes") or "").strip(),
                (data.get("extended_notes") or "").strip(),
                int(customer_id),
            ),
        )
        conn.commit()
    finally:
        conn.close()



def delete_customer(customer_id: int) -> None:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM Customers WHERE ID = ?", (int(customer_id),))
        conn.commit()
    finally:
        conn.close()
