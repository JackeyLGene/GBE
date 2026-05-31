# Bach Well-Tempered Clavier — §4.2

Externalized cognition and Codex convergence. Dual-encoding Self (chroma + IOI) on Bach's WTC Book I & II. Zero musicological priors.

## Scripts

| Script | Purpose | Runtime |
|--------|---------|---------|
| `_wtc_dual.py` | Dual-Self processing (chroma + IOI). Cross-harm time series. Tonal skeleton discovery. Transposition equivariance test. | ~2min/piece |
| `_wtc_phase2_evo.py` | Five-stage Codex evolution loop. Cross-key Codex selection (C/Eb/F#/B). 10 generations. | ~5min/piece |

## Data

- MIDI encodings of Bach WTC Book I (24 pieces) and Book II (12 pieces)
- Encoded via `midi_encoder.py` in `code/`
- MIDI files: public domain, available from multiple sources (Mutopia, KunstderFuge)

The frozen scripts read pre-encoded files from the repo-root data directory:

- `data/wtc_pieces/wtc_00.pkl`, `data/wtc_pieces/wtc_01.pkl`, ...
- `data/wtc_phase2/codex_true_cap12.json`
- `data/wtc_phase2/codex_wrong_cap12.json`

Raw MIDI files can be placed in `data/wtc/` and encoded with `code/midi_encoder.py`; the encoder produces 12-dim chroma vectors and 12-dim IOI histograms.

## Run Order

```powershell
cd experiments\wtc
python _wtc_dual.py             # Phase 1: tonal skeleton + transposition
python _wtc_phase2_evo.py       # Phase 2: five-stage Codex loop
```

## Dependencies

`numpy`, `pandas`. Core instrument: `code/geruon.py`, `code/geme.py`, `code/we_core.py` (stdlib only). MIDI parsing: `code/midi_encoder.py`.

## Key Results

- Transposition equivariance: 100% (I-V-ii skeleton shifts by exactly k semitones for all non-zero k)
- Five-stage Codex loop: Formation → Inscription → Transmission → Confirmation → Rejection
- C major Codex: 38 entries, tonic anchor at chroma dim 0 (>45%)
- Eb major Codex: 48 entries, tonic triad skeleton spanning dims 2,4,6,9
- Cross-key: non-matching entries freeze, never decay. Selection layer decouples from frame economy.

## What Didn't Work

- **Solo Geruon on WTC**: blind — no signal (< 1 L3 bridge across 48 pieces). Required Self amplifier to detect structure.
- **BiasField inheritance**: zero effect at all α (0.05-5.0). Normalization flattens inherited gradient. Transmission must go through Codex.
- **Group classification**: r(L3, PVC%) = 0; r(F, PVC%) ≤ 0.5. Instrument measures organization, not pathology labels.
- **Codex operation**: still scaffolded. Formation and selection are native; active query under noise remains manual.
