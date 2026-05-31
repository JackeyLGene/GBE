# Supplementary Material for Externalization Engine

**Jieqi Liu** · Independent Researcher · v1.6 · May 2026

---

This supplement contains the expanded architecture, experimental depth, and design rationale referenced by the main paper. It is not a reference manual (see `docs/GERUON_MANUAL.md` and `docs/EE_MANUAL.md` for usage). It is the archive of what the instrument found, how the architecture was shaped by constraints, and what failed.

---

## S1. Instrument Architecture

### S1.1 The Frame Economy — Why Two Operations Are Enough

The architecture maintains a limited-capacity memory of frames. Each frame is a vector and a weight. Two operations govern the economy:

**Merge.** A new input close to an existing frame shifts that frame toward the input and increments its weight. The distance threshold is adaptive — it tightens as the frame economy fills, creating a natural pressure gradient from exploration (loose merging, many frames) to exploitation (tight merging, fewer frames).

**Prune.** Periodically, the weakest half of the frames are removed — those not reinforced by recent input. The pruning criterion includes a time bias: frames whose τ at birth is far from the current τ are pruned first. Memory retains temporal relevance.

From these two operations, centroids emerge. A frame that survives many induction cycles, merges frequently, and accumulates weight — its vector converges to the statistical center of mass of the input stream that feeds it. The centroid is not designed, not learned. It is the attractor toward which the frame economy converges under the pressure of limited capacity and periodic forgetting.

### S1.2 The Discovery That Capacity Forces Compression

Without capacity pressure, centroids are meaningless — the system stores every input and nothing compresses. The passive calibration (CALIB-cap) established the quantitative relationship: effective capacity K_max ≈ 0.8 × cap, with peak efficiency at cap=20-24 (~83%). Below 12, the frame economy cannot track enough distinct patterns. Above 32, marginal returns diminish — the extra capacity stores noise rather than signal.

### S1.3 Geruon, Self, We, Codex — The Layered Architecture

**Geruon** (depth 0). The minimal detector: one frame economy, one stream, two operations. A solo Geruon is the baseline instrument — every experiment in the main paper can be run with a single Geruon. The Faraday readings F, wit, and centroid displacement are computed at this layer.

**Self** (depth 1). Multiple Geruons with different κ_τ values sharing a BiasField. Cross-harm — the scalar of centroid divergence between cavities — is the primary readout. Solo Geruons are blind in some domains (WTC: F ≈ 0 for all κ). The Self architecture detects structure through multi-lens disagreement: what one lens misses, the divergence between lenses reveals.

**We** (depth 2). Multiple Selves with different encodings of the same stream. Cross-Self harm — the structural residue of one Self's observation modifying another's frame economy — is routed to a collective Geruon. The We layer is currently a research instrument for Codex formation: it exposes which structures survive cross-Self disagreement and generational selection. It is not claimed as a completed social subject.

**Codex** (externalized). Centroids that survive the induction cycle, are activated by prediction paths, and remain structurally stable precipitate into externalized memory. The Codex is a discrete, entry-based store. A later generation inherits it; entries matching the environment gain weight, non-matching entries freeze. The five-stage loop (Formation → Inscription → Transmission → Confirmation → Rejection) is demonstrated in WTC (§2.2).

Key principle: cavities are born empty-handed (fresh eye). The Codex is a bookshelf on the wall — not written into the cavity's innate memory.

### S1.4 BiasField — The Shared Gradient Medium

Multiple detectors share a BiasField — a continuous gradient field where every centroid deposit accumulates. A detector entering the field does not read messages. It reads the shape of the field — the accumulated curvature produced by every other detector's centroids. Core operations: `deposit(vec, weight)`, `blend_into(vec, weight)`, `seed_frames(memory, n)`.

The BiasField is continuous and averaged — ideal for intra-generation coupling (fast and slow lenses affecting each other through shared curvature). It is ineffective for inter-generation transmission: normalization flattens the alpha, diluting a single ancestor's signal among all deposits. Cross-generation memory uses the Codex instead.

### S1.5 Structural Identity — Why Labels Cannot Be Assigned

