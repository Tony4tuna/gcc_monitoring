# core/issues_repo.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from core.db import get_conn


def list_issue_types(enabled_only: bool = True) -> List[Dict[str, Any]]:
    """
    Returns the configured issue types from the DB table: issue_types
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        where = ""
        params: tuple = ()
        if enabled_only:
            where = "WHERE active = 1"

        rows = cur.execute(
            f"""
            SELECT
                id,
                code,
                title,
                description,
                category,
                severity_default,
                active
            FROM issue_types
            {where}
            ORDER BY severity_default DESC, title ASC
            """,
            params,
        ).fetchall()

        return [dict(r) for r in rows]

    finally:
        conn.close()


def get_issue_type_by_code(code: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        row = cur.execute(
            """
            SELECT
                id,
                code,
                title,
                description,
                category,
                severity_default,
                active
            FROM issue_types
            WHERE code = ?
            LIMIT 1
            """,
            (code,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
