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

Place MIDI files in `data/wtc/`. The encoder produces 12-dim chroma vectors and 12-dim IOI histograms.

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
