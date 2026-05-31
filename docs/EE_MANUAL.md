---
title: EE Manual
nav_order: 2
parent: Manuals
---

# EE Manual

> Architecture and experiment handbook. Self/We/Codex assembly, configuration, and the four experiment domains. Read [GERUON_MANUAL.md](GERUON_MANUAL.md) first for instrument primitives.
>
> 中文版: [EE_MANUAL_CN.md](EE_MANUAL_CN.md)

---

# Practical Guide

## 1. Quick Start — Three-Cavity Self

The repository includes a runnable Self quickstart:

```powershell
git clone https://github.com/JackeyLGene/GBE.git
cd GBE
python docs\quickstart_ee_self.py
```

Expected output:

```text
step  harm     tau_fast  tau_mid  tau_slow
   1   0.0000     0.600    0.600     0.600
  30   0.0356     0.738    0.738     0.710
  60   0.2429     0.740    0.745     0.741
  90   0.7265     0.743    0.748     0.741
 120   0.7507     0.746    0.737     0.738

summary
inputs:       120
harm samples: 120
harm mean:    0.3710
harm max:     0.8499
bias count:   0

OK: 3-cavity Self produced a cross-harm series.
```

Minimal code:

```python
from pathlib import Path
import sys, math
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from geruon import Geruon, BiasField

# 3-cavity Self: three time lenses sharing a BiasField
bias = BiasField(vec_dim=16)
cavities = [
    Geruon(vec_dim=16, memory_cap=24, kappa_tau=0.5,  bias_field=bias),
    Geruon(vec_dim=16, memory_cap=24, kappa_tau=10.0, bias_field=bias),
    Geruon(vec_dim=16, memory_cap=24, kappa_tau=100.0,bias_field=bias),
]

def make_stream(n=120, dim=16):
    for i in range(n):
        block = (i // 30) % 4
        vec = [0.0] * dim
        vec[block] = 1.0
        vec[(block + 1) % dim] = 0.25
        yield vec, f"block_{block}_{i}"

for i, (vec, sig) in enumerate(make_stream()):
    for g in cavities:
        g.process_vec(vec, sig)
    cs = [g.memory.centroid() for g in cavities]
    cs = [c for c in cs if c is not None]
    if len(cs) >= 2:
        harm = sum(
            math.sqrt(sum((cs[a][k]-cs[b][k])**2 for k in range(16)))
            for a in range(len(cs)) for b in range(a+1, len(cs))
        ) / (len(cs) * (len(cs)-1) / 2)
        print(f"step={i}  harm={harm:.4f}")
```

Low harm = three time lenses agree on current structure. High harm = lenses diverge — a structural boundary is passing through.

---

## 2. Self — Multi-Lens Amplifier

### 2.1 Configuration Reference

| Configuration | kappa values | Cavities | Purpose |
|--------------|-------------|----------|---------|
| Standard 3-cavity | 0.5 / 10 / 100 | 3 | General structure detection, CDS-UTR separation |
| Extreme spread | 0.005 / 10 / 5000 | 3 | Transition magnitude detection, AUG discrimination |
| 2-cavity boundary | 0.01 / 500 | 2 | CDS boundary precise localization |
| 2-cavity minimal | 0.005 / 1000 | 2 | Simplest boundary signal |

Changing kappa configuration = changing measurement scale. Not parameter tuning — selecting which timescale the instrument is sensitive to.

### 2.2 Cross-Harm

```python
def cross_harm(cavities, D):
    cs = [g.memory.centroid() for g in cavities]
    cs = [c for c in cs if c is not None]
    if len(cs) < 2: return None
    s, n = 0.0, 0
    for a in range(len(cs)):
        for b in range(a+1, len(cs)):
            s += math.sqrt(sum((cs[a][k]-cs[b][k])**2 for k in range(D)))
            n += 1
    return s / n
```

Low harm = cavities agree on structure. High harm = time-lens divergence — this IS the signal. Harm sequences produce detectable spikes at structural boundaries.

### 2.3 Amplification Gain

Solo Geruon is blind in some domains (WTC: F ~= 0 at all kappa). Self's multiple time lenses amplify faint structure invisible to a single lens.

```
G_disc = |delta_L3| / (3 * cap)
```

