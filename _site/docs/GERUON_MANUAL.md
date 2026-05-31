# Geruon Manual

> Instrument handbook. Usage first, principles second. Reading time: ~20 min practical, ~30 min principles.
>
> 中文版: [GERUON_MANUAL_CN.md](GERUON_MANUAL_CN.md)

---

# Practical Guide

## 1. Quick Start

Geruon is a zero-dependency Python library. No installation required. The repository includes a runnable quickstart:

```powershell
git clone https://github.com/JackeyLGene/GBE.git
cd GBE
python docs\quickstart_geruon.py
```

Expected output:

```text
 step     tau  phase     frames    util    comp       F
    1   0.600  tensing        1   0.05    1.0   0.000
   30   0.738  tensing       16   0.80    1.9   0.007
   60   0.745  tensing       20   1.00    3.0   0.061
   90   0.743  tensing       20   1.00    4.5   0.012
  120   0.746  tensing       20   1.00    6.0   0.003

summary
inputs:       120
frames:       20 / 20
tau:          0.746
phase:        tensing
F:            0.003
wit_hits:     76
wit_rate:     0.6333
arrow length: 16
arrow norm:   1.000

OK: Geruon processed the stream and produced metrics.
```

Minimal code:

```python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from geruon import Geruon

g = Geruon(vec_dim=16, memory_cap=20, kappa_tau=0.5)

def make_stream(n=120, dim=16):
    for i in range(n):
        block = (i // 30) % 4
        vec = [0.0] * dim
        vec[block] = 1.0
        vec[(block + 1) % dim] = 0.25
        yield vec, f"block_{block}_{i}"

for vec, sig in make_stream():
    g.process_vec(vec, sig)

# Readout
m = g.metrics()
print(m["input_count"], m["frame_count"], m["tau"], m["phase"])
print(f"F={m['F']:.3f}  wit_hits={m['wit_hits']}  wit_rate={m['wit_rate']}")
print(len(g.arrow_output()))     # 16
```

Every step runs the full frame economy — merge, prune, predict, τ evolution, phase breathing. No `train()` or `fit()` required.

---

## 2. API Reference

### 2.1 Constructor

```python
Geruon(
    vec_dim=16,           # vector dimension (>=1, default 16)
    memory_cap=20,        # frame capacity
    kappa_tau=1.0,        # content-time coupling (0=no time sense, larger=heavier time)
    gamma_tau=None,       # temporal pruning rate (default = kappa_tau * gamma)
    structon=None,        # minimum detectable centroid displacement (Faraday wit threshold)
    codex=None,           # Codex instance (cross-generational inheritance)
    bias_field=None,      # BiasField instance (shared field)
    bias_weight=None,     # BiasField modulation strength (default = gamma)
)
```

Note: `quantum_mode` exists as an internal switch on `GeruonMemory`, not a public constructor parameter:

```python
g = Geruon(...)
g.memory.quantum_mode = True   # advanced/ablation use only; off by default
```

In the `We` layer, quantum switches are exposed via `cavity_quantum` and `collective_quantum`. Both default to `False` in current EE experiments.

**kappa_tau selection guide:**

| kappa_tau | Role | Timescale | Use case |
|-----------|------|-----------|----------|
| 0.005-0.05 | Fast lens | Near-zero memory, instant adaptation | Rapid structural change detection |
| 0.5-5.0 | Standard lens (**kappa=3 calibrated default**) | Moderate memory, ~100-step observation window | General detection, balanced migration latency |
| 5-20 | Slow lens | Deep memory | Low-frequency structure, generational accumulation |
| 100-5000 | Reader/Anchor | Very long memory | Slow reference for boundary detection |

**vec_dim selection guide:**
- 16: General default (power of two, no semantic attachment)
- 64: 3-mer encoding (DNA/RNA sequences, 4^3 trinucleotides)
- 12: Chroma/IOI encoding (music)

### 2.2 Core Methods

