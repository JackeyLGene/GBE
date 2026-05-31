# Supplementary Material for Externalization Engine

**Jieqi Liu**  
Independent Researcher  
v1.6 · May 2026

---

## Overview

This document contains technical material supporting *Externalization Engine: Creation → We Create → Create Us*. The main paper is written as a self-contained preprint and introduces only the minimal instrument needed to follow the evidence. This supplement provides the expanded architecture, dynamics, calibration, controls, and development scaffolds.

---

## S1. Instrument Architecture

### S1.1 Geruon

A Geruon is the minimal detector: one limited-memory cavity receiving one vector stream. It maintains a frame economy. Each frame contains a vector, a weight, a layer, an age, and a structural signature. Inputs close to an existing frame merge into it; inputs that do not match create new frames. Periodic pruning removes weakly reinforced frames. Surviving frames are read as centroids.

The public API is intentionally small. A run consists of repeated calls to `process_vec(vec, sig)`, followed by readout through `metrics()`, `arrow_output()`, or centroid-based summaries. `enrich()` externalizes precipitated frames into a Codex or BiasField. There is no `fit()` or `train()` method: processing the stream is the experiment.

Constructor arguments: `vec_dim`, `memory_cap`, `kappa_tau`, `gamma_tau`, `codex`, `bias_field`, `bias_weight`, `structon`.

### S1.2 Class Hierarchy

```
geme.py
  Frame      -> vector, weight, age, signature, layer
  Memory     -> observe, co-occurrence, induction_clean, prediction
  GEME       -> top-level processing and metrics

geruon.py
  GeruonFrame   -> Frame + structural signature, tau, survival, precipitation state
  GeruonMemory  -> Memory + tau dynamics, phase, boundary events, precipitation
  Geruon        -> process_vec, arrow_output, enrich, Codex, BiasField

supporting:
  StructuralSig -> collision-resistant struct_key, gid (display-only), circularity detection
  Codex         -> externalized centroid table, JSON persistence
  BiasField     -> accumulated gradient field, deposit, blend, seed frames
```

Internal layers (not supplied as labels):

```
L1  base frames
L2  co-occurrence / association frames
L3  chain / bridge frames
L4  self-observation frames
L6  anomaly / doubt frames
```

### S1.3 Self

A Self couples multiple Geruons with different temporal lenses (κ_τ). The same stream is processed by separate cavities sharing a BiasField. Centroid divergence is measured as cross-harm: low harm = consensus across time scales; high harm = structural boundary detected.

Common Self configurations:

```
standard 3-cavity:  kappa = 0.5 / 10 / 100
extreme 3-cavity:   kappa = 0.005 / 10 / 5000
boundary 2-cavity:  kappa = 0.01 / 500
```

Changing kappa changes the measurement scale — not a learned parameter, but a choice of temporal lens that must be reported and, where possible, swept or ablated.

### S1.4 BiasField

The BiasField is the shared medium in which boundary events leave traces. Detectors do not read symbolic messages from the field; they enter a field already curved by prior centroid deposits. Core operations:

```
deposit(vec, weight)      -> accumulate a centroid direction
blend_into(vec, weight)   -> mix field direction into an input
seed_frames(memory, n)    -> initialize frames from high-field dimensions
```

BiasField is continuous and averaged (intra-generation coupling). Codex is discrete and entry-based (inter-generation memory).

### S1.5 We

The We layer records harm and residual patterns across Selves. In the current work it is a research instrument for disagreement detection, not an autonomous subject. A We contains multiple Selves and a collective Geruon that receives cross-Self harm material. The resulting collective Codex provides evidence of formation: which structures survive cross-Self disagreement and generational selection. The paper does not claim a completed We-level social subject.

### S1.6 Codex

The Codex stores stable centroids outside the run that produced them. Three stages:

```
formation:   stable centroids precipitate and survive outside the originating run   — demonstrated
selection:   inherited entries are confirmed, supplemented, frozen, or ignored      — demonstrated
operation:   inherited entries actively shape ongoing processing under noise         — scaffolded
```

