from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import re
import unicodedata
from typing import Any, Mapping
from urllib.parse import urlparse


ATS_DOMAINS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("greenhouse", ("greenhouse.io",)),
    ("lever", ("lever.co",)),
    ("ashby", ("ashbyhq.com",)),
    ("workday", ("myworkdayjobs.com", "workday.com")),
    ("smartrecruiters", ("smartrecruiters.com",)),
    ("icims", ("icims.com",)),
    ("taleo", ("taleo.net",)),
    ("teamtailor", ("teamtailor.com",)),
    ("workable", ("workable.com",)),
    ("jobvite", ("jobvite.com",)),
    ("recruitee", ("recruitee.com",)),
    ("bamboohr", ("bamboohr.com",)),
)


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    result = re.sub(r"\s+", " ", str(value).replace("\u00a0", " ").strip())
    return result or None


def clean_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = value.split(",")
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        return []
    return [item for value_item in values if (item := clean_text(value_item))]


def as_mapping(value: Any) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def as_decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    text = clean_text(value)
    if not text:
        return None
    normalized = re.sub(r"[^0-9,.-]", "", text)
    if normalized.count(",") and normalized.count("."):
        normalized = normalized.replace(",", "")
    elif normalized.count(",") == 1 and len(normalized.rsplit(",", 1)[-1]) != 3:
        normalized = normalized.replace(",", ".")
    else:
        normalized = normalized.replace(",", "")
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def as_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = clean_text(value)
    if not text:
        return None
    match = re.search(r"\d[\d,.\s]*", text)
    if not match:
        return None
    digits = re.sub(r"\D", "", match.group(0))
    return int(digits) if digits else None


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = clean_text(value)
    return bool(text and text.casefold() in {"true", "1", "yes", "y"})


def normalize_title(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = re.sub(r"[^\w\s]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def workplace_type(value: Any) -> str:
    text = (clean_text(value) or "").casefold().replace("-", " ").replace("_", " ")
    if "remote" in text:
        return "REMOTE"
    if "hybrid" in text:
        return "HYBRID"
    if "on site" in text or text == "onsite":
        return "ON_SITE"
    return "UNKNOWN"


def job_state(value: Any) -> str:
    return {
        "LISTED": "ACTIVE",
        "ACTIVE": "ACTIVE",
        "CLOSED": "CLOSED",
        "EXPIRED": "EXPIRED",
    }.get((clean_text(value) or "").upper(), "DISCOVERED")


def parse_salary_range(value: str | None) -> tuple[Decimal | None, Decimal | None]:
    if not value:
        return None, None
    matches = re.findall(
        r"(?<!\w)(\d+(?:[.,\s]\d{3})*(?:[.,]\d+)?)(?:\s*([kK]))?",
        value,
    )
    numbers: list[Decimal] = []
    for token, suffix in matches[:2]:
        parsed = as_decimal(token)
        if parsed is not None:
            numbers.append(parsed * Decimal("1000") if suffix else parsed)
    if not numbers:
        return None, None
    return (numbers[0], numbers[0]) if len(numbers) == 1 else (numbers[0], numbers[1])


def parse_posted_at(
    timestamp: Any,
    published_at: Any,
    posted_time: Any,
    captured_at: datetime,
) -> tuple[datetime | None, str | None]:
    if timestamp is not None:
        numeric = as_decimal(timestamp)
        if numeric is not None:
            epoch = float(numeric)
            if epoch > 20_000_000_000:
                epoch /= 1000
            try:
                return datetime.fromtimestamp(epoch, tz=timezone.utc), "exact"
            except (OverflowError, OSError, ValueError):
                pass

    published = clean_text(published_at)
    if published:
        try:
            return _utc(datetime.fromisoformat(published.replace("Z", "+00:00"))), "exact"
        except ValueError:
            try:
                return datetime.strptime(published, "%Y-%m-%d").replace(tzinfo=timezone.utc), "date"
            except ValueError:
                pass

    relative = (clean_text(posted_time) or "").casefold()
    if relative in {"just now", "today"}:
        return captured_at, "minute"
    if relative == "yesterday":
        return captured_at - timedelta(days=1), "day"

    match = re.fullmatch(r"(\d+)\s+(minute|hour|day|week|month)s?\s+ago", relative)
    if match:
        count = int(match.group(1))
        unit = match.group(2)
        delta = {
            "minute": timedelta(minutes=count),
            "hour": timedelta(hours=count),
            "day": timedelta(days=count),
            "week": timedelta(weeks=count),
            "month": timedelta(days=count * 30),
        }[unit]
        return captured_at - delta, unit

    return None, None


def detect_ats(url: str | None) -> str | None:
    if not url:
        return None
    host = (urlparse(url).hostname or "").casefold()
    for provider, domains in ATS_DOMAINS:
        if any(domain in host for domain in domains):
            return provider
    return None


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
