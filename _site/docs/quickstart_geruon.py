"""Geruon Quick Start — runnable demo with Faraday readings (F, wit)."""
from pathlib import Path
import sys, math
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from geruon import Geruon

N, DIM, CAP, KAPPA = 120, 16, 20, 0.5
g = Geruon(vec_dim=DIM, memory_cap=CAP, kappa_tau=KAPPA, structon=0.004)

def make_stream(n=N, dim=DIM):
    for i in range(n):
        block = (i // 30) % 4
        vec = [0.0] * dim
        vec[block] = 1.0
        vec[(block + 1) % dim] = 0.25
        yield vec, f"block_{block}_{i}"

print(f"{'step':>5}  {'tau':>6}  {'phase':<8}  {'frames':>6}  {'util':>6}  {'comp':>6}  {'F':>6}")
for vec, sig in make_stream():
    g.process_vec(vec, sig)
    if g._input_count % 30 == 0 or g._input_count <= 1:
        m = g.metrics()
        phase_short = m['phase'][:8] if isinstance(m['phase'], str) else str(m['phase'])[:8]
        print(f"{m['input_count']:>5}  {m['tau']:>6.3f}  {phase_short:<8}  "
              f"{m['frame_count']:>6}  {m['utilization']:>5.2f}  "
              f"{m.get('compression_ratio',0):>5.1f}  {m['F']:>6.3f}")

m = g.metrics()
print(f"\nsummary")
print(f"inputs:       {m['input_count']}")
print(f"frames:       {m['frame_count']} / {m['capacity']}")
print(f"tau:          {m['tau']:.3f}")
print(f"phase:        {m['phase']}")
print(f"F:            {m['F']:.3f}")
print(f"wit_hits:     {m['wit_hits']}")
print(f"wit_rate:     {m['wit_rate']}")
print(f"arrow length: {len(g.arrow_output())}")
print(f"arrow norm:   {math.sqrt(sum(v*v for v in g.arrow_output())):.3f}")
print(f"\nOK: Geruon processed the stream and produced metrics.")
