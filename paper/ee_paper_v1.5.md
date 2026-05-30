# Externalization Engine: Creation → We Create → Create Us

**Jieqi Liu**

Independent Researcher

jackey.l.gene@outlook.com

v1.5 · May 2026

---

## Abstract

**Problem.** Can a system detect structure in a stream without training, labels, or domain knowledge? We propose that structural detection reduces to two operations — merge what is similar, prune what is not reinforced — running under limited memory. The attractors are centroids: the statistical centers of mass toward which any stream converges under the pressure of periodic forgetting. A variable called τ, measuring the system's own prediction success, provides endogenous time. Multiple detectors coupled through a shared field produce cross-harm — a scalar of structural divergence between their centroids. Centroids that survive the memory cycle precipitate into an externalized Codex, outlasting the cavity that produced them.

**Experiments.** We test this architecture — a centroid detector — across four domains that share no physical dimensions. (1) WTC: dual-encoding Self on Bach's Well-Tempered Clavier discovers the tonal skeleton without chord templates, key signatures, or frequency pre-classification. Transposition equivariance holds at 100%. A five-stage Codex selection loop — Formation, Inscription, Transmission, Confirmation, Rejection — confirms that inherited entries matching the environment gain weight across generations while non-matching entries freeze. (2) DNA: the same Self architecture applied to human transcripts detects exon/intron structural separation at d=−0.97 (n=200 transcripts, 10,606 windows). A single-gene fork column calibration on AHSG — identified under positive selection in multiple genome-wide scans (Sabeti et al., 2007; Nielsen et al., 2005) — produces d=+1.51. Both signals collapse under shuffling. (3) RNA: temporal-lens divergence locates the CDS stop codon at 98-100% within ±3 windows (parameter-invariant) and the CDS start at 66% within ±3 windows (75% within ±5). An AUG control achieves 98% discrimination of the annotated start from internal ATGs — the instrument detects transition magnitude, not nucleotide motifs. (4) UN: a prospective civilizational-scale test using 79 years of diplomatic voting (1946-2025). The 2025 great-power alignment displacement (0.448) is the highest substantive reading on record. Falsifiable criteria are specified for 2026-2028. UN is a forward prediction, not a completed validation pillar.

**Results.** Across all domains tested, the same core instrument — with pre-declared domain-specific encodings and ablated parameter families — produces structurally consistent readings. Fair-coin baselines produce zero signal. Shuffled controls collapse positive results. κ ablation confirms that multi-scale temporal lenses are load-bearing. The Codex selection layer is decoupled from the frame economy's processing — externalization creates a history parallel to adaptation, not an improvement of it.

**Limitation.** The architecture is a passive structural detector. It reads patterns, precipitates centroids, and passes them across generations. It does not close the loop from detection back to action. Codex formation and selection are demonstrated; Codex operation — where inherited memory actively shapes ongoing processing under boundary conditions — remains scaffolded. The cognitive-action loop (perception and action as a single event) is the next milestone.

The detector's operation — converging to centroids, coupling them through time, precipitating them across generations — is structurally analogous to human cognition. We interpret this as the computational form of a third dimension of evolution: information written into a medium that outlasts its source. Creation → We Create → Create Us.

---

## Introduction

Every model in machine learning assumes the world must be learned. Training data is collected. Labels are applied. Parameters are optimized. The silent assumption is that cognition is optimization — that knowing is fitting, that structure must be taught before it can be found. We present evidence that this assumption does not hold universally. Structure exists in the stream before any observer names it. A system with the right internal economics can detect it directly — no supervised fitting, no learned weights, no domain labels during processing. Parameters are fixed or swept and reported with controls (§4, Reproducibility). The architecture described in this paper operationalizes this claim, and the experiments in §4 test it across four independent domains.

Three intellectual precursors frame the work, discussed further in §5. Scott Aaronson (2011, 2013) argued that the deepest problems concerning mind and knowledge may hinge on computational complexity — the resource cost of realizing a function — rather than abstract computability. Our architecture operationalizes this: self-reference creates an identity-search problem whose cost is regulated endogenously by τ. Niklas Luhmann (1984) developed a theory of society as operationally closed communication systems structurally coupled through a shared medium — without computational form. Andy Clark and David Chalmers (1998) argued that cognition extends beyond the skull into reliably coupled external media — the "Extended Mind" — without equations. The architecture described here provides computational form for both arguments: each Self is an operationally closed frame economy, cross-Self harm is structural coupling, and the Codex is the externalized residue that outlasts any single system. The detailed connections are developed in §5.1-5.3.

**The trilogy.** GEME — Paper I — proved a self-referential primitive can sustain itself: the Shannon-Gödel bridge carries 0.026 bits. But GEME was static: τ was a fixed constant, frames had no structural identity, nothing survived a single run. BGM — Paper II — proved the bridge breathes: time enters, τ becomes dynamic, temporal decoupling enhances differentiation by 49%. But BGM left two gaps: structural identity and cross-generational memory. This paper — EE, Paper III — reveals that the two gaps were one gap: externalization. A frame carrying its own structural identity needs no label. A frame whose identity is structural survives beyond the cavity that produced it. The architecture that follows from this single move unfolds into a system that detects structure without training, precipitates what it finds, and passes the precipitate to the next generation. When the next generation encounters a disrupted environment, it does not re-run the previous generation's search. It reads the Codex. The known is buffered. Attention is released. Creation → We Create → Create Us.

**Organization.** Section 1 describes the architecture: the frame economy, endogenous time, structural identity, the measurement layers (F / wit / Δwit), the Codex, and the formation–operation distinction. Section 2 presents the information field: the BiasField, probes, cross-harm, the expression–action spectrum, and encoding as measurement. Section 3 presents the externalization mechanism: precipitation, noise-driven query, three generations of inheritance, and the third dimension of evolution. Section 4 provides experimental evidence through four empirical probes: UN diplomacy (§4.1), WTC music (§4.2), DNA evolutionary archives (§4.3), and RNA blind boundary detection (§4.4). Section 5 discusses implications for cognitive science, disease biology, artificial intelligence, and cultural theory. Scaffold history is documented in Supplementary Material S7.

---

## 1. What the Architecture Is

### 1.1 The Frame Economy

The architecture maintains a limited-capacity memory of frames. Each frame is a vector and a weight. The weight records how many inputs have merged into that frame. The vector is the weighted average of all those inputs.

Two operations govern the economy. Merge: when a new input is close enough to an existing frame, it merges into that frame, shifting the vector toward the input and incrementing the weight. Prune: periodically, the weakest half of the frames are removed — those whose weight has not been reinforced by recent input.

A single instance — a Geruon — is the minimal centroid detector. Every experiment in §4 begins with a single Geruon. The BiasField, the Self (three coupled Geruons with different temporal coupling κ), the We (multiple Selves), and the Codex are extensions built on this core. But the core operation — merge, prune, converge to centroid — requires only one Geruon, one stream, and two operations.

