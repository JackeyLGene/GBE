---
title: RNA Transcripts
parent: Experiments
nav_order: 4
---

# RNA Operation Boundary — §4.4

Blind translational boundary detection. The instrument locates CDS boundaries without codon knowledge, AUG scanning, or genetic code. Temporal-lens divergence produces cross-harm peaks at structural transitions.

## Scripts

| Script | Purpose | Runtime |
|--------|---------|---------|
| `_rna_te_cds.py` | CDS-UTR structural separation. 3-cavity Self, 3-mer encoding, genomic-order windows. | ~2min |
| `_rna_boundary_final.py` | Blind CDS boundary detection. 2-cavity/3-cavity Self, W=32-48 nt. Multi-seed (3×). | ~5min |
| `_rna_close.py` | RPF ablation final. Fork vs RPF-only vs process-permuted. Closes Phase 2 coupling question. | ~3min |

## Data

- **Human TE atlas**: transcript sequences + CDS masks (parquet, ~7,500 transcripts)
- **HeLa RPF bigWig tracks**: GSE79664, 7 samples (`_rna_close.py` only)
- **GENCODE v49 GTF**: primary assembly (`_rna_close.py` only)

Expected location: `data/rna/`. RPF bigWig tracks require `pybigtools` (Windows). Raw data from RPFdb v3 and GENCODE.

## Run Order

```powershell
cd experiments\rna
python _rna_te_cds.py              # CDS-UTR separation baseline
python _rna_boundary_final.py      # blind boundary detection (core result)
python _rna_close.py               # RPF ablation (optional, needs bigWig)
```

## Dependencies

`numpy`, `pandas`, `pyarrow` (parquet). `pybigtools` for `_rna_close.py` bigWig reads (Windows only). Core instrument: `code/geruon.py`, `code/geme.py` (stdlib only).

## Key Results

- CDS-UTR separation: d=−0.84 (n=100). Coding regions produce more regular 3-mer organization.
- **CDS stop**: 98-100% within ±3 windows (24 nt), **parameter-invariant** — all configs and seeds converge to median −1.0 window.
- **CDS start**: 66% within ±3 windows, 75% within ±5. Best with 2-cavity W=32 nt, κ=0.01/500. Systematic ~1 window offset.
- **AUG control**: 98% discrimination (3-cavity extreme κ spread 0.005/10/5000). Transition-magnitude detection, not motif detection.
- **Asymmetry is biological**: CDS→3'UTR is a structural cliff. 5'UTR→CDS is a ramp. The instrument reads what biology built.
- RPF coupling: negative. Fork d=−0.93, RPF-only d=−0.91, process-permuted d=−0.99. Occupancy-driven.

## What Didn't Work

- **CDS start**: 66% within ±3 windows — worse than stop (98-100%). The 5'UTR→CDS transition is structurally gradual; the instrument reads what biology built.
- **AUG motif detection**: the instrument does NOT scan for AUG. The start signal (such as it is) comes from transition magnitude, not motif recognition.
- **RPF as independent signal**: ribosome profiling does not add information beyond the transcript sequence itself. Process-permuted RPF produces nearly identical results (d=−0.99).
