"""Database setup — SQLite/PostgreSQL connection and ORM models."""

from typing import Any, Dict, List

# TODO: implement database connection, session factory, and ORM models


def store(
    request_id: str,
    user_context: Dict[str, Any],
    prompt: str,
    entities: List[Dict[str, Any]],
    policies: List[Dict[str, Any]],
    risk_result: Dict[str, Any],
    decision_result: Dict[str, Any],
    receipt: Dict[str, Any],
) -> None:
    """Persist a governance record to the database.

    No-op stub until the database layer is implemented.
    """
    # TODO: persist governance record to database
