# GBE — Generative Being Externalized

A trilogy in three papers, one runnable cognitive instrument, and four frozen experiment tracks.

The public entry point is deliberately small: no model weights, no training pipeline, and no domain labels inside the instrument. The quickstarts below run with Python stdlib only.

---

## Start in 5 Minutes

```powershell
git clone https://github.com/JackeyLGene/GBE.git
cd GBE

python docs\quickstart_geruon.py
python docs\quickstart_ee_self.py
```

Expected first checks:

- `quickstart_geruon.py` runs a solo Geruon and prints `tau`, `F`, `wit_rate`, and `arrow norm`.
- `quickstart_ee_self.py` runs a 3-cavity Self and prints a cross-harm time series.
- No `pip install` is required for these two scripts. They are tested with Python 3.8+.

After the quickstarts, read the manuals in order:

| # | File | Purpose |
|---|------|---------|
| 1 | [docs/GERUON_MANUAL.md](docs/GERUON_MANUAL.md) | Instrument API, Faraday readings, calibration vocabulary, and minimal usage |
| 2 | [docs/EE_MANUAL.md](docs/EE_MANUAL.md) | Self / We / Codex assembly and the four experiment architectures |
| 3 | [docs/experiment-passive-calibration-report.md](docs/experiment-passive-calibration-report.md) | Passive instrument calibration and frozen readout policy |

## Demos

Two zero-dependency demo videos generated from the same instrument. Each runs in under a minute.

### 1. Sine Boundary Detection — 3-Cavity Self

https://github.com/user-attachments/assets/2cfbcd0b-2b1a-473e-a69d-725830775f3b

▶ **[Watch on Substack](https://ljieqi.substack.com/p/sine-boundary-detection-3-cavity)**

A synthetic stream with three known structural boundaries. A 3-cavity Self processes the stream blind — cross-harm peaks at all three boundary positions. The video explains what cross-harm and τ measure, and why they are orthogonal readings.

### 2. Bach C Major Prelude — Solo Geruon

https://github.com/user-attachments/assets/72960818-f4ae-4072-aacb-26f372d3f286

▶ **[Watch on Substack](https://ljieqi.substack.com/p/bach-c-major-prelude-solo-geruon)**

Bach's BWV 846 as 12-dim chroma. A solo Geruon with zero music theory — F responds to harmonic density, wit density tracks structural novelty across four sections, and their divergence shows the two readings are orthogonal. Piano audio synthesized from MIDI.

To regenerate both videos:

```powershell
python demo\make_video.py
```

Requires `matplotlib`, `numpy`, `soundfile`, and `ffmpeg`.

### 3. Shepard Paradox — Structural Negative Result

[`experiments/shepard/_shepard.py`](experiments/shepard/_shepard.py) · [interpretation](docs/experiment-shepard-paradox.md)

The Shepard tone is an auditory illusion of endless ascent. It simultaneously contains a chroma circle (closed) and a height drift (open) — a structural contradiction. A solo Geruon does NOT detect this as a paradox: it locks onto the strong chroma periodicity and barely registers the height drift. A 3-cavity Self confirms the null result. This is an honest negative: the instrument is immune to perceptual illusions that lack physical structure. Good for understanding what the instrument can and cannot see.

---

## What This Is

GBE is a centroid detector with memory pressure.

The instrument repeatedly applies two operations:

- merge similar frames
- prune frames that are not reinforced

Under finite memory, those operations converge streams into structural centroids. Multiple Geruon cavities coupled through shared fields produce cross-harm: a scalar readout of structural divergence across time lenses. Centroids that survive the cycle can be externalized into a Codex, outlasting the cavity that produced them.

The same core instrument is used across four domains:

| Domain | Experiment role | Core reported result |
|--------|-----------------|----------------------|
| UN diplomatic voting | Civilizational structure / forward prediction | 2025 displacement rank 1/79; falsifiable 2026-2028 trajectory |
| Bach WTC | Externalized cognition and Codex convergence | Transposition equivariance 100%; five-stage Codex loop |
| DNA alignments | Evolutionary archive readability | Exon/intron `d≈-0.97`; AHSG fork-column `d=+1.51` |
| RNA transcripts | Molecular operation boundary | Blind CDS stop boundary 98-100% within three windows; start boundary weaker but positive |

---

## The Trilogy

| Paper | Role | Main object |
|-------|------|-------------|
| **I: GEME** | Static self-reference | Shannon-Gödel bridge |
| **II: BGM** | Time enters the bridge | Temporal decoupling and differentiation |
| **III: EE** | Externalized cognition | Geruon / Self / We / Codex and four-domain evidence |

- [Paper I: GEME](paper/gEME.pdf) — DOI: 10.5281/zenodo.20344974
- [Paper II: BGM](paper/bGM.pdf) — DOI: 10.5281/zenodo.20238099
- [Paper III: EE](paper/ee.pdf) — v1.6, May 2026
- [EE Supplement](paper/ee_supplement.pdf)

---

## Repository Map

```text
GBE/
├── docs/
│   ├── quickstart_geruon.py
│   ├── quickstart_ee_self.py
│   ├── GERUON_MANUAL.md
│   ├── EE_MANUAL.md
│   ├── experiment-passive-calibration-report.md
│   └── experiment-shepard-paradox.md
├── demo/
│   ├── demo_self_sine.mp4          # sine boundary detection (3-cavity Self)
│   ├── demo_geruon_bach.mp4        # Bach prelude (solo Geruon, with audio)
│   ├── demo_self_sine.py           # text-mode demo (runnable)
│   ├── demo_geruon_bach.py         # text-mode demo (runnable)
│   ├── make_video.py               # regenerates both MP4s
│   └── bwv846.mid                  # Bach C major prelude
├── code/
│   ├── geme.py
│   ├── geruon.py
│   ├── we_core.py
│   ├── bgm_core.py
│   ├── bgm_bacteria.py
│   ├── midi_encoder.py
│   └── _calibrate_*.py
├── experiments/
│   ├── un/
│   ├── wtc/
│   ├── dna/
│   ├── rna/
│   └── shepard/
└── paper/
    ├── gEME.pdf
    ├── bGM.pdf
    ├── ee.pdf
    └── ee_supplement.pdf
```

---

## Reproducibility Notes

- The two quickstarts are zero-dependency checks for the public instrument.
- The `demo/` and `experiments/shepard/` scripts are small runnable bridge examples.
- The frozen experiment scripts are included under `experiments/`.
- Large raw datasets are not committed; data sources and expected inputs are documented in each experiment track.
- Domain experiments may require packages such as `numpy`, `pandas`, `pyarrow`, or `pybigtools`, depending on the script.

The fastest review path is: run both quickstarts, skim the Geruon manual, then inspect one experiment track.