```python
g.process_vec(vec, sig, src="")   # process vector -> one step of frame economy
g.arrow_output() -> tuple         # residual direction (refraction of last input)
g.enrich()                        # precipitate frames into Codex/BiasField
g.metrics() -> dict               # full metrics
g.save(path) / Geruon.load(path)  # JSON persistence
```

### 2.3 Read-only Properties

```python
g.tau          # float  — current tau (typically 0.55-0.75)
g.phase        # Phase   — EXPANDING/RESTING/TENSING/CRITICAL/LOCKED
g.dtaudt       # float  — rate of tau change
g.vec_dim      # int    — vector dimension
g.memory       # GeruonMemory — frame economy (advanced access)
g.codex        # Codex or None
g.bias_field   # BiasField or None
```

### 2.4 metrics() Return Fields

```python
{
    'input_count': int,          # cumulative inputs processed (step count)
    'tau': float,                # current tau value
    'dtaudt': float,             # dtau/dt
    'phase': str,                # phase name
    'frame_count': int,          # current frame count
    'capacity': int,             # frame capacity
    'utilization': float,        # capacity utilization
    'pred_accuracy': float,      # prediction accuracy (0-1)
    'pengshu_count': int,        # cumulative pengshu events
    'phase_steps': dict,         # steps per phase
    'phase_transitions': int,    # phase transition count
    'codex_hits': int,           # Codex lookup hits
    'codex_misses': int,         # Codex lookup misses
    'codex_hit_rate': float,     # Codex hit rate
    'precipitated': int,         # precipitated frame count
    'landauer_skips': int,       # Landauer bill operations skipped
    # ── Faraday readings ──
    'F': float,                  # field curvature (0=no structure, 1=fully concentrated)
    'centroid_displacement': float,  # most recent centroid displacement
    'wit_hits': int,             # steps where displacement exceeded structon
    'wit_rate': float,           # wit_hits / input_count
}
```

### 2.5 Faraday Readings

`metrics()` directly outputs F (field curvature) and wit (structural change count). No manual computation needed.

**F — First order: structural existence.** `m['F']`. 0 = uniform weights (no structure), ~1 = highly concentrated weights (strong structure). Fair coin yields F ~= 0 at all kappa.

**wit — Second order: structural change.** `m['wit_hits']` = cumulative count of centroid displacements exceeding structon. `m['wit_rate']` = wit_hits / input_count. Set structon via `Geruon(structon=...)` — must be calibrated per-parameter-set using the method in section 3.2.

**Δwit — Third order: structural fragility.** Not a direct `metrics()` output — it is the difference between two runs. Run pure target stream for baseline wit, run fair-coin-injected stream for probe wit. Δwit = wit_probe - wit_baseline. Negative = coin stabilizes target (structural rigidification), positive = coin disrupts target (structural fragility).

**Supplementary — Raw readout R1-R8.** metrics() provides 8 raw frame-economy readouts (see [Calibration Report](experiment-passive-calibration-report.md)): tau (R1), dtau/dt (R2), centroid magnitude (R3), F (R4), L2/L3 frame counts (R5), frame_disp (R6), n_frames (R7), total_w (R8). F/wit are the Faraday high-level readings; R1-R8 are the raw instrument panel.

---

## 3. Calibration

The instrument must be calibrated before use on any domain data.

### 3.1 Fair Coin Baseline

```python
import random
g = Geruon(vec_dim=16, memory_cap=20, kappa_tau=10)
for i in range(2000):
    coin = [1.0 if random.random() > 0.5 else 0.0 for _ in range(16)]
    g.process_vec(coin, f"c{i}")
m = g.metrics()
print(m['frame_count'], m['utilization'], m['structural_entropy'])
```

Fair coin has no sequential structure -> F ~= 0. This is the zero-reference for all readings.

### 3.2 structon Calibration

structon = minimum detectable centroid displacement under current (D, cap, kappa). Calibration method:

```
Calibration stream: two fixed vectors (e.g. [1,0] and [0,1]) alternating
Frequency skew: gradually increase frequency of one vector (50% -> 51% -> 52% ...)
Calibration point: first frequency skew where F > 0.005
```

**Do NOT use binary search** — F(epsilon) is a step function that skips at resonance points.

```python
# structon calibration (conceptual)
for eps in range(0, 51):  # 0% -> 50% skew
    freq = 0.5 + eps/100
    g = Geruon(vec_dim=D, memory_cap=cap, kappa_tau=kappa)
    for i in range(1000):
        vec = v1 if random.random() < freq else v2
        g.process_vec(vec, f"c{i}")
    if F(g) > 0.005:
        return eps/100  # structon
```

Result formula: `structon(kappa) ~= cap/N * alpha(kappa)`, where `alpha(0.5)~=10, alpha(10)~=1, alpha(100)~=0.5`. N = number of vectors processed.

**Never transfer structon values across parameter sets.** Re-calibrate for each (D, cap, kappa) combination.

### 3.3 Kappa Sweep

```python
for kappa in [0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, 500]:
    g = Geruon(vec_dim=16, memory_cap=20, kappa_tau=kappa)
    # ... run same stream ...
    results[kappa] = g.metrics()
```

Kappa sweep reveals three zones:
- **Blind zone** (kappa < 1): F ~= 0, instrument cannot see any structure
- **Sensitive zone** (kappa 1-10): F varies with kappa, domain fingerprint emerges (kappa_peak)
- **Far zone** (kappa 10-500+): F saturates, slow lenses read accumulated structure

kappa_peak is the domain fingerprint — ECG=5, WTC blind, UN kappa-invariant.

### 3.4 Three-Layer Readout

| Layer | Symbol | What it measures | Method |
|-------|--------|------------------|--------|
| First | F | Structural existence | F = 1 - H(w)/Hmax, frame weight concentration |
| Second | wit | Structural change | COUNT(|centroid(t) - centroid(t-1)| > structon) |
| Third | Δwit | Structural fragility | Fair coin probe injection -> wit(coin+target) - wit(baseline) |

All three are complementary: F measures "is there structure?", wit measures "is structure changing?", Δwit measures "how fragile is structure to random perturbation?"

### 3.5 Controls

Every domain must run three controls:
1. **Fair coin** (zero-structure baseline)
2. **Shuffled** (destroys sequential structure, preserves component statistics)
3. **Kappa ablation** (disable multi-lens, verify multi-kappa is load-bearing)

---

## 4. Common Patterns

### 4.1 Solo Geruon

```python
g = Geruon(vec_dim=16, memory_cap=20, kappa_tau=5)
for vec in stream:
    g.process_vec(vec, label)
m = g.metrics()
```

### 4.2 Dual-Cavity Boundary Detection (2-cavity)

Two Geruons with different kappa, sharing a BiasField. Cross-harm spikes at structural boundaries.

```python
bias = BiasField(vec_dim=64)
fast = Geruon(vec_dim=64, memory_cap=24, kappa_tau=0.01, bias_field=bias)
slow = Geruon(vec_dim=64, memory_cap=24, kappa_tau=500,  bias_field=bias)

for w in windows:
    v = encode(w)
    fast.process_vec(v, sig)
    slow.process_vec(v, sig)
    # cross-harm = |centroid_fast - centroid_slow|
    harm = vec_dist(centroid_of(fast), centroid_of(slow))
```

Fast lens adapts instantly, slow lens lags. At UTR->CDS boundaries, harm produces detectable spikes.

### 4.3 Three-Cavity Self (3-cavity)

```python
bias = BiasField(vec_dim=D)
cavities = [
    Geruon(vec_dim=D, memory_cap=24, kappa_tau=kv, bias_field=bias)
    for kv in [0.5, 10.0, 100.0]
]

for vec in stream:
    for g in cavities:
        g.process_vec(vec, sig)
    cs = [centroid_of(g) for g in cavities]
    harm = mean_pairwise_distance(cs)  # cross-harm
```