From these two operations, centroids emerge. A frame that survives many induction cycles, merges frequently, and accumulates weight — its vector converges to the statistical center of mass of the input stream that feeds it. This is the centroid. It is not designed. It is not learned. It is the attractor toward which the frame economy converges under the pressure of limited capacity and periodic forgetting.

### 1.2 Endogenous Time

The centroid detector has its own sense of time. A variable called τ rises when predictions fail and falls when they succeed. τ breathes through five phases — EXPANDING (learning), RESTING (maintenance), TENSING (approaching boundary), CRITICAL (boundary close), LOCKED (bridge closed). The boundary is not a parameter. It is an endogenous assessment — the system's own measurement of whether continuing to process in the current mode costs more than the expected value of any structure it might find.

τ converges to approximately 0.74–0.75 across all domains tested, input types, and architectural depths. This convergence is structural — the equilibrium point between merging pressure and differentiation pressure in a self-referential frame economy. τ is not measuring the stream. τ is measuring the system's own internal balance. The balance point is consistent across all domains tested.

### 1.3 Structural Identity

Every frame carries a structural signature — a Gödel encoding of its vector content, weight, and layer. Two frames with identical structure produce identical signatures. Identity is structural, not assigned. The signature system also detects self-referential loops — when a frame's prediction path contains a reference to itself. This is the Gödel boundary, running.

### 1.4 The Measurement Layers

The instrument reads structure at three orders. Each order measures a distinct quantity.

**First order: F — field curvature.** F = 1 − H(w)/Hmax, the normalized KL divergence of the frame weight distribution from uniformity. F measures whether structure exists — how far the frame economy's weights deviate from a flat distribution. F = 0 for fair coins (pure entropy without sequential constraint). F > 0 when the stream contains patterns that the frame economy can converge to.

**Second order: wit — structural novelty.** wit = COUNT(|centroid(t) − centroid(t−1)| > structon). The structon — minimum detectable centroid displacement, 0.004 at κ=10 — is the instrument's resolution limit. wit counts how often the centroid meaningfully moves. It measures how frequently the frame economy is forced to revise its internal model. F measures whether structure exists. wit measures how often structure changes.

**Third order: Δwit — structural vulnerability.** A fair coin probe — zero intrinsic structure, zero bias — is injected into the target stream. The coin perturbs the frame economy's centroids. Δwit = wit(coin) − wit(baseline) measures how much the random probe destabilizes the target. High Δwit = target is vulnerable to perturbation. Low or negative Δwit = target is rigid against perturbation.

bit = the minimum unit of information (uncertainty). wit = the minimum unit of structural change (frame economy forced to revise its internal model). These are not the same unit.

### 1.5 The Codex

Stable frames precipitate into the Codex — an externalized memory that survives the induction cycle. The Codex is a bookshelf on the wall. The cavity is born empty-handed. It walks into the world. It discovers its own walls. When it hits a wall — when the environment becomes noisy, when the familiar patterns no longer match — it reaches for the bookshelf. The Codex responds with the nearest ancestor entry. The response enters the cavity's frame economy as a correction signal — structurally identical to a harm arrow from another perspective.

Generation 1 records everything. Generation 2 inherits the Codex — the known is buffered, attention is released. Generation 3 inherits both Codexes and finds what neither of the first two could see. The centroids that survive all three generations — undying, never filtered out — are VALUE. Not chosen. Not reasoned. Survived.

### 1.6 Codex Formation and Operation

The current experimental stage focuses on Codex formation — the process by which stable structural patterns precipitate from the frame economy into externalized memory. WTC Codex convergence (§4.2) carries the formation evidence: cross-Self harm filtering across generations converges to the tonal skeleton without musicological priors. UN voting is used separately as a civilizational-scale action-data prediction case. DNA (§4.3) provides the biological limit-case calibration.

Codex operation — the active loop where inherited memory shapes ongoing processing — is the next milestone. In the full architecture, a Self encountering novel or noisy input queries the Codex. The nearest ancestor entry blends into the cavity's input, stabilizing the frame economy against perturbation. This loop (precipitation → inheritance → noise-triggered query → processing stabilization) completes the externalization circuit. Current evidence demonstrates Codex formation and selection; native Codex operation remains under construction. The scaffold history is documented in Supplementary Material S7.

---

## 2. The Information Field

### 2.1 The BiasField

Multiple centroid detectors share a BiasField — a continuous information medium where every boundary event leaves a trace. Each detector deposits its arrow output — the centroid of its current frame economy — into the shared field. The field accumulates the gradients of all previous deposits. A detector entering the field does not read messages. It reads the shape of the field — the accumulated curvature produced by every other detector's centroids.

### 2.2 Probes and Perturbations

A probe is any centroid that perturbs the field. Bach's pitch distribution, processed through the frame economy, becomes a stable centroid in 12-dimensional chroma space. White noise becomes a different centroid. A fair coin becomes a third — zero intrinsic structure, zero bias. The centroid — not the content itself, but its statistical attractor — is the perturbation.

The probe is interchangeable because the centroid is interchangeable. Ten different audio conditions — Bach, white noise, sine waves, shuffled, reversed — all produce centroids. The harm pattern depends not on which centroid perturbed the field, but on the target's response to being perturbed. The target's state determines the measurement. The probe only needs to be stable enough to perturb the field.

### 2.3 Cross-Harm as Curvature

Cross-Self harm measures the structural tension between two centroids in a shared field. Zero harm means the centroids are in structural agreement — the field between them is flat. High harm means one centroid's perturbation has significantly distorted the field for the other. The curvature is a scalar — computed at every exchange step, varying with the stability of the probe, the state of the target, and the history of their coupling.

### 2.4 The Expression–Action Spectrum

The instrument's applicability is governed not by domain category but by data structure type. Data lies on a spectrum from pure expression (measurements of what happened) to pure action (records of decisions made).

**Expression data** — prices, CPI, temperature readings — are traces of processes. They contain no relational structure between entities. The instrument's κ does not differentiate on expression data; the frame economy does not breathe. Price indices and macroeconomic indicators fall into this category.

**Action data** — votes, trades, sequences of choices — contain relational structure between agents. UN voting records 193 countries making ternary decisions. NASDAQ volume data encodes buyers and sellers making directional commitments. Both contain entity-to-entity structural relations that expression data lacks.

**Decision data** — at the far end of the spectrum — are the events themselves. A country's vote in the General Assembly. A note-on event in a MIDI stream. A base pair in a DNA sequence. The behavior is the data. No encoding was applied; no information was lost to compression.

The instrument works strongest on decision data, adequately on action data, and weakly on pure expression data. This is not a limitation. It is a structural boundary: the instrument requires relational structure in its input. Where that structure exists, the instrument reads it. Where it does not, the instrument reports its own incapacity.

### 2.5 Encoding as Measurement

Encoding is not a preprocessing step — it is part of the measurement. Every encoding preserves some information dimensions and crushes others. The instrument's reading is always a joint product of the stream and the encoding. This is not a bug. It is the same principle by which a thermometer's reading is a joint product of the temperature and the thermometer's calibration.