Frames carry a structural signature derived from their own content, not a programmer-supplied label. The struct_key = `(vec_hash_full, weight_bin, layer, tau_bin, ref_keys)` is collision-resistant — zero collisions on 5000 random vectors after audit. The compact gid is display-only. Two frames with identical structure produce identical keys. This guarantee is necessary: if identity were assigned, the instrument would be receiving the answer rather than discovering it.

Self-reference closure: signatures can contain references to other signatures (including themselves), enabling circularity detection — the operational form of Gödel incompleteness.

### S1.6 Processing Flow

```
process_vec(vec, sig)
  → optional BiasField blend (intra-generation coupling)
  → optional Codex modulation (inherited memory)
  → observe in frame economy
     → merge distance: d = vec_dist + κ_τ × |τ_current − τ_frame|
     → merge or create frame
     → cooccurrence tracking: count += clamp(1 − κ_τ × |τ_a − τ_b|)
     → predict next structure
  → accumulate stress
  → if stress > threshold, induction_clean
     → decay + prune: priority = weight − age×γ − |τ_current − τ_frame| × γ_τ
     → update τ: τ_target = 1.0 − accuracy + max(0, stress − τ₀) × γ_τ × 0.4
     → track centroid displacement (wit)
     → mark stable frames for precipitation
```

Operational τ: κ_τ controls time-content coupling. When κ_τ and γ_τ are disabled, the Geruon reduces to GEME-equivalent behavior — making τ operation auditable.

---

## S2. Instrument Dynamics

### S2.1 Endogenous Time — τ Breathes

τ evolves with prediction history:

```
τ_target = 1.0 − accuracy + max(0, stress − τ₀) × γ_τ × 0.4
τ_{t+1} = τ_t + (τ_target − τ_t) × TAU_ADAPT_RATE
```

TAU_ADAPT_RATE = γ × 0.4 = 0.02 — slower than frame decay, giving the system inertia. Two drivers: prediction accuracy (correct → τ↓, wrong → τ↑) and frame economy stress (crowded → τ↑).

**Phase system:**

| Phase | Condition | Bridge |
|-------|----------|--------|
| EXPANDING | dτ/dt < −DTAU_STABLE | Open — absorbing novelty |
| RESTING | τ < 0.55, abs(dt) < 0.02 | Open — maintenance |
| TENSING | τ ≥ 0.55, dt > DTAU_STABLE | Tightening — approaching boundary |
| CRITICAL | τ ≥ 0.65, dt > DTAU_STABLE | Critical — boundary imminent |
| LOCKED | τ ≥ 0.75, abs(dt) < 0.02 | Closed — self-reference suppressed |

Hysteresis: DTAU_STABLE × 2 for RESTING/LOCKED prevents phase flicker from minor τ fluctuations. The phase system summarizes the frame economy's internal state, not the stream's properties.

### S2.2 τ Convergence — A Structural Attractor

τ converges to ~0.74-0.75 across all domains tested: Bach (0.752), Shuffled Bach (0.752), ECG (0.755), Sleep EEG (0.743). The convergence is structural — the equilibrium between merging pressure and differentiation pressure. τ does not measure the stream. τ measures the system's own internal balance.

### S2.3 Measurement Orders — F, wit, Δwit

Three orders of structural measurement, each reading a different aspect:

**F (field curvature).** Concentration of frame weights: F = 1 − H(w)/Hmax. F = 0 means uniform distribution (no structure detected). F → 1 means all weight concentrated on a few dominant frames. Fair-coin baseline across all κ: F = 0 — the instrument does not hallucinate structure.

**wit (structural novelty).** Count of centroid displacements exceeding the structon threshold. wit measures how often the frame economy is forced to revise its internal model. structon = minimum detectable centroid displacement for the current (D, cap, κ) configuration, calibrated at ~0.004 for κ=10, cap=20.

