from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def normalize_oracle_date(date_str: str) -> Optional[str]:
    """Convert Oracle date format (DD-MON-YY) to ISO format (YYYY-MM-DD)."""
    if not date_str or date_str.strip() == "":
        return None
    try:
        dt = datetime.strptime(date_str.strip().upper(), "%d-%b-%y")
        if dt.year > datetime.now().year:
            dt = dt.replace(year=dt.year - 100)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def normalize_date(date_str: str) -> Optional[str]:
    """Normalize any date format to ISO format."""
    if not date_str or date_str.strip() == "":
        return None

    date_str = date_str.strip()

    if len(date_str) == 10 and date_str[4] == "-" and date_str[7] == "-":
        return date_str

    if "-" in date_str:
        result = normalize_oracle_date(date_str)
        if result:
            return result

    if "/" in date_str:
        try:
            dt = datetime.strptime(date_str, "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def calculate_age(birth_date_str: str) -> Optional[int]:
    """Calculate age from birth date in ISO format."""
    if not birth_date_str:
        return None
    try:
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age
    except ValueError:
        return None