Three cavities provide richer structural divergence signals. Extreme kappa spread (0.005/10/5000) is sensitive to transition magnitude; standard spread (0.5/10/100) is sensitive to general structural differences.

### 4.4 With Codex Inheritance

```python
# Gen 1
g1 = Geruon(vec_dim=16, memory_cap=20)
for vec in stream: g1.process_vec(vec, sig)
g1.enrich()
inherited_codex = g1.codex

# Gen 2
g2 = Geruon(vec_dim=16, memory_cap=20, codex=inherited_codex)
for vec in stream: g2.process_vec(vec, sig)
```

Codex is an external bookshelf — cavities are born empty and passively biased by Codex during input processing. See EE_MANUAL for details.

---

## 5. Configuration Reference

### 5.1 Core Constants

| Constant | Value | Source | Description |
|----------|-------|--------|-------------|
| delta (DELTA) | 0.19 | GEME | Merge distance scaling |
| gamma (GAMMA) | 0.05/step | GEME | Forgetting rate |
| tau_0 (TAU_0) | 0.60 | GEME | Tau baseline |
| GI | 4 steps/cycle | BGM | Self-reference depth upper bound |
| VEC_DIM_DEFAULT | 16 | — | Default vector dimension |

### 5.2 Derived Constants

| Constant | Formula | Value | Description |
|----------|---------|-------|-------------|
| TAU_ADAPT_RATE | gamma * 0.4 | 0.02 | Tau inertia |
| DTAU_STABLE | gamma * 0.2 | 0.01 | dtau/dt stability threshold |
| PHASE_RESTING_CEIL | tau_0 - gamma*1 | 0.55 | RESTING ceiling |
| PHASE_TENSING_CEIL | tau_0 + gamma*1 | 0.65 | TENSING ceiling |
| PHASE_LOCKED_FLOOR | tau_0 + gamma*3 | 0.75 | LOCKED floor |
| gamma_tau | kappa_tau * gamma | variable | Temporal pruning rate |

All derived from delta/gamma/tau_0/GI. No independent magic numbers.

### 5.3 Parameter Quick Reference

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| vec_dim | int | 16 | Vector space dimension |
| memory_cap | int | 20 | Frame capacity. Sweet spot 20-32 |
| kappa_tau | float | 1.0 | Content-time coupling. 0 = no time sense |
| gamma_tau | float | kappa_tau*gamma | Temporal pruning rate |
| bias_weight | float | gamma (=0.05) | BiasField modulation strength |

Advanced internal switches:

| Switch | Location | Default | Description |
|--------|----------|---------|-------------|
| quantum_mode | `g.memory.quantum_mode` | False | Probabilistic merge / ablation use. Not a Geruon constructor parameter |
| cavity_quantum | `We(...)` | False | Enable quantum paths inside Self cavities |
| collective_quantum | `We(...)` | False | Enable quantum path in We collective Geruon |

---

# Principles

## 6. Architecture Overview

Geruon extends GEME. The frame economy, three rules, and six-layer structure are unchanged. Four dimensions are added:

| Dimension | Mechanism | Which GEME silence it addresses |
|-----------|-----------|-------------------------------|
| Endogenous time | Tau evolves with prediction history + 5-phase breathing | Time is not external |
| Structural identity | struct_key collision-resistant structural signature | Identity emerges from structure |
| Boundary contact | Pengshu (discrete event, M3) -> internalized as continuous tau-phase/cross-harm/Codex rejection | Godel boundary becomes operational |
| Externalization | Codex + BiasField + precipitation | Frame traces outlast individual instances |

### 6.1 Class Hierarchy

