# GBE Demos

Two zero-dependency demos. Each runs in under 10 seconds. Python 3.8+ stdlib only.

## Demo 1: Sine Boundaries → 3-cavity Self

```powershell
python demo\demo_self_sine.py
```

A synthetic stream with three known structural boundaries (frequency doubling at step 100, phase inversion at step 200, return at step 300). A 3-cavity Self (κ=0.5/10/100) processes the stream blind. Cross-harm peaks at or near all three boundary positions — without being told where they are.

**What to watch:** the cross-harm column. It should spike near steps 100, 200, and 300. The "BOUNDARY DETECTION REPORT" at the end compares detected peaks against known positions.

## Demo 2: Bach C Major Prelude → Solo Geruon

```powershell
python demo\demo_geruon_bach.py
```

Bach's BWV 846 (C major prelude) encoded as 12-dim chroma vectors. A solo Geruon (κ=5) processes 1,648 windows. Watch tau breathe between TENSING and LOCKED, F (field curvature) respond to harmonic density, and phase transitions mark structural tension — without knowing what a chord is, what a key is, or that Bach existed.

**What to watch:** the tau column oscillating between ~0.74 (TENSING) and ~0.75 (LOCKED). The F column rising during harmonically dense passages. The `|` bars showing active pitch classes per window.

## Files

| File | Purpose |
|------|---------|
| `demo_self_sine.py` | 3-cavity Self boundary detection on synthetic data |
| `demo_geruon_bach.py` | Solo Geruon breathing on real music |
| `bwv846.mid` | Bach C major prelude (public domain) |

## Expected Output

Both demos end with `OK:` and a summary line. The sine demo prints a boundary detection report comparing detected peaks against known positions. The Bach demo prints final tau, F, phase, and confirmation that it processed the prelude.