Only formation and selection are reported as demonstrated in the main paper.

### S1.7 Structural Identity

Structural identity uses a collision-resistant `struct_key`:

```
struct_key = (vec_hash_full, weight_bin, layer, tau_bin, ref_keys)
```

The compact `gid` is display-only and must not be used as an equality key. This distinction was introduced after code audit found that short display identifiers could collide (373/5000 at 15 bits). The publication claim relies on `struct_key`, which produces zero collisions on 5000 random vectors.

### S1.8 Processing Flow

```
process_vec(vec, sig)
  -> optional BiasField blend
  -> optional Codex modulation
  -> observe vector in frame economy
     -> compute distance to existing frames (with tau-gated merge)
     -> merge or create frame
     -> update co-occurrence traces (tau-weighted)
     -> predict next structure
  -> accumulate stress
  -> if stress exceeds threshold, run induction_clean
     -> decay and prune frames (tau-biased)
     -> update tau and phase
     -> track centroid displacement (Faraday wit)
     -> mark stable frames for precipitation
```

---

## S2. Instrument Dynamics

### S2.1 Frame Economy

The frame economy is governed by merge, prune, and self-observation. Merge shifts an existing frame toward a nearby input and increases its weight. Prune removes frames that have not been reinforced. Self-observation periodically creates a weighted centroid of active frames and feeds it back into the economy as an internal event.

These operations are bounded by `memory_cap`. Capacity is not a performance setting — it is the pressure that forces compression. Without limited memory, centroids are less meaningful because the system retains too many uncompressed traces.

### S2.2 Endogenous Time

Endogenous time (`tau`) rises when prediction fails or the frame economy is stressed, and falls when predictions succeed:

```
tau_target = 1.0 - accuracy + max(0, stress - tau_0) * gamma_tau * 0.4
tau_next   = tau + (tau_target - tau) * tau_adapt_rate
```

`tau_adapt_rate = gamma * 0.4 = 0.02` — slower than frame decay, giving the system inertia. `kappa_tau` controls time-content coupling strength. Multi-cavity Self architectures use different `kappa_tau` values to compare fast and slow readings.

Phase system:

```
EXPANDING  -> tau falling, bridge open
RESTING    -> low tau and stable change
TENSING    -> tau rising above resting range
CRITICAL   -> tau high and still rising
LOCKED     -> tau high and stable, expensive self-reference suppressed
```

τ converges to ~0.74-0.75 across all domains tested. This is the equilibrium between merge pressure and differentiation pressure in a self-referential frame economy.

### S2.3 Operational Tau

Tau is not only a label. It enters three core operations:

```
merge distance:
  d = vec_dist + kappa_tau * |tau_current - tau_frame|

co-occurrence weighting:
  cooccur += clamp(1 - kappa_tau * |tau_a - tau_b|)

pruning priority:
  priority = weight - age * gamma - |tau_current - tau_frame| * gamma_tau
```

When `kappa_tau` and `gamma_tau` are disabled, the Geruon reduces to GEME-equivalent behavior. This makes tau operation auditable rather than descriptive.

### S2.4 Measurement Orders

Three orders of structural measurement:

```
F      = structure existence; concentration of frame weights (0 = flat, ->1 = concentrated)
wit    = structural movement; count of centroid displacements above structon threshold
Δwit   = perturbation vulnerability; change in wit under fair-coin probe injection
```

`structon` is the minimum detectable centroid displacement for a declared (D, cap, κ) configuration. It must be calibrated per parameter family and must not be transferred across configurations without recalibration.

### S2.5 Precipitation and Enrichment

Frames precipitate when they survive across cleaning cycles, are used by prediction paths, and remain structurally stable. `Geruon.enrich()` externalizes precipitated frames into Codex or BiasField. The implementation tracks `_externalized` state so repeated calls are idempotent. A transient frame remains internal; a precipitated frame becomes eligible for cross-run inheritance or shared-field influence.