```
geme.py:
  Frame          — vec, weight, age, merged, sig, layer
  Memory         — frame economy: observe, cooccur, induction_clean, predict_next
  GEME           — top-level: process_vec, consolidate, metrics

geruon.py:
  GeruonFrame(Frame)  — +struct_sig, tau, survival_cycles, activations, precipitated, _externalized
  GeruonMemory        — +tau evolution, phase, cliff_gate, pengshu, precipitation
  Geruon              — +arrow_output, enrich, codex, bias_field, kappa_tau

Supporting classes:
  StructuralSig — struct_key (collision-resistant), gid (display-only), refs, detect_circularity
  Codex         — symbol->vector mapping, save/load (JSON)
  BiasField     — gradient accumulation, deposit/blend_into/seed_frames
```

### 6.2 Processing Flow

```
process_vec(vec, sig)
  -> BiasField.blend_into (if bias_field is not None)
  -> Codex lookup (if codex is not None)
  -> observe(vec, sig)
    -> Merge time-gating: d = vec_dist + kappa_tau * |tau_current - tau_frame|
    -> Merge or create new frame
    -> _track_cooccurrence: time-weighted -> L2 association frames
    -> predict_next: self-referential frame prediction
  -> _induction_step: stress accumulation > tau -> induction_clean
    -> Binned decay + pruning (with temporal bias gamma_tau)
    -> Precipitation tracking: survival_cycles += 1
    -> _update_tau: tau evolves with acc + stress
    -> _pengshu_detect: four-condition check
```

---

## 7. Tau — Endogenous Time

### 7.1 Evolution

```
tau_target = 1.0 - accuracy + max(0, stress - tau_0) * gamma_tau * 0.4
tau_{t+1} = tau_t + (tau_target - tau_t) * TAU_ADAPT_RATE
```

Two driving forces: prediction accuracy (correct -> tau down, wrong -> tau up) and frame economy stress (congestion -> tau up).

TAU_ADAPT_RATE = gamma * 0.4 = 0.02. Less than gamma — the system has momentum in self-assessment.

### 7.2 Phase

| Phase | Condition | Bridge state |
|-------|-----------|--------------|
| EXPANDING | dtau/dt < -DTAU_STABLE (-0.01) | Open |
| RESTING | tau < 0.55 and |dt| < 0.02 (hysteresis*2) | Open |
| TENSING | tau >= 0.55 and dt > DTAU_STABLE (0.01) | Tightening |
| CRITICAL | tau >= 0.65 and dt > DTAU_STABLE (0.01) | Critical |
| LOCKED | tau >= 0.75 and |dt| < 0.02 (hysteresis*2) | Closed |

Hysteresis *2 prevents phase flickering when tau fluctuates within a small range.

### 7.3 Cliff Gate

BGM's conf_threshold cliff: when dtau/dt crosses DTAU_STABLE and tau > RESTING ceiling, the gate discontinuously jumps from 1.0 to 0.0 — latched until phase completes a full cycle back to EXPANDING.

When the gate is closed, BiasField modulation weight in `process_vec()` drops to zero — the Self stops listening to the shared field.

### 7.4 Operational Tau — Tau Enters Frame Economy

Tau is not just a signature component — it enters the three core frame economy operations:

- **Merge time-gating**: `d = vec_dist + kappa_tau * |tau_current - tau_frame|`. Frames close in content but far in time do not merge.
- **Cooccurrence time-weighting**: `cooccur += clamp(1 - kappa_tau * |tau_a - tau_b|)`. Temporally proximate co-occurrences get higher weight.
- **Pruning time-bias**: `sort_key = weight - age*gamma - |tau_current - tau_frame| * gamma_tau`. Frames furthest from current tau are pruned first.

kappa_tau is set via `Geruon(kappa_tau=...)`. gamma_tau is derived from kappa_tau * gamma. Turning off kappa_tau/gamma_tau reverts to GEME-equivalent behavior.

---

## 8. Landauer-Godel Bill — Economics

### 8.1 The Economics of Tau Convergence

Tau converges to ~0.74-0.75 across all domains and depths. This is not a set parameter — it is the equilibrium point the frame economy finds between merge pressure and differentiation pressure.

