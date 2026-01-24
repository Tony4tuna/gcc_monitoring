# core/issue_rules.py
# Central rules for issue -> ticket creation

from datetime import datetime, timedelta

from core.tickets_repo import (
    get_open_ticket_for_issue,
    get_last_ticket_time_for_unit,
)


def can_create_ticket(issue_id: int, unit_id: int, is_admin: bool):
    """
    Returns (allowed: bool, reason: str)
    """

    # Rule 1: no duplicate open ticket for same issue
    if get_open_ticket_for_issue(issue_id):
        return False, "A ticket already exists for this issue"

    # Rule 2: client cooldown (24 hours)
    if not is_admin:
        last_time = get_last_ticket_time_for_unit(unit_id)
        if last_time:
            if datetime.utcnow() - last_time < timedelta(hours=24):
                return False, "You must wait 24 hours before creating another ticket"

    return True, "OK"