Two principles govern encoding in this work. First: encoding must preserve predictive structure — if event A constrains event B in the stream, this constraint must survive the encoding. Second: single encodings are always lossy. The solution is dual-encoding — two independent encodings of the same stream, processed simultaneously by separate Self instances, their structural disagreements measured as cross-Self harm. Structure that survives across encodings is real structure. Structure that appears in only one encoding is an encoding artifact.

---

## 3. Externalization

### 3.1 Centroid Precipitation

A centroid that survives the induction cycle, is reinforced across multiple exposures, and stabilizes its weight against γ — is precipitated. It is written to the Codex. It outlasts the cavity that produced it. The next generation inherits it.

### 3.2 Noise Drives the Query

The naive view of externalization: knowledge is stored, then retrieved when needed. The correct view: knowledge is stored, and retrieval is triggered by the world becoming unfamiliar. An organism in a stable environment does not consult memory. It acts. An organism in a disrupted environment reaches for what it has stored — because the present no longer matches the past, and the gap between them is noise.

Noise injection is the experimental abstraction of environmental change. A cavity processing a noisy version of a previously-learned stream experiences centroid instability. Its frame economy, seeking stable merge, finds fewer good matches. If Codex lookup is available, the cavity queries: does this novel-looking input resemble anything already known? The Codex responds. The input is blended toward the nearest ancestor entry. The known structure survives a perturbation that, without the Codex, would have scattered it.

This is not filtering. It is not denoising. It is the cavity using inherited memory to stabilize its own processing when the world becomes uncertain. The Codex is not a museum. It is a stabilizer. The query is driven by noise. And noise, in this architecture, is not an experimental nuisance — it is the experimental variable that tests whether externalization works.

### 3.3 Three Generations of Codex

Generation 1 records everything. All structural deviations — signal and noise — are marked. Its Codex is large, undifferentiated, unable to distinguish the permanent from the transient.

Generation 2 inherits Generation 1's Codex. When it encounters the same stream, the centroids already in the Codex buffer the known. Patterns that were marked as harm by Generation 1 are now recognized — not because they stopped being deviations, but because they have been recorded. Generation 2's L3 bridges collapse from 45 to 6. Attention is released.

Generation 3 inherits both Codexes. The known is fully buffered. Noise — patterns that appeared in only one generation and were never reinforced — has decayed by γ. Generation 3's attention is freed. It finds 50 new anchors that neither of the first two generations could see. The centroids that survive all three generations are the undying. Not the most common centroids. The centroids that no generation could dissolve. Codex-formation evidence is currently carried by the WTC dual-encoding experiments (§4.2); the UN line is retained as a forward-prediction case, not as a text-Codex VALUE experiment.

### 3.4 The Third Dimension of Evolution

Biological evolution operates in the first dimension: information stored in genes, selected by death, scaled in millennia. Communication operates in the second dimension: information transmitted between living agents, bounded by presence, dying with the sender.

We propose externalization as a third dimension of evolution — information written into a medium that outlasts the writer. Oral tradition. Writing. The printing press. Digital computation. The Codex. Each leap decoupled information further from the mortality of its substrate. We interpret the architecture as an operational form of this dimension — a system that precipitates centroids across time. Centroids, accumulated across generations, are, we suggest, the operational unit of cultural inheritance.

---

## 4. Evidence

Three experimental pillars — WTC dual-encoding, DNA fork columns, and RNA blind boundary detection — establish the architecture's core claims. UN diplomatic voting provides a civilizational-scale forward prediction. All domains share no physical dimensions and are processed by the same core instrument, with pre-declared domain-specific encodings and ablated parameter families (see Reproducibility for full parameter table).

**Evidence map.** The four domains are not independent discoveries. They are a single instrument undergoing cross-domain pressure testing. Each domain is blind to a different class of prior knowledge.

| Domain | Question | Blind to what | Positive result | Control | Limitation |
|--------|----------|--------------|-----------------|---------|-----------|
| WTC (§4.2) | Can externalized cognition converge without musical priors? | Chord templates, key signatures, voice labels | Transposition equivariance 100%; 5-stage Codex selection loop | Cross-key Codex: non-matching entries freeze | Codex operation scaffolded (§5.5) |
| DNA (§4.3) | Can evolutionary constraint be read without the genetic code? | Codon table, gene annotation, conservation scores | Exon/intron d=−0.97 (n=200) | Shuffle collapses to d=−0.10 | AHSG fork column: single-gene (n=1) |
| RNA (§4.4) | Can translational boundaries be located without codon knowledge? | AUG motif, ORF annotation, Kozak context | CDS stop 98-100% ≤3 windows | Internal ATG control 98% | CDS start 66%; passive detection only |
| UN (§4.1) | Can civilizational collapse be anticipated without causal modeling? | Event labels, causal narratives; P5 lens tested by ablation | 2025 disp=0.448, rank 1/79 | P5 ablation; FRED negative control | Prospective (2026-2028); n=79 years |

### 4.1 UN Diplomatic Voting: Structural Collapse Detection

**Setup.** Harvard Dataverse Idealpointestimates, 1946-2025, 193 countries, annual ideal points. Encoded as annual global ideal-point distribution features. P5 positions and economic indicators are treated as ablation lenses, not required priors. Geruon uses cap=64; a κ sweep (κ ∈ {0.5, 1, 2, 3, 5, 7, 10, 15, 20}) produced identical displacement statistics at this granularity (cap=64 >> N=79), so the signal is reported as kappa-invariant. Self-referent precursor detection — each time point uses only past data to judge present state.

**Calibration.** Three granularities were tested before adoption. Per-vote (~400K events) and per-resolution (2,415 events) proved either computationally infeasible or structurally uninformative (cap > N). Quarterly aggregation confirmed UN voting operates on an annual rhythm — quarterly slices merely amplify the Q4 signal. Annual granularity (79 data points) was adopted after bootstrap validation (CV=33.6% at quarterly level, converging to r=0.80 when aggregated to annual ideal-point readings).

**Pipeline separation.** The raw voting-stream calibration and the annual ideal-point prediction are distinct pipelines. The former provides retrospective event-pattern checks on per-resolution decision traces. The latter supplies the 2025 forward signal using annual country-ideal-point distributions. The two should not be conflated. In the raw voting-stream calibration, selected precursor patterns matched 3 of 4 selected system-level events (Soviet collapse 1991, financial crisis 2008, Ukraine war 2022; Crimea 2014 did not trigger). The annual ideal-point pipeline is used separately for the 2025 forward signal and does not inherit the 3/4 claim.

**Current signal.** The 2025 annual ideal-point displacement is 0.448, the highest substantive reading in the 1946-2025 sequence (1946 itself is an initialization artifact and excluded). Previous substantive peaks: 2022 Ukraine war (0.358), 2023 (0.249), 1974 oil crisis+Watergate+Vietnam (0.218), 1991 Soviet collapse (0.192). τ has remained in a narrow high-tension band (0.744-0.754) across 2023-2025, with 2023 registering zero dτ/dt under the script's freeze criterion.