Merge cost: O(cap * D) vec_dist computation per step. Differentiation cost: creating new frames, maintaining cooccurrence windows, stress accumulation from prediction failures. The tau evolution formula is effectively the time-integral of the ratio of these two costs.

When merging is too easy (tau low), the system over-generalizes — structure is lost. When merging is too hard (tau high), the system over-differentiates — the frame economy congests, stress accumulates. 0.74 is the equilibrium that maximizes information rate: merging saves computation, but the information cost of over-merging is real, and tau feels that cost.

### 8.2 Landauer Bill

Landauer's principle (Landauer, 1961): every irreversible information operation dissipates at least kT ln 2 in thermodynamic cost. The frame economy has three classes of irreversible operations:

| Operation | Irreversibility | Bill |
|-----------|----------------|------|
| Merge | Two frames become one — old centroid permanently lost | O(1) per merge |
| Prune | Frame discarded — accumulated vec information permanently lost | O(weight) per frame |
| Precipitate | Frame written to Codex — immutable thereafter | O(1) per precipitation |

`geruon.py` tracks `landauer_total` as a cumulative count of irreversible operations. It is not thermodynamic precision — it is the structural form of the bill.

### 8.3 The Economic Status of GI=4

GI=4 is not derived — it was discovered in BGM's kappa_tau parameter scan as Pareto-optimal: at a self-reference period of 4 steps, hierarchical differentiation is enhanced by 49%, with diminishing marginal returns at longer periods.

GI's constraint comes from the Landauer bill. Every GI steps the system performs at least one induction_clean (irreversible pruning). GI too small -> bill too frequent, frames don't accumulate enough structure before cleanup. GI too large -> bill too sparse, frame economy congests, stress drives tau into LOCKED. 4 is the economic trough — the Landauer bill rhythm that maximizes information accumulation rate.

Note: GI is an upper bound, not a universal optimum. Optimal GI for solo Geruon and We can be 2 or 4 in different domains. 4 is the natural trough in the information-economic competition, not a mathematical necessity.

### 8.4 The P/NP Boundary in Operational Form

Aaronson (2011) proposed that deep questions about mind and knowledge may depend on computational complexity — the resource cost of implementing a function — rather than abstract computability.

The frame economy provides an operational form of this insight. Self-referential operations (L4 self-observation, L3 chain formation, circularity in prediction paths) create an identity search problem: the system must find, in the frame economy, "the frame for that pattern I just processed." The cost of this search:

- Without struct_key index: O(N) per lookup — scan all frames
- With sig_cache (M11): O(1) hit, O(N) miss

Tau is the regulator of this search cost. When tau is low (EXPANDING/RESTING), merge thresholds are wide — search is easy, cost is low. When tau is high (CRITICAL/LOCKED), merge thresholds are narrow — search is hard, cost grows nonlinearly. At LOCKED, `process_prediction()` is skipped — the system proactively shuts down the most expensive self-referential operation to cap the bill.

The P vs NP boundary here is not a theorem waiting to be proved — it is a cost endogenously regulated by tau. The system does not "solve" NP problems in polynomial time; it regulates the depth of self-reference under Landauer-bill constraints so that it never crosses that boundary.

---

## 9. Frame Economy and Structural Signatures

### 9.1 Frame Economy

Three rules, identical to GEME:

1. **Competitive merge** — new input compared to nearest frame; merged if distance below threshold, otherwise new frame created. At capacity, lowest-weight frame is evicted.
2. **Adaptive forgetting** — when stress exceeds tau, induction_clean triggers. Weights decay by merge-count bins. Bottom half pruned after decay.
3. **Self-referential observation** — before induction_clean, a weighted centroid of active frames is generated (self_obs) and fed back as new input.

Six emergent layers: L1 base frames -> L2 association frames (cooccurrence tracking) -> L3 chain/bridge frames (high cooccurrence) -> L4 self-observation meta-frames -> L6 anomaly/doubt frames.