L3 = chain frame count. cap = frame capacity. |delta_L3| = max L3 difference across three cavities.

- ECG: G_disc = 0.65 (RR encoding, cap=20)
- WTC: G_disc = 0.52 (frequency-bin encoding, cap=12)
- Cap sweet spot 20-32: too small loses signal, too large dilutes L3 chains

### 2.4 Encoding

Encoding is part of measurement. Principles:
- Encoding must preserve predictive structure
- A single encoding is always lossy — dual-encoding cross-validation
- Harm surviving across encodings = true structure

Common encodings:
- **RR encoding** (ECG): RR intervals + differences + timestamps
- **chroma + IOI** (WTC): 12-dim pitch class + 12-dim inter-onset intervals
- **3-mer** (DNA/RNA): 64-dim trinucleotide frequency
- **fork column** (DNA): 4x4=16-dim multi-species alignment vector

---

## 3. We — Cross-Self Disagreement and Codex Formation

### 3.1 Architecture

```
We:
├── Self_0: 3 cavities (encoding A)
├── Self_1: 3 cavities (encoding B)
├── Self_2: 3 cavities (encoding C)
└── collective: Geruon(kappa=10) <- cross-Self harm collector
```

### 3.2 Harm

Harm is not a moral judgment. It is "another Self's observation modified my frame economy" — the structural trace of cross-Self cognitive conflict. When one Self's residual arrow is routed to another Self, frames created or modified in the target are marked as harm.

### 3.3 Codex Formation Loop

```python
for gen in range(n_generations):
    we = We(n_selves=3)
    for event in stream:
        we.process(event)
    we.finalize()          # harm frames -> collective -> collective_codex
    we.archive()

survivors = archive.survivals(min_gens=2)  # cross-generation survivors
```

### 3.4 Quantum Switches

```python
We(cavity_quantum=False, collective_quantum=False)
```

- `cavity_quantum`: cavity-level quantum branching. Off during deposit phase.
- `collective_quantum`: collective quantum. Optionally on during precipitation analysis.
- Ablation confirmed: classical mode zero signal difference. Off by default.

---

## 4. Codex — Externalized Precipitate

### 4.1 Five-Stage Loop

| Stage | Operation | Status |
|-------|-----------|--------|
| Formation | Cross-Self harm filtering -> stable centroid precipitation | Verified |
| Inscription | Precipitated frames written to collective_codex | Verified |
| Transmission | collective_codex -> next-generation Self's `g.codex` | Verified |
| Confirmation | Inherited entries matching environment -> weight growth | Verified |
| Rejection | Non-matching entries frozen -> not decayed | Verified |

Stage six (**not yet closed**): Codex operation — Self actively queries Codex under stress/noise conditions, inheriting centroids as corrective signals into the frame economy.

### 4.2 Inheritance Path

```
Gen N end:    collective_codex -> self._prev_codex
Gen N+1 start: _prev_codex -> Self codex -> Codex lookup in process_vec()
```

Inheritance goes through Codex, not BiasField. BiasField averages all ancestors together (normalization flattens alpha) — ineffective for generational transmission.

### 4.3 Scaffolding

Codex operation currently exists as scaffolding: manually triggered Codex nearest-neighbor lookup -> soft blend into cavity input -> generational integration. These manual triggers are verification probes for future native mechanisms.

Scaffolding vs shortcuts: shortcuts skip the hard part. Scaffolding builds a temporary bridge to the hard part — verifies the destination exists, then decides whether to build a road.

---

## 5. Experiment Domains

Four domains share the same instrument. Domains are not independent discoveries — they are cross-domain stress tests of a single instrument.

| Domain | Blind to | Core result | Controls | Limitations |
|--------|----------|-------------|----------|-------------|
| WTC | Chord templates, key signatures | Transposition equivariance 100%; 5-stage Codex loop | Cross-key Codex: non-matching entries frozen | Codex operation scaffolded |
| DNA | Codon table, gene annotations | Exon/intron d=-0.97 (n=200) | Shuffle collapses to d=-0.10 | AHSG fork: single gene |
| RNA | AUG motifs, ORF annotations | CDS stop 98-100% within 3 windows | Internal ATG control 98% | CDS start 66%; passive detection |
| UN | Event labels, causal narratives | 2025 disp=0.448, rank 1/79 | P5 ablation; FRED negative control | Prospective (2026-2028); n=79 years |

