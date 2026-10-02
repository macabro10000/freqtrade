"""Controlled internet research intake for ALFA OMEGA.

Internet content is evidence for research, never executable strategy logic.
Fetched material is stored as immutable source metadata so hypotheses can be
traced back to the source and later revalidated. The module deliberately does
not execute code found on the web.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import ipaddress
import re
import socket
from urllib.parse import urlparse
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ResearchSource:
    source_id: str
    url: str
    title: str
    fetched_at: str
    content_sha256: str
    content_length: int
    status: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResearchFinding:
    finding_id: str
    source_id: str
    topic: str
    claim: str
    evidence: str
    confidence: float
    state: str = "RESEARCH_CANDIDATE"


def _safe_host(host: str) -> None:
    if not host:
        raise ValueError("URL host is required")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, None)}
    except OSError as exc:
        raise ValueError("could not resolve research source host") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError("research source resolves to a non-public address")


def _source_id(url: str) -> str:
    return "SRC-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def fetch_research_source(
    url: str,
    *,
    max_bytes: int = 1_000_000,
    timeout_seconds: float = 15.0,
) -> tuple[ResearchSource, str]:
    """Fetch public text/HTML for research; never executes downloaded content."""
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"}:
        raise ValueError("research URLs must use http or https")
    _safe_host(parsed.hostname or "")

    request = Request(
        url,
        headers={
            "User-Agent": "ALFA-OMEGA-Research/1.0",
            "Accept": "text/html,text/plain,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        if not any(token in content_type for token in ("text/", "html", "json", "xml")):
            raise ValueError("research source is not a text-compatible document")
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise ValueError("research source exceeds max_bytes")
        charset = "utf-8"
        match = re.search(r"charset=([^;]+)", content_type)
        if match:
            charset = match.group(1).strip()
        text = body.decode(charset, errors="replace")

    digest = hashlib.sha256(body).hexdigest()
    source = ResearchSource(
        source_id=_source_id(url),
        url=url,
        title=parsed.netloc,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        content_sha256=digest,
        content_length=len(body),
        status="FETCHED",
        notes=(
            "External content is research evidence only.",
            "Downloaded content is never executed as code.",
        ),
    )
    return source, text


def build_finding(
    *,
    source: ResearchSource,
    topic: str,
    claim: str,
    evidence: str,
    confidence: float = 0.5,
) -> ResearchFinding:
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be in [0, 1]")
    finding_id = "FIND-" + hashlib.sha256(
        f"{source.source_id}|{topic}|{claim}".encode("utf-8")
    ).hexdigest()[:16]
    return ResearchFinding(
        finding_id=finding_id,
        source_id=source.source_id,
        topic=topic,
        claim=claim,
        evidence=evidence,
        confidence=confidence,
    )


def research_to_dict(value: ResearchSource | ResearchFinding) -> dict[str, object]:
    return asdict(value)