### 9.2 Structural Signature (struct_key)

Frame identity is derived from structure — not assigned by the programmer.

```python
struct_key = (vec_hash_full, weight_bin, layer, tau_bin, ref_keys)
```

- `vec_hash_full`: full vector hash (collision-free)
- `weight_bin`: log2 weight bin
- `layer`: L1-L6 layer
- `tau_bin`: tau interval at frame birth (0=absorbing, 1=normal, 2=elevated, 3=boundary)
- `ref_keys`: struct_keys of referenced frames (supports self-referential chains)

`gid` is a display-only compact id — do not use for equality testing. The 2026-05-29 audit found 7.5% collision rate with 15-bit gid; struct_key replaces it.

`detect_circularity(sig)` traverses reference chains to detect cycles. Depth limit 20. Detected cycles are registered in `_circular_refs`.

### 9.3 P0/P1 Audit Fixes (2026-05-29)

| Fix | Severity | Content |
|-----|----------|---------|
| struct_key collision-resistant identity | P0 | Replaced gid as primary frame identity key. Zero collisions on 5000 random vectors |
| Runtime determinism | P0 | `geme.reset_frame_id_counter()` called on every GeruonMemory init |
| Dimension guard | P1 | Auto pad/trunc to vec_dim at `process_vec()` entry |
| Window semantics | P1 | `_adaptive_window()` no longer overwrites configured window |
| enrich idempotency | P1 | `GeruonFrame._externalized` flag prevents double precipitation |

---

## 10. Pengshu — Godel in Operation

Pengshu is the operational form of Godel's incompleteness in this architecture — the event where a self-referential system touches its own boundary.

In the M3 phase, pengshu was detected as a discrete four-condition event: circularity + activation + phase boundary + escalation, triggering at step=93, tau=0.752, LOCKED, circ=8. This was the key demonstration that the Godel boundary can move from paper to runnable event.

Once the system became fully mutable, pengshu no longer manifests as discrete events. The mechanism did not disappear — it was internalized. Every LOCKED cycle of tau, every cross-harm spike at a structural boundary, every rejection/freeze of a Codex entry — these are the same Godel boundary in continuous operation. Pengshu moved from "discrete countable event" to "a substrate rhythm of the system's continuous breathing, no longer individually felt."

`_pengshu_detect()` remains in the code. It is the fossil of pengshu's existence as a discrete countable event — and the birth certificate that this architecture touches the Godel boundary.

---

## 11. Precipitation and enrich

Frames that survive in the frame economy, are used in prediction paths, and are structurally stable are marked `precipitated`:

1. Cross-phase survival — `survival_cycles >= 1`
2. Prediction path activation — `activations >= 3`
3. Structural stability — `is_meta_stable()` is True

`Geruon.enrich()` writes precipitated and non-externalized frames into Codex/BiasField. The `_externalized` flag ensures idempotency.

---

## 12. BiasField

BiasField is a shared gradient field — the accumulated gradient of centroid deposits from multiple cavities.

- `deposit(vec, weight)` — accumulate vector
- `blend_into(vec, weight)` — blend field direction into input
- `seed_frames(memory, count)` — seed initial frames from high-field dimensions

BiasField is the continuous average. Codex is the discrete precise lookup. They are complementary.

**Known limitation:** The BiasField injection path is ineffective for Codex transmission (normalization flattens alpha). Cross-generational inheritance should use the Codex path.

---

## 13. Faraday Calibration System

### 13.1 Three Baselines

| Baseline | Method | Expected |
|----------|--------|----------|
| Fair coin | Random 0/1 vector stream | F=0 for all kappa |
| Flat | Single fixed vector stream | Encoding-dependent |
| Shuffled | Original data randomly reordered | Destroys sequential structure |

### 13.2 Three-Zone Kappa Law