### 5.1 WTC

Bach Well-Tempered Clavier, 36 pieces. Dual-encoding (chroma + IOI), 10-generation Codex convergence. Zero musicological priors. Transposition equivariance 100%. Codex selection layer is decoupled from frame economy — externalization creates a history parallel to processing efficiency.

### 5.2 DNA

Human TE atlas + 4-species hominid alignments. 3-mer encoding, genomic-order windows. Exon/intron d=-0.97 (n=200). AHSG fork column d=+1.51 (single-gene calibration — AHSG annotated as positive selection by multiple genome scans). Shuffle ablation confirms sequence order is load-bearing. Kappa ablation confirms multi-lens is load-bearing.

### 5.3 RNA

Human TE atlas. Temporal-lens divergence produces cross-harm spikes at UTR/CDS boundaries. CDS stop 98-100% within 3 windows, **parameters unchanged**. CDS start 66% within 3 windows. AUG control 98% — transition magnitude detection, not motif detection. The instrument does not recognize codons. It detects the structural transition of molecular operations entering and exiting the coding regime.

Stop > start is a biological prediction — 3'UTR is a cliff, 5'UTR is a gentle slope.

### 5.4 UN

1946-2025 UN ideal points, 79 years, 193 nations. 2025 displacement=0.448, highest in history. P5 ablation: signal concentrated in major-power layer. FRED negative control: pure economic data judges 2025 as structurally normal. Prospective prediction 2026-2028: P5-aligned system structural collapse. Falsifiable: any two of three indicators satisfied = confirmed.

---

# Principles

## 6. Architecture Physics

### 6.1 Four-Layer Amplification Chain

```
Geruon (depth 0)   -> Single lens. F/wit measurement.
Self (depth 1)     -> Multi-lens * BiasField. cross-harm = inter-lens structural divergence.
                      Solo-blind domains (WTC) produce detectable signal at Self layer.
We (depth 2)       -> Multi-Self * multi-encoding. harm crossing -> Codex formation material.
                      Structure a single Self cannot process precipitates at We layer.
Codex (externalized) -> Precipitate. Cross-generation survival. Forms a selection layer
                      decoupled from frame economy.
```

### 6.2 Inter-layer Communication

Communication between layers is primarily residual/refraction — "what did this cavity fail to absorb?" Not centroid averaging, but the direction of disagreement.

Key principles:
- Cavities keep a fresh eye: reborn each generation, Codex not written into cavity innate memory
- Self is the future Codex operation subject: book queries triggered at Self layer
- We is currently a research tool: cross-Self disagreement detector, not a community subject
- GI recurs at each layer: not a universal constant, but an economic trough. BGM: GI=4 optimal. EE Self (n=3): GI=5 signal-optimal, GI=4 conservative operating point

---

## 7. Cross-Harm — Multi-Lens Structural Divergence

### 7.1 Physical Picture

Three cavities are like three lenses of different focal lengths aimed at the same stream. The fast lens (kappa=0.005) adapts instantly to new patterns — its centroid displaces immediately after structural change. The slow lens (kappa=5000) barely moves — its centroid retains memory of the previous structure.

When the stream's structure is stable, the three lens centroids converge to the same position -> harm low. When the stream crosses a structural boundary, the fast lens has already moved while the slow lens hasn't -> harm spike.

This is temporal-lens divergence — the mechanism by which the instrument detects structural boundaries. The same mechanism detects tonal skeleton transitions in WTC, distinguishes exons from introns in DNA, locates CDS boundaries in RNA, and detects international system displacement in UN.

### 7.2 2-cavity vs 3-cavity

2-cavity (fast+slow) gives the cleanest boundary position — only one dimension of divergence. 3-cavity (fast+mid+slow) captures richer divergence structure — the middle lens provides an additional reference, making it more sensitive to transition magnitude.

In RNA experiments, 2-cavity CDS start localization was more precise (median -0.9 window). 3-cavity extreme spread discriminated AUG magnitude better (98% vs 78%).

---

## 8. Information Economics

### 8.1 BiasField Attention Economics

