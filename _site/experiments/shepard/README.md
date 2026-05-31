# Shepard Scale Paradox — Bridge Experiment

A zero-data bridge between the quickstarts and the four paper experiments.

The Shepard scale contains two incompatible structures in one stream:

- chroma closes every 12 semitone steps
- pitch height keeps drifting upward

Geruon reads this as a structural contradiction. The useful signature is not a classification score; it is phase behavior: CRITICAL/LOCKED flicker, chroma-period tau structure, and over-anchoring onto the predictable chroma circle.

## Run

```powershell
python experiments\shepard\_shepard.py
python experiments\shepard\_shepard_phase.py
python experiments\shepard\_shepard_window.py
```

All three scripts use only Python stdlib plus the core instrument in `code/`.

## Scripts

| Script | Purpose |
|--------|---------|
| `_shepard.py` | Main three-condition comparison: Shepard vs chroma-only vs height-only |
| `_shepard_phase.py` | Phase-transition timeline and first LOCKED/flicker detection |
| `_shepard_window.py` | Co-occurrence-window scan; paradox strongest near one chroma circle |

## Expected Results

- Shepard produces tau autocorrelation at lag 12, showing the chroma circle remains visible.
- Shepard reaches higher final tau than either pure control: over-anchoring, not confusion.
- The phase analysis detects CRITICAL/LOCKED flicker after the contradiction becomes established.
- The window scan shows the paradox is measurement-scale dependent.

Full interpretation: [docs/experiment-shepard-paradox.md](../../docs/experiment-shepard-paradox.md).
