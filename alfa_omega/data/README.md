# DATA

ALFA OMEGA does not store massive historical market data in GitHub or MongoDB.

## Sources

The historical source of record currently includes the private Hugging Face
dataset repository:

- `Macabro10000/trading-data`

Access credentials are runtime secrets only. They must never be committed to the
repository, embedded in source code, or written into catalog artifacts.

## Data flow

```
Hugging Face source
      ↓
read-only inventory
      ↓
data quality / provenance
      ↓
validated market data
      ↓
research dataset builder
```

The inventory layer does not download, modify, delete, or rewrite source data.
Actual market files are kept outside the Git repository and are referenced by
provenance metadata and checksums.

## Supported ALFA OMEGA markets

- BTC/USD
- XAU/USD

Research data must be normalized to timezone-aware UTC timestamps and validated
with `alfa_omega.data.data_catalog` before entering the research pipeline.