BiasField is a shared gradient field — the accumulated gradient of centroid deposits from multiple cavities. `deposit(vec, weight)` accumulates; `blend_into(vec, weight)` blends the field direction into new input. The field is continuous — it does not seek a "nearest neighbor"; it imposes a directional bias.

Economic meaning: **attention allocation**. Strong-field dimensions receive more modulation weight — the system allocates more attention to "dimensions that once had structure." Weak-field dimensions are ignored. This is not programmed attention — it is weight asymmetry naturally formed by deposited gradients.

BiasField vs Codex division of labor:
- Codex = discrete precise lookup. Known symbols match directly.
- BiasField = continuous gradient bias. Nameless directional influence — "GABA mode."

### 8.2 BiasField Game Theory

When multiple cavities share a BiasField, the field is no longer a neutral information channel — it becomes an implicit game space.

**Strategy space.** Each cavity's strategy is the centroid it deposits into the field — its estimate of "what the current structure is." Cavities do not directly know other cavities' states — they only feel their accumulated influence through the field gradient.

**Payoff.** A cavity's payoff is merge success — how well its input matches its own frame economy. If the field bias helps the cavity find matches faster -> positive payoff. If the field bias pulls the cavity away from its own structural region -> negative payoff.

**Equilibrium dynamics.** High-weight, frequently-merging cavities deposit more and with greater weight — they dominate the field gradient. Low-weight cavities are pulled by the field gradient, their centroids dragged toward the mainstream direction. This is not "consensus" — it is the field's attention allocation naturally converging to the region of highest information density.

**Three findings from multi-cavity game theory (M15):**

1. **Attention concentration.** When multiple cavities process different encodings of the same stream, the field gradient rapidly concentrates on structural dimensions shared across encodings. Encoding-specific dimensions are diluted — the field automatically separates signal (survives cross-encoding) from noise (encoding-specific).
2. **Small cavities covered by large ones.** Low-weight cavity centroids are pulled by the field to positions far from their own data — they lose expressive rights over their own structure in the game. This is not a bug — it is precisely the source of "cross-Self unabsorbable residuals" in Codex formation: when a small Self's structure is inconsistent with the dominant field direction, it is suppressed by field attention allocation and becomes residual harm.
3. **Field cliff effect.** When the field gradient accumulates to critical density in some direction, it exerts non-negligible bias on ALL cavities — even when that direction is inconsistent with some cavities' data. This is the BiasField-layer counterpart of BGM's conf_threshold cliff: the field's attention allocation is not linear — it has a phase transition point beyond which the field shifts from "suggestion" to "command."

**Connection to We-layer harm.** We-layer harm is essentially the output of the multi-cavity BiasField game. When a cavity is presumed by the field gradient to be in some region, but its actual input points elsewhere — this irreconcilable difference is harm. Harm is not error — it is the inevitable byproduct of attention allocation in the game. Codex formation extracts cross-generationally surviving structure from these harms.

### 8.3 Landauer-Godel Bill

Landauer's principle (Landauer, 1961): every irreversible information operation dissipates at least kT ln 2. The frame economy has three classes of irreversible operations:

| Operation | Irreversibility | Bill |
|-----------|----------------|------|
| Merge | Two frames become one — old centroid permanently lost | O(1) per merge |
| Prune | Frame discarded — accumulated vec information permanently lost | O(weight) per frame |
| Precipitate | Frame written to Codex — immutable thereafter | O(1) per precipitation |

`landauer_skips` counts prediction operations skipped during LOCKED — the system proactively shuts down the most expensive self-referential operations to cap the bill.

### 8.4 Economics of Tau Convergence

Tau converges to ~0.74-0.75 across all domains and depths. This is not set — it is the economic equilibrium the frame economy finds between merge pressure and differentiation pressure. When merging is too easy (tau low), the system over-generalizes — structure is lost. When merging is too hard (tau high), the system over-differentiates — frame economy congests, stress accumulates. 0.74 is the equilibrium that maximizes information rate.

### 8.5 Economic Status of GI

GI=4 was discovered in BGM's kappa_tau parameter scan as Pareto-optimal for single-GEME+G0 architecture.

EE's CALIB-GI scan produced more refined results for the Self architecture:

