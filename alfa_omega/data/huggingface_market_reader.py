"""Controlled Hugging Face market-data reader for ALFA OMEGA.

Only an explicitly selected market-data candidate is downloaded. Files are
read into temporary runtime storage, hashed, normalized to UTC, validated as
OHLCV, and returned with auditable source metadata.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from alfa_omega.data.data_catalog import build_data_catalog_entry
from alfa_omega.data.market_file_classifier import MarketDataFileCandidate


_ALLOWED_MARKETS = {"BTC/USD", "XAU/USD"}
_ALLOWED_TIMEFRAMES = {"1m", "5m", "15m", "1h", "4h", "1d", "1w"}
_ALLOWED_FORMATS = {"csv", "parquet"}
_TIMESTAMP_NAMES = ("timestamp", "datetime", "date", "time")
_OHLCV_NAMES = ("open", "high", "low", "close", "volume")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    mapping = {str(column).strip().lower(): column for column in frame.columns}
    rename: dict[Any, str] = {}
    for name in _OHLCV_NAMES:
        source = mapping.get(name)
        if source is not None:
            rename[source] = name
    frame = frame.rename(columns=rename)

    if not all(name in frame.columns for name in _OHLCV_NAMES):
        missing = sorted(set(_OHLCV_NAMES).difference(frame.columns))
        raise ValueError(f"missing OHLCV columns: {missing}")
    return frame


def _set_utc_index(frame: pd.DataFrame) -> pd.DataFrame:
    if isinstance(frame.index, pd.DatetimeIndex):
        timestamps = frame.index
    else:
        mapping = {str(column).strip().lower(): column for column in frame.columns}
        timestamp_column = next(
            (mapping[name] for name in _TIMESTAMP_NAMES if name in mapping),
            None,
        )
        if timestamp_column is None:
            raise ValueError("missing timestamp column")
        timestamps = pd.to_datetime(frame[timestamp_column], errors="coerce")
        frame = frame.drop(columns=[timestamp_column])

    if timestamps.isna().any():
        raise ValueError("invalid timestamp values")

    if isinstance(timestamps, pd.Series):
        timestamps = pd.DatetimeIndex(timestamps)

    if timestamps.tz is None:
        timestamps = timestamps.tz_localize("UTC")
    else:
        timestamps = timestamps.tz_convert("UTC")

    frame = frame.copy()
    frame.index = timestamps
    frame.index.name = "timestamp"
    return frame.sort_index()


def _read_downloaded(path: Path, file_format: str) -> pd.DataFrame:
    if file_format == "csv":
        return pd.read_csv(path)
    if file_format == "parquet":
        return pd.read_parquet(path)
    raise ValueError(f"unsupported format: {file_format}")


def _validate_candidate(candidate: MarketDataFileCandidate) -> None:
    if candidate.classification != "MARKET_DATA_CANDIDATE":
        raise ValueError("file is not a validated market-data candidate")
    if candidate.market not in _ALLOWED_MARKETS:
        raise ValueError(f"unsupported market: {candidate.market}")
    if candidate.timeframe not in _ALLOWED_TIMEFRAMES:
        raise ValueError(f"unsupported timeframe: {candidate.timeframe}")
    if candidate.format not in _ALLOWED_FORMATS:
        raise ValueError(f"unsupported format: {candidate.format}")


def _download_file(
    api: Any,
    *,
    repository: str,
    path: str,
    destination: Path,
) -> Path:
    downloader = getattr(api, "hf_hub_download", None)
    if downloader is None:
        try:
            from huggingface_hub import hf_hub_download
        except ImportError as exc:
            raise RuntimeError(
                "huggingface_hub is required for Hugging Face data access"
            ) from exc
        token = os.getenv("HF_TOKEN")
        if not token:
            raise RuntimeError("HF_TOKEN is not configured")
        downloaded = hf_hub_download(
            repo_id=repository,
            filename=path,
            repo_type="dataset",
            token=token,
            local_dir=str(destination),
        )
        return Path(downloaded)

    downloaded = downloader(
        repo_id=repository,
        filename=path,
        repo_type="dataset",
        local_dir=str(destination),
    )
    return Path(downloaded)


def read_market_data_file(
    api: Any,
    *,
    repository: str,
    candidate: MarketDataFileCandidate,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Download and validate exactly one selected market-data file."""
    _validate_candidate(candidate)
    if not repository.strip():
        raise ValueError("repository must not be empty")

    with tempfile.TemporaryDirectory(prefix="alfa_omega_hf_") as temp_dir:
        local_dir = Path(temp_dir)
        downloaded = _download_file(
            api,
            repository=repository,
            path=candidate.path,
            destination=local_dir,
        )
        if not downloaded.is_file():
            raise FileNotFoundError(f"downloaded file not found: {downloaded}")

        source_sha256 = _sha256(downloaded)
        frame = _read_downloaded(downloaded, candidate.format)
        frame = _normalize_columns(frame)
        frame = _set_utc_index(frame)

        catalog = build_data_catalog_entry(
            frame,
            market=candidate.market,
            timeframe=candidate.timeframe,
            source=f"huggingface:{repository}",
            source_path=downloaded,
        )
        quality = catalog["quality"]
        if quality["status"] == "CORRUPTED":
            raise ValueError(f"market data failed quality validation: {quality}")

        catalog["source_path"] = candidate.path
        catalog["source_sha256"] = source_sha256
        catalog["repository"] = repository
        catalog["format"] = candidate.format

    return frame, catalog
