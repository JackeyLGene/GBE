# UN Diplomatic Voting — §4.1

Civilizational-scale forward prediction. 79 years of UN General Assembly ideal points (1946-2025), 193 countries. P5 ablation and FRED economic negative control.

## Scripts

| Script | Purpose | Runtime |
|--------|---------|---------|
| `_un_predict.py` | Annual ideal-point pipeline. Centroid displacement time series. 2025 signal. | ~30s |
| `_un_p5_ablation.py` | Systematic P5 ablation: No-P5 / P5-only / No-USA / No-Russia / Random-5. | ~2min |
| `_un_fred_only.py` | FRED economic negative control (NASDAQ, T10Y, CPI, etc.). Same pipeline, pure economic data. | ~30s |

## Data

- **UN ideal points**: Voeten, Strezhnev & Bailey, Harvard Dataverse V33
- **FRED economic indicators**: NASDAQ, T10Y, T2Y, FedFunds, CPI, Unemployment (1993-2025)

Data files must be obtained from source and placed in a `data/` directory at the repo root. Expected format: CSV/parquet with country-year ideal-point values.

## Run Order

```powershell
cd experiments\un
python _un_predict.py       # main prediction pipeline
python _un_p5_ablation.py   # P5 ablation
python _un_fred_only.py     # economic negative control
```

## Dependencies

`numpy`, `pandas`. Core instrument: `code/geruon.py`, `code/geme.py` (stdlib only).

## Key Results

- 2025 great-power alignment displacement: 0.448 (rank 1/79, excluding initialization artifact)
- P5 ablation: signal concentrated in great-power layer (No-USA = 0.550, P5-only = 0.448)
- FRED negative control: 2025 economic displacement rank 24/33 — structurally normal
- Falsifiable prediction: 2026-2028 structural collapse of US-led P5 alignment. Three verification criteria.

## What Didn't Work

- **Resolution-level pipeline**: matched 3/4 historical events (Soviet collapse 1991, financial crisis 2008, Ukraine 2022; Crimea 2014 missed). Not used for the forward signal.
- **Non-P5 signal**: global-only encoding yields displacement 0.101 (rank 12/78) — elevated but not extreme. Signal concentrated in great-power layer.
- **Expression-type data**: same pipeline on FRED economic indicators — 2025 structurally normal (rank 24/33). Instrument needs relational structure.