---

## S3. Instrument Calibration and Controls

### S3.1 Passive Calibration

A full passive calibration was completed on 2026-05-31. Six parameters were quantitatively calibrated with synthetic streams. Full report: `docs/experiment-passive-calibration-report.md`.

| Parameter | Calibrated value | Method |
|-----------|-----------------|--------|
| κ_τ | **3** (default); migration latency 109 steps | Environmental reversal: sine frequency doubling |
| cap | **K_max ≈ 0.8×cap**; peak efficiency at cap=20-24 (~83%) | Random-value storage: K distinct vectors, pred_err threshold |
| δ | **δ_eff ≈ 1.25/cap**; cap=16 → δ≈0.08 | Sine-wave quantization: compression ratio vs bit depth |
| γ | Half-life **31 steps** at γ=0.05 | 400-step reinforcement → 800-step random decay |
| τ₀ | τ_drop **0.008** (weak, direction correct) | Periodic → chaotic mode transition |
| GI | n=3 Self: **GI_opt=3**, GI上限=5 | MiniSelf: GI × n_cav 2D sweep |

### S3.2 Fair-Coin Baseline

16-dim fair coin across all κ ∈ {0.1, ..., 500}: F = 0. The instrument's absolute zero. Every domain experiment must report its F against this baseline.

### S3.3 Required Controls

Every domain experiment must include at least three controls:

1. **Fair-coin baseline** — zero sequential structure. Defines the instrument's zero point.
2. **Shuffle control** — preserves component statistics while breaking sequential order. Tests whether signal depends on order.
3. **κ ablation or sweep** — tests whether multi-scale temporal lenses are load-bearing. Single-κ replication must confirm that the signal degrades.

Additional controls by domain: dinucleotide shuffle (DNA, preserves base composition); process-permutation (RNA RPF, shuffles RPF across windows); cross-key Codex injection (WTC, tests selection specificity); P5 ablation (UN, tests whether institutional lens creates or amplifies the signal); FRED negative control (UN, tests domain specificity).

### S3.4 Parameter Discipline

All instrument constants trace to four base values: δ=0.19, γ=0.05, τ₀=0.60, GI=4. Every derived constant uses small-integer or simple-fraction multipliers. Domain-specific choices (vec_dim, κ spread, window, stride) are pre-declared and either fixed or swept with reported controls. Parameters are not fitted to data; they are chosen before the run and reported regardless of outcome.

### S3.5 Run-Order Determinism

Fixed after 2026-05-29 audit: global `Frame.fid` counter reset per `GeruonMemory.__init__`. Three independent runs with identical seed produce identical output for all metrics. Verified in the calibration report.

---

## S4. Encoding and Data-Type Boundary

### S4.1 Encoding as Measurement

Encoding is part of the measurement — not preprocessing. The instrument reads the joint product of stream and encoding, not a raw domain essence. Different encodings of the same signal produce different F baselines and different κ fingerprints.

The practical rule: encoding must preserve predictive structure. If event A constrains event B in the stream, that constraint must survive the encoding. Single encodings are lossy — the strongest experiments use dual or multi-lens readings and ask whether structure survives across them.

Common encodings used in this work:

| Domain | Encoding | Dim | What it preserves |
|--------|----------|-----|-------------------|
| WTC | chroma + IOI | 12+12 | Pitch class activation + inter-onset interval histogram |
| DNA/RNA | 3-mer frequency | 64 | Trinucleotide composition in sliding genomic windows |
| DNA fork | 4-species alignment vector | 16 | Per-column conservation across species |
| UN | Annual ideal-point distribution | variable | Country-year position in policy space |
| ECG (calibration) | RR interval + adjacent diff | 16 | Beat-to-beat interval and first derivative |

### S4.2 Expression-Action Spectrum

The instrument's sensitivity is governed by data structure type, not domain category:

| Type | Definition | Instrument response | Examples |
|------|-----------|-------------------|----------|
| **Decision** | Behavior IS the data | Strongest. F readable, κ has fingerprint. | UN votes, MIDI note-on, DNA bases |
| **Action** | Directional entity choices | Moderate. Requires correct encoding. | NASDAQ volume direction |
| **Expression** | Traces of processes | Weak or blind. τ doesn't breathe, κ doesn't differentiate. | CPI, prices, raw ECG voltage |

### S4.3 Illustrative Cases (Archival)

Three calibration domains tested the boundary empirically. Full data archived in the instrument calibration report.

**ECG.** Six encodings tested. Only RR interval + adjacent difference produced a usable κ fingerprint. Raw voltage — a trace of depolarization — carries no relational action structure. κ_peak = 5.

**Sleep.** Epoch resolution matters: 5-second sub-epochs exposed structural boundaries that clinical 30-second windows averaged away. The coin-probe method was validated here: REM wit > Wake wit in 16/18 recordings (89%).

**Economic data.** Same Geruon pipeline on FRED data (1993-2025): expression-mode hit rate 1/6, 2025 displacement rank 24/33. The 2025 structural pressure detected in diplomatic voting is absent from economic expression data.

---

## S5. Faraday/Probe Measurements

### S5.1 Probe Interchangeability

Three probes tested: Bach pitch distribution (structured), white noise (unstructured), sine wave (periodic). All produce centroids. The harm pattern between probe and target depends on the target's state, not on which probe is used. The centroid — not the content — is the perturbation. Verified with 10 control conditions.

### S5.2 τ Convergence

τ converges to 0.74-0.75 across all domains, all input types, and all architectural depths. This is the equilibrium between merge pressure and differentiation pressure. τ measures the system's internal balance, not the stream's properties.

### S5.3 F and τ Decoupling

Across all κ and all probes: r(F, τ) ≈ 0.1. Field curvature and field temperature are independent dimensions. The instrument's structural reading does not drift with its internal state.

### S5.4 F and dτ/dt Conditional Coupling

On noise input: r(F, dτ/dt) = 0.817 — field bends with temperature. On Bach: r(F, dτ/dt) = −0.14 — field is structurally rigid. The coupling itself is a domain signature: unstructured input allows F to follow τ; structured input resists.

### S5.5 structon Resolution

Minimum detectable centroid displacement at κ=10, cap=20: structon = 0.004 ≈ cap/N. structon scales with κ: α(0.5)≈10, α(10)≈1, α(100)≈0.5. This is the instrument's spatial resolution — the smallest structural change registerable in a single step.

---

## S6. UN Prediction Protocol

### S6.1 Data Source

Voeten, Strezhnev & Bailey (2024). United Nations General Assembly Ideal Point Estimates. Harvard Dataverse, V33. Annual country-level ideal points, 1946-2025, 193 countries.

### S6.2 Pipeline Separation

Two separate pipelines are maintained:

1. **Annual ideal-point pipeline** (main paper §4.1): Country-year ideal points → annual global distribution features → Geruon centroid displacement. N=79 years. Produces the 2025 forward signal.

2. **Per-resolution voting-stream calibration** (historical only): ~2,400 resolutions as event traces. Selected precursor patterns matched 3 of 4 system-level events (Soviet collapse 1991, financial crisis 2008, Ukraine war 2022; Crimea 2014 did not trigger). This pipeline is NOT the source of the 2025 forward signal and the 3/4 claim is not inherited.

Pipeline separation prevents retrospective calibration from contaminating the forward prediction.

### S6.3 P5 Ablation

Six encoding variants tested:

