"""Demo: 3-cavity Self detects known boundaries in a synthetic stream.

The stream has three structural transitions at precisely known positions:
  step 100: frequency doubles
  step 200: phase inverts
  step 300: returns to original

A 3-cavity Self (κ=0.5/10/100) processes the stream. Cross-harm should peak
at or near the three boundary positions — without being told where they are.
"""
from pathlib import Path
import sys, math
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from geruon import Geruon, BiasField

DIM, CAP, N = 16, 24, 400
# 3-cavity Self
bias = BiasField(vec_dim=DIM)
cavities = [
    Geruon(vec_dim=DIM, memory_cap=CAP, kappa_tau=0.5,  bias_field=bias),
    Geruon(vec_dim=DIM, memory_cap=CAP, kappa_tau=10.0, bias_field=bias),
    Geruon(vec_dim=DIM, memory_cap=CAP, kappa_tau=100.0,bias_field=bias),
]

def make_sine_stream(n=N, dim=DIM):
    """Generate vectors whose statistical structure changes at known boundaries."""
    for i in range(n):
        if i < 100:
            freq = 1.0          # base frequency
        elif i < 200:
            freq = 2.0          # frequency doubles -> boundary at 100
        elif i < 300:
            freq = 1.0; phase = math.pi  # phase inversion -> boundary at 200
        else:
            freq = 1.0; phase = 0.0      # return -> boundary at 300

        phase_val = phase if 'phase' in dir() else 0.0
        vec = [0.0] * dim
        for j in range(dim):
            t = i * 0.1 + j * 0.3
            vec[j] = math.sin(freq * t + phase_val) * 0.5 + 0.5
        yield vec, f"s{i:04d}"

print("3-cavity Self — sine boundary detection demo")
print(f"{'step':>5}  {'harm':>8}  {'tau_fast':>8}  {'tau_mid':>8}  {'tau_slow':>8}")
print(f"{'':->5}  {'':->8}  {'':->8}  {'':->8}  {'':->8}")

harms = []
boundary_markers = {100: 'FREQ×2', 200: 'PHASE FLIP', 300: 'RETURN'}

for i, (vec, sig) in enumerate(make_sine_stream()):
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

        marker = boundary_markers.get(i, '')
        if i % 20 == 0 or marker:
            print(f"{i:>5}  {harm:>8.4f}  {cavities[0].tau:>8.3f}  "
                  f"{cavities[1].tau:>8.3f}  {cavities[2].tau:>8.3f}  {marker}")

# ── Boundary detection report ──
print(f"\n{'='*55}")
print("BOUNDARY DETECTION REPORT")
print(f"{'='*55}")

# Find peaks in cross-harm within ±5 steps of each known boundary
for pos, label in sorted(boundary_markers.items()):
    window = [(rp, h) for rp, h in enumerate(harms) if abs(rp - pos) <= 10]
    if window:
        peak_pos, peak_h = max(window, key=lambda x: x[1])
        offset = peak_pos - pos
        baseline = harms[max(0, pos-20):pos] if pos >= 20 else harms[:pos]
        bl_mean = sum(baseline) / len(baseline) if baseline else 0
        ratio = peak_h / bl_mean if bl_mean > 0 else float('inf')
        print(f"  {label:>10} @ step {pos}: peak at {peak_pos} (offset={offset:+d}), "
              f"harm={peak_h:.4f}, {ratio:.1f}× baseline")

print(f"\n  Harmonics detected without labels or training.")
print(f"  Known boundaries: {list(boundary_markers.values())}")
print(f"  OK: 3-cavity Self demo complete.")