| n_cav | GI_opt | GI upper | Notes |
|-------|--------|----------|-------|
| 2 | 1 | ~2 | Two cavities need no long cycle |
| **3** | **5** | **5** | GI=4 conservative operating point (0.0890 vs GI=5 0.0950) |
| 5 | 1 | ~3 | More cavities need more frequent sync |
| 8 | 3 | ~5 | GI*(n-1) is not constant |

**Key finding:** GI=4 is optimal for BGM architecture, not for EE Self architecture. For n=3 standard Self, GI=5 is signal-optimal; GI=4 retains ~94% signal with one notch of safety margin. The difference arises from different information economics — BGM's G0 is an external observer, EE's Self is bidirectional inter-cavity communication. Different game structures produce different optimal communication rhythms.

Current recommendation: n=3 Self with standard lenses (0.5/10/100) uses GI=5 as signal calibration point, GI=4 as conservative operating point.

### 8.6 The P/NP Boundary in Operational Form

Aaronson (2011) proposed that deep questions about mind and knowledge may depend on computational complexity rather than abstract computability.

The frame economy provides an operational form. Self-referential operations create an identity search problem — the system must find "the frame for that pattern I just processed." The cost of this search is endogenously regulated by tau. When tau is low, merge thresholds are wide — search is easy, cost is low. When tau is high, merge thresholds are narrow — search is hard, cost grows nonlinearly. At LOCKED, `process_prediction()` is skipped — the system proactively caps the most expensive operation.

The P vs NP boundary here is not a theorem to be proved — it is a cost endogenously regulated by tau. The system does not "solve" NP problems in polynomial time; it regulates self-reference depth under Landauer-bill constraints so that it never crosses the economically infeasible boundary.

---

## 9. Expression-Action Spectrum

The instrument's applicability to different data types is determined by data structure type — not domain category:

| Data type | Definition | Example | Instrument sensitivity |
|-----------|-----------|---------|----------------------|
| **Decision** | Action as data | UN votes, MIDI note-on, DNA bases | Strongest |
| **Action** | Entity choice records | NASDAQ volume direction | Moderate |
| **Expression** | Process trace | CPI, price indices, raw ECG voltage | Weak |

The instrument needs relational structure in the input. Decision data natively carries inter-entity structural relations — uncompressed, not downsampled. Expression data only records process outputs — the relational structure is not in the data. This is not an instrument defect; it is a boundary of information itself.

ECG lesson: raw voltage is Expression — of six encodings tested, only one produced signal. Encoding is part of measurement.

---

## 10. Scaffolding Method

Every architectural layer's mechanism was first verified through scaffolding — temporarily injecting what the architecture should eventually do natively — then dismantled, replaced by native mechanism.

- L4 self_observation: originally explicit steps (108 self_observe calls) -> dismantled
- doubt condition: originally pengshu's fifth condition -> M2 removed
- 27-dim formula alphabet: originally hardcoded vector space -> dismantled to configurable vec_dim
- Codex operation: currently scaffolded — manual Codex lookup + soft blend -> awaiting native

Scaffolding is not a shortcut. A shortcut skips the hard part. Scaffolding builds a temporary bridge to the hard part — verifies the destination exists, then decides whether to build a road.

---

## 11. Reproducibility Checklist

1. **Fair coin baseline** — same D, same cap, same kappa sweep
2. **Shuffled control** — destroy sequential structure, preserve component statistics
3. **Kappa ablation** — disable multi-lens, reproduce with single kappa -> confirm multi-kappa is load-bearing
4. **Multi-seed** — minimum 3 seeds (42, 123, 456)
5. **structon calibration** — minimum detectable displacement at current (D, cap, kappa)
6. **Three-step threshold** — report |error| <= 2 / <= 3 / <= 5 simultaneously
7. **Parameter freeze** — no geruon.py modifications within one batch; parameters fixed or swept and reported
8. **Code archive** — experiment scripts frozen in `experiments/` by domain

Dependencies: core instrument Python 3.8+ stdlib only; data processing `pandas`/`numpy`/`pyarrow`; RNA bigWig requires `pybigtools` (Windows).

---

*EE Manual v2.0. Practical: Quick Start -> Self -> We -> Codex -> Experiment Domains. Principles: Architecture Physics -> Cross-Harm -> Information Economics -> Expression-Action -> Scaffolding -> Reproducibility. Instrument primitives: [GERUON_MANUAL.md](GERUON_MANUAL.md).*