| Encoding | 2025 disp | Rank/78 | Interpretation |
|----------|-----------|---------|----------------|
| No-P5 (global only) | 0.101 | 12 | Elevated but not extreme |
| P5-augmented (current) | 0.445 | 1 | Great-power institutional lens |
| P5-only | 0.448 | 1 | Great-power layer dominates the signal |
| No-USA | 0.550 | 1 | Multi-polar fracture > unilateralism |
| No-Russia | 0.290 | 2 | Still historically extreme |
| Random-5 (mean, 5 trials) | 0.288 | ~9 | P5 is not an arbitrary prior |

The signal is concentrated in the P5 layer. The No-USA result (0.550) is the most precise: US disengagement produces greater alignment fracture than direct participation.

### S6.4 FRED Negative Control

Same pipeline on FRED economic data (1993-2025): 2025 displacement rank 24/33 — below median. Pure economic expression data judges 2025 structurally normal.

### S6.5 Forward Prediction

2026-2028: structural collapse of the US-led post-war international order, concentrated in P5 great-power alignment. Magnitude exceeds 2022 Ukraine war, comparable to 1991 Soviet collapse. Not a prediction of US domestic collapse — a prediction of gravitational realignment in the P5 layer.

### S6.6 Verification Criteria

Three indicators, any two satisfied = confirmation:

1. Annual displacement does not return below 0.20 by end of 2028 (after Soviet collapse, disp fell from 0.19 to 0.05 within four years)
2. P5 voting agreement rate falls below historical minimum (~12%) in any year 2026-2028
3. Ideal-point distribution transitions from uni-/bi-modal to multi-modal with no dominant peak for two consecutive years

**Boundary statement.** If this prediction is wrong, it means that for the first time in 79 years, displacement at 0.448 occurred without a subsequent structural collapse. The model measures structure, not causality.

---

## S7. Scaffold History

During development, several mechanisms were first tested as temporary scaffolds:

| Scaffold | Purpose | Disposition |
|----------|---------|-------------|
| Explicit L4 self_observe() calls | Test whether self-observation produces signal | Removed. Native frame economy reproduces the signal. |
| Doubt condition in boundary detection | Test whether L5→L6 doubt triggers boundary events | Removed (M2). Boundary detection is L3↔L4 structural, not L5→L6 conscious. |
| 27-dim formula alphabet | GEME formula-language experiments | Dismantled. Replaced by configurable vec_dim (default 16). |
| Codex nearest-neighbor blending | Test whether inherited entries can bias cavity input | Partially removed. Formation and selection are now native. |
| Codex query under noise | Test whether noise triggers productive Codex lookup | **Still scaffolded.** This is the Codex operation gap (§5.5). |

Where the native frame economy reproduced the signal, the scaffold was removed. Active Codex operation remains scaffolded and is treated as a limitation.

---

## S8. Reproducibility Checklist

**Code.**
- Core instrument: `code/geruon.py`, `code/geme.py`, `code/we_core.py` — Python 3.8+ stdlib only.
- Domain scripts: `experiments/un/`, `experiments/wtc/`, `experiments/dna/`, `experiments/rna/`.
- Quickstart verification: `docs/quickstart_geruon.py`, `docs/quickstart_ee_self.py`.

**Data dependencies.**
- Core instrument: zero external packages.
- Data processing: `numpy`, `pandas`, `pyarrow` (parquet).
- RNA bigWig: `pybigtools` (Windows). Raw data sources documented in each experiment README.

**Required controls per domain.**
- Fair-coin baseline (zero structure)
- Shuffled order (preserves components, breaks sequence)
- κ ablation or sweep (tests multi-lens load-bearing)
- Domain-specific: dinucleotide shuffle (DNA), process-permutation (RNA RPF), cross-key Codex (WTC), P5 ablation + FRED (UN)

**Required reporting.**
- Random seeds (42, 123, 456 for multi-seed)
- Sample counts, effect sizes with Cohen's d
- Window size, stride, κ values, vec_dim, memory_cap
- Three-tier threshold reporting (|error| ≤2 / ≤3 / ≤5)
- Failure cases and negative results alongside positive ones
- Parameter choices declared before runs, not fitted to data
