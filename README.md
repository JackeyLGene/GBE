# GBE — Generative Being Externalized

A trilogy in three papers. One cognitive architecture. Zero training, zero learned weights, zero domain labels.

---

## What this is

A centroid detector. Two operations — merge what is similar, prune what is not reinforced — converge any vector-encoded stream to its statistical attractors under limited memory. The attractors are centroids. Multiple detectors coupled through a shared field produce cross-harm — a scalar of structural divergence. Centroids that survive the memory cycle precipitate into an externalized Codex, outlasting the cavity that produced them.

The same core instrument, with pre-declared domain-specific encodings and ablated parameter families, detects structure across four domains that share no physical dimensions: UN diplomatic voting (1946-2025), Bach's Well-Tempered Clavier, cross-species DNA alignments, and human mRNA transcripts.

The trilogy spans three stages of a single discovery:

| Paper | Metaphor | Core contribution | Key constant |
|-------|----------|-------------------|--------------|
| **I: GEME** | The static prism | Self-reference is possible. The Shannon-Gödel bridge costs 0.026 bits. | τ₀ = 0.60 |
| **II: BGM** | Time enters | The bridge breathes. Temporal decoupling enhances differentiation by 49%. | GI = 4 |
| **III: EE** | Information builds its own time | Externalization. Four-domain evidence: WTC Codex formation, DNA archive boundary, RNA blind boundary detection, UN civilizational-scale forward prediction. | GI^N |

---

## Code

Instrument core — zero external dependencies, Python 3.8+ stdlib only.

| File | Lines | Role |
|------|-------|------|
| `code/geme.py` | ~800 | GEME kernel — the frame economy primitive. Never modified. |
| `code/geruon.py` | ~2500 | Geruon — endogenous time (τ), structural identity (struct_key, collision-resistant), operational τ (merge/cooccur/prune), 碰数 boundary detection, Codex externalized memory |
| `code/we_core.py` | ~550 | We — multi-Self collective architecture, BiasField, cross-Self harm, collective pattern detector |
| `code/bgm_core.py` | 180 | BGM GEMENet — N GEME units + G0 observer |
| `code/bgm_bacteria.py` | 367 | Spatial grid experiment — 8×8 GEME units, emergent differentiation |
| `code/midi_encoder.py` | 70 | MIDI → chroma vector encoding |

**Run it:**

```python
from geruon import Geruon

g = Geruon(vec_dim=16, memory_cap=12, kappa_tau=0.5)
g.process_vec([0.1, 0.2, 0.3, ...], "first_input")
print(g.phase, g.tau)  # It breathes.
```

---

## Experiments

Frozen scripts producing the EE paper's reported results. Organized by domain:

| Directory | Domain | Paper § | Core result |
|-----------|--------|---------|-------------|
| `experiments/un/` | UN diplomatic voting | §4.1 | 2025 disp=0.448, rank 1/79; P5 ablation; FRED negative control |
| `experiments/wtc/` | Bach WTC | §4.2 | Transposition equivariance 100%; Codex formation and selection |
| `experiments/dna/` | DNA archive | §4.3 | Exon/intron d=−0.97 (n=200); AHSG fork column d=+1.51 (single-gene) |
| `experiments/rna/` | RNA operation boundary | §4.4 | CDS stop 98-100% ≤3 windows (parameter-invariant); CDS start 66% ≤3 windows |

Data dependencies: `pandas`, `numpy`, `pyarrow`; `pybigtools` (RNA bigWig only). Raw data sources documented in `experiments/rna/rna-final-2026-05-30.md`.

---

## Papers

- [Paper I: GEME](paper/gEME.pdf) — *A Self-Referential Prism for Cognitive Modeling*
- [Paper II: BGM](paper/bGM.pdf) — *Building Bridge: From Bach to Bacteria and Forward*
- [Paper III: EE](paper/ee.pdf) — *Externalization Engine: Creation → We Create → Create Us* (v1.5, May 2026)
- [EE Paper Source](paper/ee_paper_v1.5.md)

---

*Not a model of cognition. A system for detecting structure and precipitating centroids across time.*
