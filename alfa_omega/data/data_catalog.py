"""Auditable market-data catalog and quality checks for ALFA OMEGA.

This module does not download data or infer missing history. It inventories a
provided OHLCV frame and records deterministic quality evidence.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


_TIMEFRAME_DELTAS = {
    "1m": pd.Timedelta(minutes=1),
    "5m": pd.Timedelta(minutes=5),
    "15m": pd.Timedelta(minutes=15),
    "1h": pd.Timedelta(hours=1),
    "4h": pd.Timedelta(hours=4),
    "1d": pd.Timedelta(days=1),
    "1w": pd.Timedelta(weeks=1),
}


@dataclass(frozen=True)
class DataQuality:
    rows: int
    duplicate_timestamps: int
    monotonic: bool
    timezone: str | None
    utc_normalized: bool
    null_ohlcv: int
    invalid_ohlc: int
    negative_volume: int
    gap_count: int
    max_gap_seconds: float
    status: str


@dataclass(frozen=True)
class DataCatalogEntry:
    market: str
    timeframe: str
    source: str
    source_path: str | None
    source_sha256: str | None
    rows: int
    time_start: str | None
    time_end: str | None
    quality: DataQuality
    schema_columns: tuple[str, ...]
    catalog_version: str = "v1"


def _file_sha256(path: str | Path | None) -> str | None:
    if path is None:
        return None
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"source_path does not exist: {file_path}")
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_ohlcv_columns(frame: pd.DataFrame) -> None:
    required = {"open", "high", "low", "close", "volume"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"missing OHLCV columns: {missing}")


def inspect_data_quality(frame: pd.DataFrame, timeframe: str) -> DataQuality:
    if timeframe not in _TIMEFRAME_DELTAS:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    _validate_ohlcv_columns(frame)

    index = frame.index
    timezone = str(index.tz) if isinstance(index, pd.DatetimeIndex) and index.tz else None
    utc_normalized = timezone == "UTC"

    duplicate_timestamps = int(index.duplicated(keep=False).sum())
    monotonic = bool(index.is_monotonic_increasing)

    numeric = frame[["open", "high", "low", "close", "volume"]]
    null_ohlcv = int(numeric.isna().sum().sum())
    invalid_ohlc = int(
        (
            (numeric["high"] < numeric[["open", "close"]].max(axis=1))
            | (numeric["low"] > numeric[["open", "close"]].min(axis=1))
            | (numeric["high"] < numeric["low"])
        ).sum()
    )
    negative_volume = int((numeric["volume"] < 0).sum())

    gap_count = 0
    max_gap_seconds = 0.0
    if isinstance(index, pd.DatetimeIndex) and len(index) > 1:
        deltas = index[1:] - index[:-1]
        expected = _TIMEFRAME_DELTAS[timeframe]
        gaps = deltas[deltas > expected]
        gap_count = len(gaps)
        if gap_count:
            max_gap_seconds = float(gaps.max().total_seconds())

    status = "READY"
    if (
        not isinstance(index, pd.DatetimeIndex)
        or timezone is None
        or not utc_normalized
        or duplicate_timestamps
        or not monotonic
        or null_ohlcv
        or invalid_ohlc
        or negative_volume
    ):
        status = "CORRUPTED"
    elif gap_count:
        status = "READY_WITH_WARNINGS"

    return DataQuality(
        rows=len(frame),
        duplicate_timestamps=duplicate_timestamps,
        monotonic=monotonic,
        timezone=timezone,
        utc_normalized=utc_normalized,
        null_ohlcv=null_ohlcv,
        invalid_ohlc=invalid_ohlc,
        negative_volume=negative_volume,
        gap_count=gap_count,
        max_gap_seconds=max_gap_seconds,
        status=status,
    )


def build_data_catalog_entry(
    frame: pd.DataFrame,
    *,
    market: str,
    timeframe: str,
    source: str,
    source_path: str | Path | None = None,
) -> dict[str, object]:
    quality = inspect_data_quality(frame, timeframe)
    time_start = frame.index.min().isoformat() if len(frame) else None
    time_end = frame.index.max().isoformat() if len(frame) else None
    entry = DataCatalogEntry(
        market=market,
        timeframe=timeframe,
        source=source,
        source_path=str(source_path) if source_path is not None else None,
        source_sha256=_file_sha256(source_path),
        rows=len(frame),
        time_start=time_start,
        time_end=time_end,
        quality=quality,
        schema_columns=tuple(str(column) for column in frame.columns),
    )
    return asdict(entry)