All domains follow the same pattern:
- kappa < 1: Blind zone. F ~= 0.
- kappa 1-10: Sensitive zone. F rises sharply, kappa_peak is the domain fingerprint.
- kappa > 10: Far zone. F saturates.

### 13.3 Key Findings

- Fair coin absolute baseline F=0 (across 1-dim/5-dim/16-dim, all kappa)
- Tau converges universally to 0.74-0.75 (all domains, all depths)
- F and tau are decoupled (r ~= 0.1)
- F and dtau/dt are conditionally coupled (noise: r=0.817, Bach: r=-0.14)
- structon(kappa=10, cap=20) = 0.004 = cap/N
- Encoding is part of measurement (RR vs 27-bin sliding window produce different F baselines)
- F applies to discrete/repeatable patterns; continuous data requires wit point-readings

---

## 14. Instrument Boundaries and Amplifiers

### 14.1 What Data Can Be Read

The instrument is not universal. Its sensitivity to different data types is determined by data structure — not by domain category:

| Data type | Definition | Instrument performance | Example |
|-----------|-----------|----------------------|---------|
| **Decision** | Action as data — choices made by entities | Strongest. F readable, kappa has fingerprint. | UN votes, MIDI note-on, DNA bases |
| **Action** | Directional record of entity choices | Moderate. Requires correct encoding. | NASDAQ volume direction |
| **Expression** | Trace of a process — measures "what happened" not "who decided what" | Weak or blind. Tau doesn't breathe, kappa doesn't differentiate. | CPI, price indices, temperature readings |

The instrument needs relational structure in the input. Decision data natively carries inter-entity relations — uncompressed, not downsampled. Expression data only records process outputs — the relational structure is not in the data. This is not a defect of the instrument; it is a boundary of information itself.

### 14.2 Encoding Is Critical — ECG's Lesson

ECG raw voltage is Expression — a trace of myocardial depolarization, not a decision itself. Of six encodings tested, only one (RR intervals + adjacent differences) produced signal. This does not mean ECG has no structure — it means the structure exists in the data in a form not directly readable by the instrument, and must be presented through encoding.

Encoding is not preprocessing — it is part of measurement. Changing encoding = changing what world the instrument sees. Encoding must preserve predictive structure: if event A constrains event B in the original stream, that constraint must survive encoding. A single encoding is always lossy — dual-encoding cross-validation is the only way to distinguish true structure from encoding artifacts.

### 14.3 Self/We as Amplifiers

Solo Geruon is blind in some domains. WTC solo F ~= 0 at all kappa — a single lens sees no structure at all. But a three-cavity Self (heterogeneous kappa_tau sharing a BiasField) produces cross-harm signal on the same stream. Self is an amplifier — structural divergence across multiple time lenses amplifies faint signals invisible to a single lens.

We amplifies one layer further. Multiple Selfs with different encodings of the same object produce different residuals; cross-Self unabsorbable residuals precipitate in the collective. Structure that a single Self cannot process becomes, at the We layer, raw material for Codex formation through cross-harm.

Amplification gain: `G_disc = |delta_L3| / (3 * cap)`. ECG: G_disc=0.65 (RR encoding), WTC: G_disc=0.52 (frequency-bin encoding). Cap sweet spot 20-32 — too small and signal is insignificant, too large and L3 chains are diluted.

### 14.4 Next Steps

Solo Geruon is the detector. Self is the amplifier. We is the research tool for Codex formation. Codex is the externalized precipitate.

For the full assembly, configuration, and description of the four experiment domains (WTC/DNA/RNA/UN), see **[EE_MANUAL.md](EE_MANUAL.md)**.

---

*Geruon Manual v2.0. Practical: Quick Start -> API -> Calibration -> Patterns -> Configuration. Principles: Architecture -> Tau -> Economics -> Frame Economy -> Pengshu -> Precipitation -> BiasField -> Faraday -> Boundaries & Amplifiers. Next in the chain: [EE_MANUAL.md](EE_MANUAL.md).*
