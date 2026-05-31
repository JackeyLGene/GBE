# GBE — Generative Being Externalized

A trilogy in three papers. One cognitive architecture. Zero training, zero learned weights, zero domain labels.

---

## New Here? Start in 5 Minutes

```powershell
cd G:\GBE\GBE
python docs\quickstart_geruon.py       # solo Geruon — F, wit, τ breathing
python docs\quickstart_ee_self.py      # 3-cavity Self — cross-harm across time lenses
```

Both scripts run with zero dependencies. Python 3.8+ stdlib only. You'll see τ converge to ~0.74, F fluctuate with stream structure, and cross-harm spike at block boundaries.

**After the quickstarts, read the manuals in order:**

| # | Manual | What you'll learn |
|---|--------|------------------|
| 1 | [GERUON_MANUAL.md](docs/GERUON_MANUAL.md) | The instrument: API, calibration (fair coin / structon / κ sweep), Faraday readings (F/wit/Δwit), τ/phase/pengshu |
| 2 | [EE_MANUAL.md](docs/EE_MANUAL.md) | The architecture: Self (multi-cavity amplifiers), We (cross-Self harm), Codex (five-stage externalization loop), four experiment domains |
| 3 | [Calibration Report](docs/experiment-passive-calibration-report.md) | Instrument factory calibration: κ/δ/cap/γ/GI quantitative curves, readout policy |

---

## What This Is

A centroid detector. Two operations — merge what is similar, prune what is not reinforced — converge any vector-encoded stream to its statistical attractors under limited memory. The attractors are centroids. Multiple detectors coupled through a shared field produce cross-harm — a scalar of structural divergence. Centroids that survive the memory cycle precipitate into an externalized Codex, outlasting the cavity that produced them.

The same core instrument detects structure across four domains that share no physical dimensions:

| Domain | What it proves | Core result |
|--------|---------------|-------------|
| UN diplomatic voting | Civilizational structure is detectable | 2025 disp=0.448, rank 1/79 (falsifiable 2026-2028) |
| Bach WTC | Externalized cognition converges without priors | Transposition equivariance 100%; five-stage Codex loop |
| DNA alignments | Evolutionary archive is structurally readable | Exon/intron d=−0.97 (n=200); AHSG d=+1.51 |
| RNA transcripts | Operation boundary is blind-detectable | CDS stop 98-100% ≤3 windows (parameter-invariant) |

---

## The Trilogy

| Paper | Metaphor | Core contribution | Key constant |
|-------|----------|-------------------|--------------|
| **I: GEME** | The static prism | Self-reference is possible. The Shannon-Gödel bridge costs 0.026 bits. | τ₀ = 0.60 |
| **II: BGM** | Time enters | The bridge breathes. Temporal decoupling enhances differentiation by 49%. | GI = 4 |
| **III: EE** | Information builds its own time | Externalization. Four-domain evidence. | GI^N |

- [Paper I: GEME](paper/gEME.pdf) — DOI: 10.5281/zenodo.20344974
- [Paper II: BGM](paper/bGM.pdf) — DOI: 10.5281/zenodo.20238099
- [Paper III: EE](paper/ee.pdf) — v1.5, May 2026 — [Source](paper/ee_paper_v1.5.md)

---

## Repository Map

```
GBE/
├── docs/                        ← START HERE: manuals + quickstarts
│   ├── quickstart_geruon.py     # solo Geruon demo (F, wit, τ)
│   ├── quickstart_ee_self.py    # 3-cavity Self demo (cross-harm)
│   ├── GERUON_MANUAL.md         # instrument manual
│   ├── EE_MANUAL.md             # architecture & experiments manual
│   └── experiment-passive-calibration-report.md
│
├── code/                        # instrument core (zero dependencies)
│   ├── geme.py                  # GEME kernel (~800 lines)
│   ├── geruon.py                # Geruon engine (~2500 lines)
│   ├── we_core.py               # We multi-Self tool (~550 lines)
│   ├── bgm_core.py              # BGM GEMENet
│   ├── bgm_bacteria.py          # BGM spatial grid
│   └── midi_encoder.py          # MIDI → chroma
│
├── experiments/                 # frozen experiment scripts
│   ├── un/                      # §4.1 UN prediction
│   ├── wtc/                     # §4.2 Bach WTC
│   ├── dna/                     # §4.3 DNA archive
│   └── rna/                     # §4.4 RNA boundary
│
└── paper/                       # trilogy PDFs + EE source
    ├── gEME.pdf
    ├── bGM.pdf
    ├── ee.pdf                   # EE v1.5
    └── ee_paper_v1.5.md
```

---

*Not a model of cognition. A system for detecting structure and precipitating centroids across time.*
