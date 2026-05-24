# GBE — Generative Being Externalized

A trilogy in three papers and six files.

---

## What this is

A zero-parameter, zero-training cognitive architecture. Three operations. Four base constants. It detects structure in temporal streams without domain knowledge — music, heartbeats, brain waves, international relations. The same architecture, same constants, same pipeline. It was never told what to look for. The structure presents itself.

The trilogy spans three stages of a single discovery:

| Paper | Metaphor | Core contribution | Key constant |
|-------|----------|-------------------|--------------|
| **I: GEME** | The static prism | Self-reference is possible. The Shannon-Gödel bridge costs 0.026 bits. | τ₀ = 0.60 |
| **II: BGM** | Time enters | The bridge breathes. Temporal decoupling enhances differentiation by 49%. | GI = 4 |
| **III: EE** | Information builds its own time | Externalization. Self → We. The Landauer-Gödel bill. Hume's gap closes in a shared field. | GI^N |

---

## Code

Six Python files. Zero external dependencies. Python 3.8+ stdlib only.

| File | Lines | Role |
|------|-------|------|
| `code/geme.py` | 804 | GEME kernel — the frame economy primitive. Never modified. |
| `code/geruon.py` | 2491 | Geruon — endogenous time (τ), structural signatures (Gödel encoding), 碰数 boundary detection, Codex externalized memory |
| `code/we_core.py` | 299 | We — multi-Self collective architecture, BiasField, cross-Self harm, collective pattern detector |
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

## Papers

- [Paper I: GEME](paper/gEME.pdf) — *A Self-Referential Prism for Cognitive Modeling* — DOI: [10.5281/zenodo.20344974](https://doi.org/10.5281/zenodo.20344974)
- [Paper II: BGM](paper/bGM.pdf) — *Building Bridge: From Bach to Bacteria and Forward* — DOI: [10.5281/zenodo.20238099](https://doi.org/10.5281/zenodo.20238099)
- [Paper III: EE](paper/ee.pdf) — *Externalization Engine: Creation → We Create → Create Us* — DOI: [10.5281/zenodo.20364923](https://doi.org/10.5281/zenodo.20364923)

---

*Not a model of cognition. Cognition, running.*