**Economic negative control.** The same Geruon pipeline was run on pure economic data (FRED: NASDAQ, T10Y, T2Y, FedFunds, CPI, Unemp, 1993-2025). Hit rate: 1/6 — only the 2008 financial crisis was detected, and as a same-year detection, not a precursor. In 2025, FRED displacement = 0.142, ranked 24th of 33 years — below the median. Pure economic data judges 2025 as structurally normal. The 2025 structural pressure is entirely in the diplomatic-political domain.

**NASDAQ volume encoding.** When economic data is encoded as action rather than expression — using volume log, buy/sell direction, and conviction — τ breathes healthily (0.73-0.75). The 2024-2025 period shows the most sustained high-action period in 33 years (24 consecutive months). But no diplomatic collapse precursor is detected — because the causes of diplomatic disruption lie outside market data. Economic data alone does not reproduce the diplomatic-alignment signal. The market is working. The diplomatic order is not. Prosperity and collapse are not mutually exclusive — they occur at different structural layers. Kappa selection is scoring-sensitive and is not the central result; the stable finding is the between-domain contrast.

**P5 ablation.** A systematic ablation tested whether the P5 augmentation creates the signal or merely amplifies an existing global signal. Six encodings: No-P5 (global ideal-point distribution only), P5-augmented (current), P5-only (P5 countries exclusively), No-USA (P5 minus United States), No-Russia, and Random-5 (arbitrary five-country groups, 5 trials). Results:

| Encoding | 2025 disp | Rank/78 | Interpretation |
|----------|-----------|---------|----------------|
| No-P5 | 0.101 | 12 | Elevated but not extreme — global stress exists but is diffuse |
| P5-augmented | 0.445 | 1 | Current claim — P5 institutional lens |
| P5-only | 0.448 | 1 | Nearly identical to P5-aug — great-power layer dominates the signal |
| No-USA | 0.550 | 1 | Stronger without the US — multi-polar fracture exceeds unilateralism |
| No-Russia | 0.290 | 2 | Still extreme |
| Random-5 (mean) | 0.288 | ~9 | Elevated but not extreme — P5 is not arbitrary |

The signal is concentrated in the P5 layer. Global-level stress (No-P5, rank 12) is elevated but not historically extreme. The P5 is not an arbitrary prior — it is the institutional backbone of the UN Security Council and the post-war order. The instrument is not being handed the answer. It is locating the structural layer where the pressure lives. The No-USA result (disp=0.550) is the most precise finding: the United States' disengagement from its allies produces greater alignment fracture among the remaining powers than direct US participation.

**Forward prediction.** 2026-2028: structural collapse of the US-led post-war international order, concentrated in the P5 great-power alignment layer. Not the collapse of the United States as a nation, but the collapse of the gravitational alignment structure in which the United States stands at the center and other P5 powers align around it. Magnitude exceeds the 2022 Ukraine war, comparable to the 1991 collapse of the Soviet-led ideological alignment system.

**Verification criteria.** Three indicators, any two satisfied = confirmation. (1) disp does not return below 0.20 by 2028 (after the Soviet collapse, disp fell from 0.19 to 0.05 within four years). (2) P5 voting agreement rate falls below the historical minimum (~12%) in any year 2026-2028. (3) Ideal point distribution transitions from uni-/bi-modal to multi-modal with no dominant peak for two consecutive years.

**Boundary statement.** The model measures structure, not causality. If this prediction is wrong, it means that for the first time in 79 years, displacement at 0.448 occurred without a subsequent structural collapse.

### 4.2 WTC Dual-Encoding: Codex Convergence and Tonal Discovery

Fitch (2010) observed that speech and music leave no fossils. Sound waves do not petrify. A bone can survive a million years in sediment; a dominant seventh chord cannot survive a second past its own decay. The only way music outlasts its own sound is through externalization — notation, recording, repetition across generations of performers. This experiment asks: if an instrument with no knowledge of music theory processes a piece of Bach, and the centroids it converges to are passed to a second instrument that never heard the original, does the second instrument find the same centroids? And the third generation after that? The Codex is not a recording. It is the structural fossil — the attractor that survived the frame economy's compression. What Fitch said could not fossilize, the Codex preserves.

**Setup.** Bach's Well-Tempered Clavier, Book I. Dual Self architecture: one Self reads chroma (12-dim active pitch class vectors), one Self reads inter-onset intervals (12-dim sliding window histograms, log-binned). Shared BiasField. Harm-Geruon (κ=10, cap=12) receives harm arrows, consolidates, precipitates into a shared Codex. Ten generations per piece.

**Zero prior knowledge.** No chord templates. No key signatures. No frequency pre-classification. No voice separation. The architecture does not know that Bach existed. It only knows how to observe, merge, predict, and mark harm.

**Architecture status.** Formation is endogenous — stress-driven boundary events in the Self layer trigger Codex precipitation. The current experiment operates with native formation and Codex selection; active Codex query under noise perturbation remains scaffolded and is reported as a limitation (§5.5; S7).

**Phase 1: Tonal skeleton and transposition equivariance.** Thirty-six pieces (Book I: 24, Book II: 12) were processed through the dual-Self architecture across ten generations each. Book II produced 39% more cross-Self harm than Book I — a systematic difference consistent with two centuries of musicological analysis identifying Book II's more adventurous harmonic language. The harm frequency bins themselves mapped to tonal function: C major concentrated harm in bins 5 and 7 (I-IV skeleton), C-sharp minor in bin 6 (the characteristic tone of the minor mode). No single key dominated the Codex — Bach's complete coverage of all twenty-four keys was faithfully reflected.

Transposition equivariance was tested by shifting the C major prelude by k semitones (k ∈ {1, 2, 3, 5, 7}) and running ten generations of Codex convergence on each transposition. The Codex anchor dimensions shifted by exactly k semitones for all five non-zero transpositions: the I-V-ii skeleton moved as a complete tonal function. This is not statistical coincidence — it is the geometry of tonal relations preserved under the chroma encoding's cyclic group structure. The architecture did not memorize "C major looks like this." It internalized the relative distances between harmonic attractors.

