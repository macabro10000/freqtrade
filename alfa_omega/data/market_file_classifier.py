"""Classify Hugging Face market-data files before downloading them."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass

from alfa_omega.data.huggingface_catalog import HuggingFaceFile


_MARKET_ALIASES = {
    "btc": "BTC/USD",
    "btcusd": "BTC/USD",
    "btc_usd": "BTC/USD",
    "btc-usd": "BTC/USD",
    "xau": "XAU/USD",
    "xauusd": "XAU/USD",
    "xau_usd": "XAU/USD",
    "xau-usd": "XAU/USD",
}

_TIMEFRAME_PATTERN = re.compile(
    r"(?<![a-z0-9])(?P<timeframe>1m|5m|15m|1h|4h|1d|1w)(?![a-z0-9])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MarketDataFileCandidate:
    path: str
    size: int | None
    market: str | None
    timeframe: str | None
    format: str | None
    classification: str


def _normalize_market(value: str) -> str | None:
    return _MARKET_ALIASES.get(value.lower())


def _infer_market(path: str) -> str | None:
    tokens = re.split(r"[/_.\- ]+", path.lower())
    for token in tokens:
        market = _normalize_market(token)
        if market is not None:
            return market
    compact = re.sub(r"[^a-z0-9]", "", path.lower())
    for alias, market in sorted(_MARKET_ALIASES.items(), key=lambda item: -len(item[0])):
        compact_alias = re.sub(r"[^a-z0-9]", "", alias)
        if compact_alias in compact:
            return market
    return None


def _infer_timeframe(path: str) -> str | None:
    matches = _TIMEFRAME_PATTERN.findall(path)
    normalized = {match.lower() for match in matches}
    return next(iter(normalized)) if len(normalized) == 1 else None


def _infer_format(path: str) -> str | None:
    suffix = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return suffix or None


def classify_file(item: HuggingFaceFile) -> MarketDataFileCandidate:
    market = _infer_market(item.path)
    timeframe = _infer_timeframe(item.path)
    file_format = _infer_format(item.path)

    if market in {"BTC/USD", "XAU/USD"} and timeframe in {
        "1m",
        "5m",
        "15m",
        "1h",
        "4h",
        "1d",
        "1w",
    }:
        classification = "MARKET_DATA_CANDIDATE"
    elif market is not None or timeframe is not None:
        classification = "RELATED_BUT_UNRESOLVED"
    else:
        classification = "UNRESOLVED"

    return MarketDataFileCandidate(
        path=item.path,
        size=item.size,
        market=market,
        timeframe=timeframe,
        format=file_format,
        classification=classification,
    )


def classify_inventory(
    files: Iterable[HuggingFaceFile],
) -> list[dict[str, object]]:
    """Classify files without downloading or reading their contents."""
    candidates = [classify_file(item) for item in files]
    candidates.sort(key=lambda item: item.path)
    return [asdict(item) for item in candidates]
