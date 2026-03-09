import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def log_action(
    db,
    user_id: Optional[int],
    username: str,
    action: str,
    ip: Optional[str] = None,
    fiscal_code: Optional[str] = None,
    details: Optional[dict] = None,
):
    try:
        await db.execute(
            """
            INSERT INTO audit_logs (user_id, username, action, fiscal_code, ip_address, details)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            user_id,
            username,
            action,
            fiscal_code,
            ip,
            json.dumps(details) if details else None,
        )
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