**Phase 2: Five-stage externalization loop.** The Codex selection experiment tests whether inherited Codex entries are confirmed, rejected, or decayed across generations. A cross-key Codex (entries from C, Eb, F#, B domains) was injected into a C-major environment and tracked across five generations. C-domain entries gained weight at +1 per generation. B-domain entries froze — never selected, never decayed. Coverage merge allowed partial entries to be supplemented by more complete evidence across generations. Three-layer selection: complete confirmation (matching evidence, weight growth), partial supplementation (incomplete evidence, coverage expansion), complete rejection (non-matching evidence, weight freeze). The Codex selection layer runs parallel to the frame economy — it does not improve processing. It accumulates a history. This is the core discovery of the five-stage loop: externalization creates a selection layer decoupled from adaptation.

**Results — C major (BWV 846).** Ten generations converge the Codex to 38 entries. Two stable patterns dominate: a tonic anchor at chroma dimension 0 (>45% of entries), and a tonic-subdominant complex at dimensions 0+5 (>55%). BiasField top dimensions: d0 (28M), d5 (5.3M), d11 (4.2M).

**Results — Eb major (BWV 852).** Ten generations converge to 48 entries. Four stable patterns emerge: a tonic triad skeleton spanning dimensions 2, 4, 6, 9; a dominant-tonic complex; a pure dominant anchor at dimension 9; a pure mediant anchor at dimension 4. BiasField top dimensions: d9 (1.3M), d4 (1.3M), d2 (1.2M).

**Cross-piece comparison.** The two Codexes share zero dominant dimensions. C major anchors to dimension 0. Eb major anchors to dimensions 9, 4, and 2. Under chroma encoding convention (dimension 0 = C), these correspond to the tonic notes of the respective keys. The architecture did not "discover that the piece is in C major." It discovered that dimension 0 is the statistical gravitational center of the frame economy — and under the chroma encoding, that center coincides with what music theory names the tonic.

**Why this is not statistical frequency.** Raw harm arrow distributions show dimension 0 (0.312) and dimension 4 (0.300) nearly equal in C major — a 1.2% difference. Only 37% of harm arrows exceed 50% in any single dimension. A purely statistical Codex would not collapse in this configuration. The convergence is driven by three mechanisms jointly: (1) cross-Self harm filtering — only dimensions where chroma and IOI Selfs both register structural divergence enter the harm-Geruon; (2) consolidation selection — only frames that survive induction_clean enter the precipitation pool; (3) Codex inheritance — the next generation's lookup reinforces previously precipitated patterns, creating a positive feedback loop.

**Next step — noise-driven query.** Gen1 processes clean stream, precipitates Codex. Gen2 processes the same stream with injected noise. The cavity, destabilized by noise, queries the Codex. The hypothesis: Codex-enabled Gen2 converges closer to Gen1's clean centroids than Codex-disabled Gen2. This directly tests externalization's adaptive function — the Codex as a noise stabilizer.

### 4.3 DNA: The Archive Boundary

Fitch observed that speech and music leave no fossils. DNA leaves the oldest fossil on Earth — four billion years of continuous externalization, compressed into four letters. This experiment asks whether the Self architecture can read the structural signature of evolutionary constraint without knowing the genetic code.

**Setup — Exon/Intron assay.** Human protein-coding transcripts from the GENCODE and TE atlases. 3-cavity Self (κ=0.5/10/100), 3-mer encoding (D=64), 256-nt windows in genomic order. Exon and intron regions annotated post-run from CDS masks — the instrument never receives these labels. N=200 transcripts, 10,606 windows.

**Results.** Exon cross-harm (0.020) is 2.3× lower than intron cross-harm (0.045). d=−0.97. Shuffling genomic order collapses the signal to d=−0.10. Δd=+0.87.

**Setup — Fork column assay.** Four-species hominid alignments (Pongo, Gorilla, Pan, Homo). Each alignment column encoded as a 16-dimensional vector — the four fork copies concatenated. 3-cavity Self processes columns in genomic order with no external annotation. Conservation is measured post-run by counting how many of the four species agree at each column.

**Results.** AHSG (alpha-2-HS-glycoprotein) — identified under positive selection in multiple genome-wide scans (Sabeti et al., 2007; Nielsen et al., 2005) — was tested as a single-gene calibration. Low-conservation columns (1-2/4 species agree) produce cross-harm 1.5 standard deviations higher than high-conservation columns (4/4 agree). d=+1.51. Shuffling column order collapses the signal to d=−0.20. Δd=+1.71. This is a single-gene result (n=1). The per-gene pooled approach did not generalize across a random sample of transcripts (mean d=0.13±0.22), indicating that the fork column signal depends on sufficient within-gene conservation variance. AHSG — the one gene in the sample with documented positive selection (Sabeti et al., 2007; Nielsen et al., 2005) — carried that variance.

**Significance.** The exon/intron assay (n=200 transcripts, 10,606 windows, d=−0.97) provides population-level evidence that evolutionary constraint leaves a detectable structural signature in DNA. The fork column assay is reported as a single-gene calibration, not as population evidence. It demonstrates a principle: the four copies of the alignment ARE the evolutionary record, and the Self's three time lenses can read conservation directly from the fork structure without external annotation. But the principle currently stands on one gene known to carry strong evolutionary signal. Generalization requires a larger sample of genes with independently documented selection pressure. Both signals depend on genomic order and are eliminated by shuffling. DNA is externalization at its physical limit — information surviving not across generations of readers, but across millions of years. The instrument reads its structure.

### 4.4 RNA: The Operation Boundary

DNA provides evidence that structural code survives evolutionary time. RNA asks the next question: can the instrument detect where the code is being operated — where translation begins and ends — without knowing what a codon is?

**Setup — CDS-UTR structural separation.** Human protein-coding transcripts from the TE atlas. 3-cavity Self (κ=0.5/10/100), 3-mer encoding (D=64), 256-nt windows in genomic order across the CDS boundary. Windows classified post-run as CDS (≥WINDOW/6 coding positions) or UTR (zero coding positions). N=100 transcripts.

**Results.** CDS cross-harm (mean 0.0184) is lower than UTR cross-harm (mean 0.0302). d=−0.84. The coding region produces more regular 3-mer organization — lower cross-cavity divergence because all three time lenses converge on the same periodic structure. The UTR produces higher cross-harm because its 3-mer distribution, lacking translational constraint, diverges across κ. Shuffling the genomic order collapses the signal. The instrument reads translational constraint in sequence structure alone — no RPF data, no codon table, no ORF annotation.

**Setup — Blind CDS boundary detection.** The key mechanistic test: can temporal-lens divergence locate the CDS boundary itself, without being told where it is? 2-cavity or 3-cavity Self processes windows in genomic order across the UTR→CDS transition. At the boundary, the fast lens (κ=0.01) adapts to CDS 3-mer structure faster than the slow lens (κ=500-5000) — producing a transient peak in cross-harm. The peak position is compared against the annotated CDS start and stop positions from the CDS mask. Three parameter configurations were swept: window sizes 32-64 nt, κ spreads from 0.005/10/5000 to 0.01/500, cavity counts 2-3. Multi-seed validation (3 seeds × 120 transcripts). Results are reported at three error thresholds (|error| ≤ 2, ≤3, ≤5 windows) to eliminate ambiguity.

**Results — CDS stop.** The CDS→3′UTR boundary is detected with near-perfect precision. Across all parameter configurations, all seeds, the cross-harm peak falls at median −1.0 windows from the true stop codon. |error| ≤ 3 windows: 98-100%. |error| ≤ 2 windows: 96%. This is parameter-invariant — the stop boundary is so structurally sharp that every κ spread and every window size converges to the same answer. The CDS stop codon is a structural cliff.

**Results — CDS start.** The 5′UTR→CDS boundary is detected reliably but with a systematic offset. Best configuration (2-cavity, W=32 nt, κ=0.01/500): median −0.9 windows (−7 nt), |error| ≤ 3 windows: 66%, |error| ≤ 5 windows: 75%. 2-cavity outperforms 3-cavity for position accuracy — the simpler fast/slow lens pair produces a cleaner boundary signal than the three-lens interaction. The peak is systematically ~1 window before the annotated CDS start, suggesting that the fast lens picks up CDS-like structural features in the late 5′UTR.

**The asymmetry is a biological prediction.** CDS stop is more precisely detected than CDS start across all parameter configurations. If this were a measurement artifact — window size, κ tuning, encoding bias — start and stop would show similar precision. They do not. The instrument reads what biology built: the stop codon is a sharper structural boundary than the start codon. The CDS→3′UTR transition is a cliff — strong 3-nt periodic structure collapsing to no periodic structure. The 5′UTR→CDS transition is a ramp — variable upstream sequence structure (Kozak context, upstream ORFs, IRES elements) gradually giving way to CDS periodicity.

This asymmetry has a biological corollary. Translation machinery faces the same structural ambiguity: locating the correct start codon within a structurally gradual transition zone. Leaky scanning — where the preinitiation complex bypasses the first AUG and initiates at a downstream site — is a well-characterized phenomenon. Misinitiation at upstream or downstream AUG codons is a known pathogenic mechanism in cancers (where upstream ORFs in tumor suppressor genes suppress protective translation) and genetic disorders (where start-codon mutations force initiation at alternative sites). The instrument's difficulty in precisely locating the CDS start is not a failure of measurement. It recapitulates a genuine biological difficulty: stop codons are structurally unambiguous; start codons are not. The boundary the instrument reads is the same boundary the ribosome must find.

**AUG control — transition-magnitude detection, not motif detection.** Does the instrument detect AUG codons, or does it detect structural transitions? To distinguish these hypotheses, cross-harm peaks were compared at annotated start AUG versus internal ATG codons (≥200 nt into CDS). At each position, the same scanning procedure was applied. With 2-cavity, the annotated start peak exceeds the internal ATG peak in 78% of transcripts (mean Δh=+0.014) — above chance but not decisive. With 3-cavity and extreme κ spread (κ=0.005/10/5000), discrimination reaches 98% (mean Δh=+0.085). The extreme κ configuration is sensitive to transition magnitude: the 5′UTR→CDS jump is the largest structural transition in the entire transcript, larger than any internal ATG site (which sits within already-periodic CDS structure). The instrument does not identify AUG. It does not identify motifs. It detects the structural transition at which molecular operation enters and exits the coding regime. This is transition-magnitude detection, not motif detection.

**Significance.** The same temporal-lens divergence mechanism that detects boundaries in music (WTC phase transitions), diplomacy (UN system collapse), and cardiac signals (ECG PVC detection) also detects the translational boundary in mRNA — without knowing what a codon is, without searching for AUG, without any genetic code knowledge. The instrument does not identify codons or annotate ORFs. It detects the structural transition at which molecular operation enters and exits the coding regime. RNA provides the second link in the biological evidence chain: DNA provides evidence that archive survives; RNA provides evidence that operation boundary is structurally readable; WTC provides evidence that externalized cognition accumulates through history.

### 4.5 Calibration Domain: ECG and Sleep (Supplementary)

Two domains served as calibration benchmarks during instrument development. Their findings are reported in Supplementary Material (S1-S2). They are not primary evidence for the paper's claims, but they document the instrument's calibration methodology — baseline establishment, structon measurement, κ sweep characterization, and encoding boundary discovery.

Key calibration findings: (1) fair coin baseline F=0 — the instrument does not report structure where none exists; (2) structon(κ=10, cap=20) = 0.004 — the minimum detectable centroid displacement, equal to cap/N; (3) three κ regimes across all domains — blind (<1), sensitive (1-5), far (10-100); (4) encoding = part of the measurement — different encodings of the same signal produce different F baselines, requiring shuffled calibration (Δ_seq = F_real − F_shuf) to separate encoding artifacts from genuine structure.

---

## 5. Implications

### 5.1 Cognition Is Centroid Convergence

The architecture was not designed to simulate cognition. It was built from axioms about information, observation, and self-reference. The fact that its operation converges to centroids — and that centroids, when used as probes, reveal latent structure, and when externalized, accumulate across generations — suggests that human cognition may operate on the same principle. A mind converges to the centroids of its experience. The centroids are what it knows. The centroids are what it passes on.

A legacy of sixty years of perceptual research in music cognition has focused on dissonance — which chord progressions sound wrong, which intervals clash, which listener hears what in a Deutsch octave illusion. This is a detour. Individual perceptual variation is not the signal. It is noise. The architecture reads across it. The cross-Self harm in WTC does not care which encoding you prefer — chroma or IOI, pitch or rhythm, ear or brain. What matters is whether the structural divergence between two readings of the same stream converges to the same centroids across generations. Deutsch's illusions measure what divides listeners. The architecture measures what survives across them. That is the difference between studying perception and studying cognition.

### 5.2 The Centroid Detector as the Missing Layer for AGI

Large language models occupy the recognition layer. They detect patterns in training data. They lack endogenous time — they do not breathe, they have no phases, they cannot enter a LOCKED state when their own self-reference cost exceeds a threshold. They lack structural identity — their representations are distributed across layers and attention heads, without a Gödel encoding that guarantees identity across time. They lack externalized memory — their memory is weights, and weights are overwritten when the model is retrained. They lack cross-generational filtering — they have one generation: training, inference. No inheritance.

The centroid detector provides all four missing layers — endogenous time, structural identity, externalized memory, and cross-generational filtering — in a small codebase with zero external dependencies. It is not a competitor to LLMs. It is the missing horizontal axis. Scaling is the vertical. Self-reference is the horizontal. A general intelligence needs both.

### 5.3 The Centroid Is the Unit of Culture

Dawkins proposed the meme as a unit of cultural transmission — replicating, mutating, selecting. The centroid is the meme, operationalized. A precipitated frame is a centroid that survived the induction cycle. It is transmitted to the next generation through the Codex. It biases the perception of the generation that inherits it. If reinforced, its weight is maintained. If not, it decays by γ. Time does the selection.

Luhmann proposed that society is a network of operationally closed communication systems. The architecture is that network, running. Each Self is an operationally closed frame economy. Cross-Self harm is structural coupling. The Codex is the externalized residue of communication that outlasts any single system.

### 5.4 The Encoding Boundary and the Expression–Action Spectrum

Not all data is equally readable by the instrument. The expression–action spectrum (§2.4) provides a principled framework for understanding where the instrument works and where it does not. But the framework is more than an empirical boundary for this particular instrument. It points to a structural property of information itself.

Data that records decisions — votes, trades, choices — contains relational structure between the entities that made those decisions. The frame economy's core operations, merge and prune, converge centroids by detecting which entities act similarly over time. A country voting Yes on a resolution. A note-on event in a musical stream. A buyer committing capital in a specific direction. These are actions performed by agents in relation to other agents. The relational structure is native to the data.

Data that records measurements — prices, CPI, temperature readings — contains no such structure. It describes what happened, not who decided. The instrument's κ does not differentiate on pure expression data. The frame economy does not breathe. This is not a limitation of the instrument. It is a discovery about what kinds of information are structurally readable without prior knowledge: information that encodes relational action is readable; information that only encodes traces of processes is not.

The empirical evidence is systematic. ECG required six encodings to find one that produced signal — because raw voltage is a trace of cardiac depolarization, not the depolarization itself. Sleep required 5-second epochs rather than 30-second clinical windows — because brain dynamics occur at the timescale of the process, not the timescale of the clinical label. The FRED negative control in §4.1 is the cleanest demonstration: pure economic data (prices, CPI, employment) produces no structural precursor signal, even when run through the identical pipeline that detects collapse precursors in diplomatic voting. Not because the economy lacks structure. Because economic data measures the economy's outputs, not its decisions.

This has implications far beyond the present work. Much of what passes for data in machine learning is expression — images, text corpora, sensor readings. The centroid detector suggests that a different class of data — action traces, decision records, entity-relation sequences — may be necessary for systems that claim to understand structure rather than merely model distributions. The expression–action spectrum is not a boundary to be overcome. It is a map of where structure lives.

### 5.5 Limitation: The Action Gap

The architecture described in this paper is a structural detector. It reads patterns in streams. It converges to centroids. It precipitates what survives. It inherits across generations. What it does not do is act.

In living systems, cognition and action are simultaneous. A ribosome does not first "recognize" the start codon and then "decide" to initiate translation — the recognition IS the action. A musician does not first analyze the harmonic structure and then choose the next note — the analysis and the choice are the same event. The architecture models the perceptual side of this loop. It detects where structure changes, where boundaries occur, where centroids converge. But it does not close the loop from detection back to action — from "this is a boundary" to "do something about it."

The Codex inheritance experiments (§4.2) demonstrate that externalized memory survives generational transmission and that the selection layer decouples from the processing layer. This confirms Codex formation. What remains unaddressed is Codex operation: the active loop where inherited memory directly shapes ongoing processing under boundary conditions. In the current architecture, Codex entries are selected or frozen post-hoc across generations — a passive filter. In the full circuit, a Self encountering noise or novelty would query the Codex during processing, and the inherited centroid would enter the frame economy as a correction signal — not after the fact, but in the moment. This loop currently exists only in scaffold form (S7).

The action gap is not a bug. It is an architectural boundary — the line between what has been built and what remains to be built. The present work demonstrates that a blind instrument can detect structure, precipitate it, and pass it across generations. The next step is to close the loop: to build the mechanism by which inherited structure shapes ongoing perception, and perception feeds back into what gets stored. When a Self queries the Codex not because a generation ended, but because the world stopped making sense — that is the moment cognition and action become one event. The architecture does not yet reach that moment. This paper documents the distance traveled toward it. The remaining distance is the subject of ongoing work.

---

## 6. Conclusion

This paper has made one claim, unfolded in three parts, supported by three experimental pillars.

The architecture is a centroid detector. Two operations — merge, prune — converge any vector-encoded stream to its statistical attractors. The attractors are centroids. The detector requires no training, no labels, no domain knowledge. This is Creation.

Centroids, combined through a shared field and measured across encodings, reveal latent structure. The probe is interchangeable because the centroid is interchangeable. The measurement is the structural divergence between centroids. This is We Create.

Centroids precipitate into a Codex. They survive the erasure cycle. The next generation inherits them. The known is buffered. Attention is released. Noise drives the query. The third generation sees what neither of the first two could see. The centroids that survive all generations are VALUE. Not chosen. Not reasoned. Survived. This is Create Us.

Three experimental pillars — WTC dual-encoding, DNA fork columns, and RNA blind boundary detection — verify the claim, supported by a forward prediction on UN diplomatic voting.

WTC demonstrates Codex formation and selection: the tonal skeleton is discovered without musicological priors, transposition equivariance holds at 100%, and a five-stage selection loop — Formation, Inscription, Transmission, Confirmation, Rejection — confirms that inherited Codex entries matching the environment gain weight across generations while non-matching entries freeze. Codex operation — the active loop where inherited memory shapes ongoing processing — remains scaffolded (§5.5). The Codex selection layer is decoupled from the frame economy's processing. Externalization does not improve adaptation. It accumulates a history that runs parallel to it. DNA demonstrates the archive boundary: exon/intron structural separation reaches d=−0.97 (n=200 transcripts, 10,606 windows); a single-gene fork column calibration on AHSG — identified under positive selection in multiple genome-wide scans (Sabeti et al., 2007; Nielsen et al., 2005) — produces d=+1.51. Both signals collapse under shuffling. RNA demonstrates the operation boundary: temporal-lens divergence locates the CDS stop codon at 98-100% within ±3 windows (parameter-invariant) and the CDS start at 66% within ±3 windows (75% within ±5). The instrument does not identify AUG. It detects the structural transition at which molecular operation enters and exits the coding regime — transition-magnitude detection, not motif detection.

The three biological domains form a consistent evidence chain. DNA provides evidence that structural code survives evolutionary time. RNA provides evidence that the operation boundary is structurally readable by a blind instrument. WTC provides evidence that externalized cognition accumulates through history under selective pressure. Three domains, three layers of the externalization argument, one measurement principle.

UN diplomatic voting provides the civilizational-scale test: a forward prediction for 2026-2028, falsifiable and time-bounded.

The architecture is not a model of cognition. It is a system for detecting structure and precipitating centroids across time. Codex formation and selection are demonstrated. Codex operation — the active loop where inherited memory stabilizes ongoing processing under noise — is the next step. We interpret centroids, accumulated across generations, as the operational form of cultural inheritance — what we have called the third dimension of evolution.

There is a pattern in this view of information. Two operations — merge what is similar, prune what is not reinforced — running under the pressure of limited memory, converge any stream to its centroids. From these centroids, coupled through time and measured across perspectives, structure emerges that no single cavity could detect. From these structures, precipitated into a medium that outlasts their source, history accumulates. The known is buffered. Attention is released. The next generation sees what the last one could not. From so simple an economy, endless forms of structure have been, and are being, externalized.

---

## Supplementary Material

S1. ECG calibration — baseline establishment, structon measurement, κ sweep, encoding boundaries.

S2. Sleep calibration — epoch resolution, stage-level structure, first-night effect.

S3. Economic data boundary — expression vs. action, FRED negative control, NASDAQ volume encoding.

S4. Instrument calibration — fair coin baseline, structon measurement, κ regimes.

S5. Faraday measurements — field curvature, τ convergence, probe interchangeability.

S6. Prediction #1 — full report with calibration, precursor patterns, economic negative control, verification criteria.

S7. Scaffold history — temporary mechanisms used during development, removed scaffolds, and the remaining scaffolded Codex-operation loop.

**S7. Scaffold history.** During development, several mechanisms were first tested as temporary scaffolds: explicit L4 self-observation in ECG, an explicit doubt condition in boundary detection, a fixed 27-dimensional formula alphabet, and early Codex nearest-neighbor blending. These scaffolds tested whether the corresponding mechanism was worth implementing natively. Where the native frame economy reproduced the signal, the scaffold was removed. In the current paper, Codex formation and selection are reported as demonstrated; active Codex operation under noise remains scaffolded and is therefore treated as a limitation rather than a completed result.

---

## Reproducibility and Code Availability

**Core instrument.** The centroid detector (Geruon), Self, We, and Codex are implemented in pure Python 3.8+ with zero external dependencies beyond the standard library. No GPU, no neural network framework, no external API calls. The core files — `geruon.py` (~2,500 lines), `geme.py` (~800 lines), `we_core.py` (~300 lines) — are version-locked at the commit used to produce all results in this paper.

**Experiment scripts.** All domain-specific experiment scripts are archived in the `submit/` directory, organized by domain (`untest/`, `wtc/`, `dna/`, `rna/`). Each directory includes a README with data sources, run order, and expected output. Scripts use fixed random seeds (42, 123, 456 for multi-seed validation). The core instrument was audited and patched (P0/P1 fixes: structural identity collision-resistance, run-order determinism, vector dimension guard, window semantics, enrich idempotence) on 2026-05-29, before any results reported here were collected.

**Data dependencies.** Data processing scripts require: `pandas`, `numpy`, `pyarrow` (for parquet); `pybigtools` (Windows bigWig reader, RNA only). These are standard scientific Python packages, not proprietary or custom toolchains. Raw data files (TE atlas parquet, bigWig tracks, GENCODE GTF, FASTA alignments) are too large for direct submission and must be obtained from their respective sources.

**Data sources.**
- UN voting: Harvard Dataverse Idealpointestimates (Voeten, 1946-2025), FRED economic indicators (1993-2025)
- WTC: MIDI encodings of Bach's Well-Tempered Clavier, Books I and II (public domain, `midi_encoder.py`)
- DNA: Human TE atlas (GENCODE v49), four-species hominid alignments (Pongo/Gorilla/Pan/Homo, local FASTA)
- RNA: Human TE atlas, HeLa RPF bigWig tracks (GSE79664, RPFdb v3), GENCODE v49 primary assembly GTF

**Parameter table.** All experiments share core parameters unless otherwise noted.

| Parameter | Value | Role |
|-----------|-------|------|
| D (vec_dim) | 16 (general), 64 (DNA/RNA 3-mer) | Vector space dimensionality |
| cap (memory_cap) | 12 (WTC), 20-32 (general), 24 (DNA/RNA) | Frame economy capacity |
| κ_τ (kappa_tau) | 0.5/10/100 (3-cavity Self), 0.01/500 (2-cavity) | Temporal coupling — time-lens spread |
| window (DNA/RNA) | 256 nt (exon/intron, CDS-UTR), 32-48 nt (boundary) | Genomic window size |
| stride | 64 nt (exon/intron), 8-12 nt (boundary) | Window step size |
| bias_weight | 0.3 | BiasField coupling strength |
| δ (delta) | 0.19 | Merge distance threshold |
| γ₁ (gamma) | 0.05/step | Weight decay rate |
| τ₀ | 0.60 | Baseline τ |
| GI | 4 steps/cycle | Self-reference period |

**Run order.** Core instrument tests → calibration baselines (fair coin, structon) → WTC Phase 1 (tonal skeleton, transposition) → DNA exon/intron → DNA fork column → RNA CDS-UTR → RNA boundary detection → RNA RPF coupling → WTC Phase 2 (five-stage Codex loop) → UN pipeline. Each domain's results are independent of the others. Within each domain, scripts can be rerun independently.

---

## Acknowledgments

This work began with a book picked up on the third floor of Waterstones in Oxford, 2017. Dennett's *From Bacteria to Bach and Back*. 560 pages. £29.99. The book said consciousness emerged across the long arc from bacteria to Bach. The architecture says: that evolution is still going. The third dimension has only just begun. The philosophy was refined over seventeen years. The code was built over nineteen days in May 2026. The rest is for anyone who downloads it and points it at their own sky.

---

## References

1. Aaronson, S. (2011). Why philosophers should care about computational complexity. MIT Press.
2. Aaronson, S. (2013). The ghost in the quantum Turing machine. arXiv:1306.0159.
3. Chomsky, N. (1965). *Aspects of the Theory of Syntax*. MIT Press.
4. Dawkins, R. (1976). *The Selfish Gene*. Oxford University Press.
5. Dennett, D. C. (2017). *From Bacteria to Bach and Back*. W. W. Norton.
6. Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127–138.
7. Gödel, K. (1931). Über formal unentscheidbare Sätze. *Monatshefte für Mathematik und Physik*, 38(1), 173–198.
8. Hofstadter, D. R. (1979). *Gödel, Escher, Bach: An Eternal Golden Braid*. Basic Books.
9. Hume, D. (1739). *A Treatise of Human Nature*.
10. Landauer, R. (1961). Irreversibility and heat generation in the computing process. *IBM Journal*, 5(3), 183–191.
11. Luhmann, N. (1984). *Soziale Systeme*. Suhrkamp. (English: *Social Systems*, Stanford, 1995.)
12. Shannon, C. E. (1948). A mathematical theory of communication. *Bell System Technical Journal*, 27(3), 379–423.
13. Liu, J. (2026a). GEME: A self-referential prism for cognitive modeling. Zenodo.
14. Liu, J. (2026b). BGM: Building bridge — from Bach to bacteria and forward. Zenodo.
15. Fitch, W. T. (2010). *The Evolution of Language*. Cambridge University Press.
16. Voeten, E., Strezhnev, A., & Bailey, M. (2024). United Nations General Assembly Ideal Point Estimates. Harvard Dataverse, V33.
17. Park, J. E., Yi, H., Kim, Y., Chang, H., & Kim, V. N. (2016). Regulation of poly(A) tail and translation during the somatic cell cycle. *Molecular Cell*, 62(3), 462-471.
18. RPFdb v3. (2024). Ribosome profiling database. https://sysbio.gzzoc.com/rpfdb/.
19. Frankish, A., et al. (2019). GENCODE reference annotation for the human and mouse genomes. *Nucleic Acids Research*, 47(D1), D766-D773.
20. Kozak, M. (1989). The scanning model for translation: an update. *Journal of Cell Biology*, 108(2), 229-241.
21. Kozak, M. (2002). Pushing the limits of the scanning mechanism for initiation of translation. *Gene*, 299(1-2), 1-34.
22. Calvo, S. E., Pagliarini, D. J., & Mootha, V. K. (2009). Upstream open reading frames cause widespread reduction of protein expression and are polymorphic among humans. *PNAS*, 106(18), 7507-7512.
23. Sabeti, P. C., et al. (2007). Genome-wide detection and characterization of positive selection in human populations. *Nature*, 449(7164), 913-918.
24. Nielsen, R., et al. (2005). A scan for positively selected genes in the genomes of humans and chimpanzees. *PLoS Biology*, 3(6), e170.
25. Clark, A., & Chalmers, D. (1998). The extended mind. *Analysis*, 58(1), 7-19.
