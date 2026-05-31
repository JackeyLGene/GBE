"""EE Self Quick Start — 3-cavity cross-harm demo."""
from pathlib import Path
import sys, math
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from geruon import Geruon, BiasField

N, DIM, CAP = 120, 16, 24
bias = BiasField(vec_dim=DIM)
cavities = [
    Geruon(vec_dim=DIM, memory_cap=CAP, kappa_tau=0.5,  bias_field=bias),
    Geruon(vec_dim=DIM, memory_cap=CAP, kappa_tau=10.0, bias_field=bias),
    Geruon(vec_dim=DIM, memory_cap=CAP, kappa_tau=100.0,bias_field=bias),
]

def make_stream(n=N, dim=DIM):
    for i in range(n):
        block = (i // 30) % 4
        vec = [0.0] * dim
        vec[block] = 1.0
        vec[(block + 1) % dim] = 0.25
        yield vec, f"block_{block}_{i}"

harms = []
print(f"{'step':>5}  {'harm':>8}  {'tau_fast':>8}  {'tau_mid':>8}  {'tau_slow':>8}")
for i, (vec, sig) in enumerate(make_stream()):
    for g in cavities:
        g.process_vec(vec, sig)
    cs = [g.memory.centroid() for g in cavities]
    cs = [c for c in cs if c is not None]
    if len(cs) >= 2:
        harm = sum(
            math.sqrt(sum((cs[a][k]-cs[b][k])**2 for k in range(DIM)))
            for a in range(len(cs)) for b in range(a+1, len(cs))
        ) / (len(cs) * (len(cs)-1) / 2)
        harms.append(harm)
        if i % 30 == 0 or i <= 1:
            print(f"{i:>5}  {harm:>8.4f}  {cavities[0].tau:>8.3f}  "
                  f"{cavities[1].tau:>8.3f}  {cavities[2].tau:>8.3f}")

print(f"\nsummary")
print(f"inputs:       {N}")
print(f"harm samples: {len(harms)}")
print(f"harm mean:    {sum(harms)/len(harms):.4f}" if harms else "no harms")
print(f"harm max:     {max(harms):.4f}" if harms else "")
print(f"bias count:   {bias._count}")
print(f"\nOK: 3-cavity Self produced a cross-harm series.")