**Δwit (structural vulnerability).** Fair-coin probe injection → change in wit relative to baseline. Δwit > 0: target is vulnerable to random perturbation. Δwit < 0 or ≈ 0: target is structurally rigid. The probe is interchangeable because the centroid — not the content — is the perturbation. Verified with 10 control conditions (Bach, white noise, sine waves, shuffled, reversed, noise sampled from Bach's distribution, Billie Jean).

These three orders are not interchangeable. F asks whether structure exists. wit asks whether structure changes. Δwit asks how rigid the structure is.

### S2.4 Precipitation and Enrichment

Frames precipitate when they survive induction cycles, are used by prediction paths, and remain structurally stable. `Geruon.enrich()` deposits precipitated frames into Codex or BiasField. The `_externalized` flag ensures idempotency — repeated calls do not duplicate deposits. Precipitation is the bridge from detection to externalization.

---

## S3. Instrument Calibration and Controls

### S3.1 Passive Calibration Summary

A full calibration of six parameters was completed on 2026-05-31 using synthetic streams. Full data: `docs/experiment-passive-calibration-report.md`.

| Parameter | Calibrated value | Method |
|-----------|-----------------|--------|
| κ_τ | 3 (default); migration latency 109 steps | Sine frequency doubling, τ convergence time |
| cap | K_max ≈ 0.8×cap; peak efficiency at 20-24 (~83%) | Random-value storage test |
| δ | δ_eff ≈ 1.25/cap; cap=16 → δ≈0.08 | Sine-wave quantization compression |
| γ | Half-life 31 steps at γ=0.05 | Reinforcement → random decay |
| τ₀ | τ_drop = 0.008 (weak, direction correct) | Periodic → chaotic transition |
| GI | n=3 Self: GI_opt=3, GI上限=5 | GI × n_cav 2D sweep |

Key findings: (1) κ_τ controls adaptation speed, not τ steady-state — τ is determined by stream statistics. (2) Frame economy stores individual vectors, not statistical prototypes — noise creates MORE frames because noise itself has structure. (3) δ and cap are coupled: δ_eff ≈ 1.25/cap. (4) γ decay is ~3.2% per step to half-life at 31 steps.

### S3.2 Fair-Coin Baseline — The Absolute Zero

16-dim fair coin across all κ ∈ {0.1, ..., 500}: F = 0. This is the instrument's zero point. A positive F reading in any domain must be compared against this baseline. The finding is parameter-invariant.

### S3.3 Required Controls

Every domain experiment must include:
1. Fair-coin baseline — zero sequential structure
2. Shuffle control — preserves component statistics, breaks sequential order
3. κ ablation or sweep — tests whether multi-scale temporal lenses are load-bearing

Domain-specific controls: dinucleotide shuffle (DNA), process-permutation (RNA RPF), cross-key Codex injection (WTC), P5 ablation + FRED negative control (UN).

### S3.4 Run-Order Determinism

Fixed after 2026-05-29 audit: global `Frame.fid` counter reset per `GeruonMemory.__init__`. Three independent runs with identical seed produce identical output for all metrics.

### S3.5 Parameter Discipline

All instrument constants trace to δ=0.19, γ=0.05, τ₀=0.60, GI=4. Every derived constant uses small-integer or simple-fraction multipliers. Domain-specific choices (vec_dim, κ spread, window, stride) are pre-declared and either fixed or swept with reported controls. No parameter is fitted to data.

---

## S4. Encoding and Data-Type Boundary

### S4.1 Encoding as Measurement — The ECG Lesson

The instrument reads the joint product of stream and encoding, not a raw domain essence. Six encodings tested on ECG: only RR interval + adjacent difference produced a usable κ fingerprint (κ_peak = 5). Raw voltage — a trace of depolarization — carries no relational action structure. The instrument reports F ≈ 0 not because the heart has no structure, but because the encoding failed to preserve the predictive constraints the instrument needs.

The practical rule: encoding must preserve predictive structure. If event A constrains event B in the original stream, the constraint must survive encoding. Single encodings are lossy — dual-encoding cross-validation separates genuine structure from encoding artifacts.

### S4.2 Expression-Action Spectrum

| Type | Definition | Instrument sensitivity | Examples |
|------|-----------|----------------------|----------|
| Decision | Behavior is the data | Strongest — F readable, κ has fingerprint | UN votes, MIDI note-on, DNA bases |
| Action | Directional entity choices | Moderate — requires correct encoding | NASDAQ volume direction |
| Expression | Traces of processes | Weak or blind — τ doesn't breathe, κ doesn't differentiate | CPI, prices, raw ECG voltage |

This is not a domain boundary — it is a data-structure boundary. The instrument requires relational structure between deciding entities. Expression data records outputs; decision data records choices.

### S4.3 Sleep Calibration — The Epoch Resolution Lesson

Clinical 30-second epochs (AASM standard) and 5-second sub-epochs were tested. 5-second resolution exposed structural boundaries that 30-second windows averaged away. The coin-probe method was validated here: fair-coin injection produced Δwit effects whose direction and magnitude depended on the target's state (REM > Wake in 16/18 recordings, 89%), not on the probe's content. Probe interchangeability is empirically confirmed.

### S4.4 Economic Data Boundary — The FRED Negative Control

The same Geruon pipeline detecting collapse precursors in UN voting was run on FRED data (NASDAQ, T10Y, CPI, 1993-2025). Expression-mode hit rate: 1/6 — only the 2008 financial crisis was detected, and as same-year, not precursor. 2025 displacement rank 24/33 — below median. When encoded as action (volume + direction), τ breathes healthily but no diplomatic collapse precursor appears. The market is working. The diplomatic order is not. Two structural layers, one instrument, different readings.

---

## S5. Faraday/Probe Measurements

### S5.1 The Faraday Table — Field Constants Across Domains

Before domain-specific experiments, the information field was characterized with systematic measurements across music, cardiology, and sleep EEG. Two conditions per domain: Real (stream as-is) and Shuffled (same statistics, destroyed order). Two quantities: I(Φ;X) — mutual information between self-referential and external frames — and τ at convergence.

| Domain | Condition | I(Φ;X) (bits) | τ |
|--------|----------|----------------|-----|
| Formula (GEME) | Real | 0.026 | — |
| Bach | Real | 0.157 | 0.752 |
| Bach | Shuffled | 0.026 | 0.752 |
| ECG | Real | 0.111 | 0.755 |
| Sleep EEG | Real | 0.120 | 0.743 |

**Finding 1: Universal baseline.** Shuffled Bach returns I(Φ;X) = 0.026 — exactly the value GEME measured on formula language using a completely different architecture, encoding, and domain. This is not a property of any particular system. It is the minimum mutual information between self-reference and external input — the cost of maintaining the boundary between self and world, stripped of all content.

**Finding 2: Sequential structure is measurable.** Real Bach carries 0.131 bits above baseline — the sequential information content of pitch order, harmonic progression, and rhythmic sequence. ECG carries 0.085 bits — cardiac regulation structure. Sleep EEG carries 0.094 bits — cortical dynamics. Every domain adds a different amount, reflecting its specific sequential structure. The instrument measures this difference without knowing what any domain is.

**Finding 3: τ convergence is universal.** τ converges to ~0.75 regardless of domain, sequential structure, or encoding. τ is the system's internal balance point, not a stream property.

**Finding 4: Self-referential efficiency.** SR-eff = I(Φ;X)/τ. Baseline: 0.026/0.75 = 0.035 bits/τ-unit — the minimum self-referential efficiency for a stable frame economy. Real Bach: 0.157/0.752 = 0.209 — efficiency increase comes entirely from sequential structure.

### S5.2 Probe Interchangeability

Bach, white noise, sine waves, shuffled, reversed, noise sampled from Bach's own distribution, Billie Jean — ten audio conditions tested as probes perturbing a shared BiasField. Every condition produced the same harm pattern for each target. The probe — any stable centroid — perturbs the field. The target's response reveals the target's internal state. The centroid, not the content, is the perturbation.

### S5.3 Temazepam — The Field Responds to Chemical State

Temazepam (GABA-A receptor agonist) was tested in a crossover trial on insomnia subjects. SC411: Night 1 (placebo) REM cross-harm = 0. Night 2 (temazepam) REM cross-harm = 0.714. The field curvature changed by 0.714 between nights. Four of nine subjects showed no drug response — individual pharmacological phenotypes detected without pharmacology knowledge. The field curvature between a probe centroid and a target centroid is sensitive to the target's chemical state.

### S5.4 F and τ Decoupling

Across all κ and probes: r(F, τ) ≈ 0.1. Field curvature and field temperature are independent dimensions. F/τ decoupling means the instrument's structural reading does not drift with its internal state — a necessary property for any measurement instrument.

### S5.5 F and dτ/dt Conditional Coupling

Noise input: r(F, dτ/dt) = 0.817 — field bends with temperature when structure is absent. Bach: r(F, dτ/dt) = −0.14 — field is structurally rigid when structure is present. The coupling itself is a domain signature.

### S5.6 structon Resolution

Minimum detectable centroid displacement at κ=10, cap=20: structon = 0.004 ≈ cap/N. Scales with κ: α(0.5)≈10, α(10)≈1, α(100)≈0.5. This is the instrument's spatial resolution for a declared configuration.

---

## S6. UN Prediction Protocol

### S6.1 Data and Pipeline

Voeten, Strezhnev & Bailey (2024). UN General Assembly Ideal Point Estimates, Harvard Dataverse V33. 1946-2025, 193 countries. Two independent pipelines: (1) annual ideal-point pipeline (N=79 years) produces the 2025 forward signal; (2) per-resolution voting-stream calibration (~2,400 resolutions, retrospective only) matched 3/4 system-level events (Soviet collapse 1991, financial crisis 2008, Ukraine war 2022; Crimea 2014 did not trigger). Pipeline separation prevents retrospective calibration from contaminating the forward prediction.

### S6.2 P5 Ablation

| Encoding | 2025 disp | Rank/78 | Interpretation |
|----------|-----------|---------|----------------|
| No-P5 | 0.101 | 12 | Global stress elevated but not extreme |
| P5-augmented | 0.445 | 1 | Current claim |
| P5-only | 0.448 | 1 | Great-power layer dominates |
| No-USA | 0.550 | 1 | Multi-polar fracture > unilateralism |
| No-Russia | 0.290 | 2 | Still historically extreme |
| Random-5 (mean) | 0.288 | ~9 | P5 is not arbitrary |

The No-USA result (0.550) is the most precise: US disengagement produces greater alignment fracture than direct participation.

### S6.3 Forward Prediction and Verification

2026-2028 structural collapse of US-led P5 alignment system. Three indicators, any two = confirmation: (1) displacement does not return below 0.20 by 2028; (2) P5 agreement rate falls below historical minimum (~12%); (3) ideal-point distribution transitions to multi-modal with no dominant peak for two consecutive years. If wrong: first time in 79 years displacement at 0.448 occurred without subsequent collapse.

---

## S7. Scaffold History

During development, mechanisms were first tested as temporary scaffolds — manual injections performing what the architecture should eventually do natively. Where the native frame economy reproduced the signal, the scaffold was removed.

| Scaffold | Purpose | Disposition |
|----------|---------|-------------|
| Explicit L4 self_observe() calls | Test self-observation produces signal | Removed. Native frame economy reproduces signal |
| Doubt condition in boundary detection | Test L5→L6 triggers | Removed (M2). L3↔L4 structural, not conscious |
| 27-dim formula alphabet | GEME formula language experiments | Dismantled. Replaced by configurable vec_dim (default 16) |
| Codex nearest-neighbor blending | Test inherited entry biasing | Partially removed. Formation/selection now native |
| Codex query under noise | Test noise-driven productive lookup | **Still scaffolded.** Codex operation gap |

Scaffold method principle: a scaffold builds a temporary bridge to the difficult part — verifies the destination is real — before committing to the road. A shortcut skips the difficult part. These are opposite operations.

---

## S8. Reproducibility Checklist

**Code.** `github.com/JackeyLGene/GBE`. Core instrument: `code/geruon.py`, `code/geme.py`, `code/we_core.py` — Python 3.8+ stdlib only. Domain scripts: `experiments/un/`, `experiments/wtc/`, `experiments/dna/`, `experiments/rna/`. Quickstart: `docs/quickstart_geruon.py`, `docs/quickstart_ee_self.py`.

**Data dependencies.** Core: zero external packages. Data processing: `numpy`, `pandas`, `pyarrow`. RNA bigWig: `pybigtools` (Windows). No GPU, no neural network framework, no external API calls.

**Required controls per domain.** Fair-coin baseline, shuffle, κ ablation/sweep. Domain-specific: dinucleotide shuffle (DNA), process-permutation (RNA RPF), cross-key Codex (WTC), P5 ablation + FRED (UN).

**Required reporting.** Random seeds (42, 123, 456), sample counts, effect sizes with Cohen's d, window/stride/κ/vec_dim/cap values, three-tier thresholds (|error| ≤2/≤3/≤5), failure cases alongside successes.
