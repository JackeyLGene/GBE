---
title: Home
nav_order: 1
permalink: /
---

# GBE — Generative Being Externalized

**Can a small, zero-training detector find structure in streams without knowing what it's looking at?**

This is a runnable test of that question. No neural network. No labels. No domain-specific rules. Just merge, prune, and read the survivors.

## Start in 5 Minutes

```powershell
git clone https://github.com/JackeyLGene/GBE.git
cd GBE
python docs\quickstart_geruon.py
python docs\quickstart_ee_self.py
```

- `quickstart_geruon.py` — solo Geruon, prints `tau`, `F`, `wit_rate`, `arrow norm`
- `quickstart_ee_self.py` — 3-cavity Self, prints cross-harm time series
- No `pip install` required. Python 3.8+ stdlib only.

After the quickstarts, read the [manuals](docs/) in order.

## Demos

Two runnable demos from the same instrument.

| Demo | Type | Script | Video |
|------|------|--------|-------|
| Sine Boundary Detection | 3-Cavity Self | [demo_self_sine.py](demo/demo_self_sine.py) | [Substack](https://ljieqi.substack.com/p/sine-boundary-detection-3-cavity) |
| Bach C Major Prelude | Solo Geruon | [demo_geruon_bach.py](demo/demo_geruon_bach.py) | [Substack](https://ljieqi.substack.com/p/bach-c-major-prelude-solo-geruon) |

<video controls playsinline preload="metadata" style="width:100%;max-width:900px">
  <source src="{{ '/demo/demo_self_sine.mp4' | relative_url }}" type="video/mp4">
  <a href="{{ '/demo/demo_self_sine.mp4' | relative_url }}">Download Sine Boundary MP4</a>
</video>

<video controls playsinline preload="metadata" style="width:100%;max-width:900px">
  <source src="{{ '/demo/demo_geruon_bach.mp4' | relative_url }}" type="video/mp4">
  <a href="{{ '/demo/demo_geruon_bach.mp4' | relative_url }}">Download Bach Prelude MP4</a>
</video>

A third bridge experiment — [Shepard Paradox](experiments/shepard/) — is an honest negative: the instrument is immune to perceptual illusions that lack physical structure.

## What This Is

GBE is a centroid detector with memory pressure. Two operations — merge similar frames, prune unreinforced frames — converge streams into structural centroids under finite memory.

| Domain | Core result | Limitations |
|--------|-------------|-------------|
| UN diplomatic voting | 2025 displacement rank 1/79; falsifiable 2026-2028 | 79 data points; forward prediction unverified |
| Bach WTC | Transposition equivariance 100%; Codex selection loop | Codex operation scaffolded |
| DNA alignments | Exon/intron d=-0.97; AHSG fork d=+1.51 | AHSG: single-gene calibration |
| RNA transcripts | CDS stop 98-100% within three windows | CDS start 66%; passive detection only |

## The Trilogy

| Paper | Role |
|-------|------|
| **I: GEME** | Static self-reference |
| **II: BGM** | Time enters the bridge |
| **III: EE** | Externalized cognition |

- [Paper I: GEME](paper/gEME.pdf) — DOI: 10.5281/zenodo.20344974
- [Paper II: BGM](paper/bGM.pdf) — DOI: 10.5281/zenodo.20238099
- [Paper III: EE](paper/ee.pdf)
- [EE Supplement](paper/ee_supplement.pdf)

## Reproducibility

- Quickstarts: zero dependencies, Python 3.8+ stdlib only.
- `demo/` and `experiments/shepard/` scripts are runnable bridge examples.
- Frozen experiment scripts under `experiments/`.
- Domain experiments may require `numpy`, `pandas`, `pyarrow`, or `pybigtools`.
- Fastest review path: run both quickstarts → skim [Geruon Manual](docs/GERUON_MANUAL.html) → inspect one experiment track.
