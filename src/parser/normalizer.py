from datetime import datetime, date
import re


def normalize_text(value):
    if not isinstance(value, str):
        return value

    value = " ".join(value.split())
    return value if value else None


def normalize_date(value):
    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if not isinstance(value, str):
        return value

    value = value.strip()

    # Only try date-like strings.
    if not re.search(r"\d", value):
        return value

    normalized = re.sub(r"[-\s]+", "-", value)
    parts = normalized.split("-")

    if len(parts) == 3:
        try:
            day = int(parts[0])
            month = int(parts[1])
            year = int(parts[2])

            if year < 100:
                year += 2000

            return date(year, month, day).isoformat()

        except ValueError:
            pass

    # Example: 30-726 -> 30-7-26
    match = re.fullmatch(
        r"(\d{1,2})-(\d)(\d{2})",
        normalized,
    )

    if match:
        try:
            day = int(match.group(1))
            month = int(match.group(2))
            year = 2000 + int(match.group(3))

            return date(year, month, day).isoformat()

        except ValueError:
            pass

    return value


def normalize_value(value):
    if value is None:
        return None

    if isinstance(value, (datetime, date)):
        return normalize_date(value)

    if isinstance(value, str):
        return normalize_date(
            normalize_text(value)
        )

    return value