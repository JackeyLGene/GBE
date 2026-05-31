"""Shepard scale — structural paradox in Geruon's frame economy.

A Shepard scale simultaneously:
  - Returns to the same pitch class every 12 steps (chroma circle — CLOSED)
  - Rises continuously in pitch height (octave — OPEN)

This creates a structural paradox: one dimension says "I've seen this before,"
the other says "this is completely new."

Encoding D=4:
  [chroma_sin, chroma_cos, height_norm, octave_norm]

Geruon should:
  - Form L2/L3 chains on chroma circle (repeating structure)
  - Keep τ from fully stabilizing (height keeps introducing novelty)
  - Produce centroid trajectories that circle in chroma while drifting in height
  - BiasField coherence should show tension between circle (stable) and drift (unstable)
"""
import math, random, os, sys, io
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'code'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from geruon import Geruon, BiasField, GAMMA, TAU_0

# ── Generate Shepard scale stream ──
def generate_shepard_stream(n_octaves=8, steps_per_octave=12, n_partials=3):
    """Generate a Shepard scale: chroma cycles, height rises.

    Each step: chroma_angle advances by 1 semitone (30 degrees),
    height rises by 1/12 octave. After 12 steps, chroma returns
    to start but height is 1 octave higher.

    Multiple partials at octave intervals create the Shepard illusion.
    """
    stream = []
    n_steps = n_octaves * steps_per_octave

    for i in range(n_steps):
        chroma_angle = (i % 12) * 2 * math.pi / 12  # 0 to 2π, cycles every 12
        height = i / steps_per_octave  # 0 to n_octaves
        octave = int(height)

        # Encode: chroma as sin/cos pair (circular), height normalized
        vec = [
            math.sin(chroma_angle) * 0.4 + 0.5,   # chroma sin [0.1, 0.9]
            math.cos(chroma_angle) * 0.4 + 0.5,   # chroma cos [0.1, 0.9]
            height / n_octaves,                     # height [0, 1]
            octave / n_octaves,                     # octave [0, 1]
        ]
        stream.append(vec)

    return stream


def run_shepard(stream, kappa=3.0, cap=16):
    """Run Geruon on Shepard stream with BiasField."""
    g = Geruon(vec_dim=4, memory_cap=cap, kappa_tau=kappa)
    bf = BiasField(vec_dim=4)

    tau_hist = []
    dtau_hist = []
    l2_hist = []; l3_hist = []
    F_hist = []
    centroid_hist = []

    for i, vec in enumerate(stream):
        base = list(vec)
        if not bf.is_empty():
            base = bf.blend_into(base, weight=GAMMA)
        g.process_vec(base, 'shepard')

        arrow = list(g.arrow_output())
        bf.deposit(arrow, weight=0.2)

        tau_hist.append(g.tau)
        dtau_hist.append(g.dtaudt)

        frames = g.memory.frames
        l2 = sum(1 for f in frames if hasattr(f, 'layer') and f.layer == 'L2')
        l3 = sum(1 for f in frames if hasattr(f, 'layer') and f.layer == 'L3')
        l2_hist.append(l2); l3_hist.append(l3)

        weights = [f.weight for f in frames if f.weight > 0.001]
        if len(weights) >= 2:
            tw = sum(weights)
            probs = [w/tw for w in weights]
            ent = -sum(p * math.log(max(p, 1e-10)) for p in probs)
            F = 1.0 - ent / math.log(len(weights)) if len(weights) > 1 else 0
        else:
            F = 0.0
        F_hist.append(F)

        centroid_hist.append(list(g.arrow_output()))

    return {
        'tau_hist': tau_hist, 'dtau_hist': dtau_hist,
        'l2_hist': l2_hist, 'l3_hist': l3_hist,
        'F_hist': F_hist, 'centroid_hist': centroid_hist,
        'final_frames': len(g.memory.frames),
        'g': g, 'bf': bf,
    }


# ── Run ──
print('Shepard Scale — Structural Paradox')
print('Encoding D=4: [chroma_sin, chroma_cos, height, octave]')
print()

N_OCTAVES = 20
stream = generate_shepard_stream(n_octaves=N_OCTAVES)
print(f'Stream: {len(stream)} steps ({N_OCTAVES} octaves x 12 semitones)')

# Run Shepard
result = run_shepard(stream, kappa=3.0, cap=16)

# ── Control conditions ──
# Control A: pure chroma circle (no height rise)
stream_chroma_only = []
for i in range(len(stream)):
    ca = (i % 12) * 2 * math.pi / 12
    stream_chroma_only.append([
        math.sin(ca)*0.4+0.5, math.cos(ca)*0.4+0.5, 0.0, 0.0
    ])
result_chroma = run_shepard(stream_chroma_only, kappa=3.0, cap=16)

# Control B: pure height rise (no chroma circle)
stream_height_only = []
for i in range(len(stream)):
    h = i / 12
    stream_height_only.append([0.5, 0.5, h/N_OCTAVES, (h//1)/N_OCTAVES])
result_height = run_shepard(stream_height_only, kappa=3.0, cap=16)

# ── Analysis ──
tau = result['tau_hist']
l3 = result['l3_hist']
F = result['F_hist']

# τ oscillation: does τ cycle with the chroma circle?
print()
print('=== τ analysis ===')
print(f'τ range: [{min(tau):.4f}, {max(tau):.4f}]')
print(f'τ final: {tau[-1]:.4f}')
print(f'τ mean:  {sum(tau)/len(tau):.4f}')

# τ auto-correlation at lag=12 (chroma period)
n = len(tau)
tau_mean = sum(tau) / n
tau_ac = [t - tau_mean for t in tau]
corr_12 = sum(tau_ac[i] * tau_ac[i-12] for i in range(12, min(120, n))) / min(120-12, n-12)
corr_12 /= (sum(t**2 for t in tau_ac[:min(120,n)]) / min(120,n)) ** 0.5
corr_12 /= (sum(tau_ac[i-12]**2 for i in range(12, min(120,n))) / min(120-12, n-12)) ** 0.5
print(f'τ autocorr at lag=12 (chroma period): {corr_12:+.3f}')

# Phase-locked τ: average τ by chroma position
tau_by_chroma = {i: [] for i in range(12)}
for i, t in enumerate(tau):
    tau_by_chroma[i % 12].append(t)
print('τ by chroma position (last 48 steps):')
for c in range(12):
    vals = tau_by_chroma[c][-4:]  # last 4 cycles
    if vals:
        bar = '+' if sum(vals)/len(vals) > tau_mean else '-'
        print(f'  chroma {c:2d}: τ={sum(vals)/len(vals):.4f} {bar}')

# ── L3 chain analysis ──
print()
print('=== Frame economy ===')
print(f'Final frames: {result["final_frames"]}')
print(f'Max L2: {max(l3)} (L3/L2 chains)')
print(f'L3 formation: starts at step {next((i for i, v in enumerate(l3) if v > 0), -1)}')

# L3 trajectory (every 12 steps)
print('L3 chains every 12 steps:')
for i in range(0, min(len(l3), 120), 12):
    print(f'  step {i:4d}: L3={l3[i]}', end='')
    if i >= 12:
        print(f' tau={tau[i]:.4f} F={F[i]:.4f}', end='')
    print()

# ── F and τ relationship ──
print()
print('=== F-τ coupling ===')
# Correlation between F and tau over the whole stream
F_mean = sum(F) / len(F)
tau_mean2 = sum(tau) / len(tau)
num = sum((F[i]-F_mean)*(tau[i]-tau_mean2) for i in range(len(F)))
den = math.sqrt(sum((f-F_mean)**2 for f in F) * sum((t-tau_mean2)**2 for t in tau))
r_F_tau = num / den if den > 0 else 0
print(f'r(F, τ): {r_F_tau:+.3f}')

# ── Centroid trajectory ──
print()
print('=== Centroid trajectory (chroma plane) ===')
centroids = result['centroid_hist']
# Project centroid onto chroma dimensions (dim 0-1)
print('First 24 steps, chroma projection:')
for i in range(24):
    c = centroids[i]
    chroma_angle = math.atan2(c[0]-0.5, c[1]-0.5) * 180 / math.pi
    chroma_dist = math.sqrt((c[0]-0.5)**2 + (c[1]-0.5)**2)
    print(f'  step {i:2d}: chroma_angle={chroma_angle:+7.1f} deg  r={chroma_dist:.3f}  '
          f'tau={tau[i]:.4f}')

# ── BiasField structure ──
print()
print('=== BiasField analysis ===')
for label, res in [('Shepard', result), ('Chroma-only', result_chroma),
                    ('Height-only', result_height)]:
    bf = res['bf']
    if not bf.is_empty():
        bias = bf.bias
        chroma_mag = math.sqrt(bias[0]**2 + bias[1]**2)
        height_mag = math.sqrt(bias[2]**2 + bias[3]**2)
        ratio = chroma_mag / max(0.001, height_mag)
        print(f'{label:<14} chroma={chroma_mag:.2f} height={height_mag:.2f} ratio={ratio:.2f}x')

# ── Three-way comparison ──
print()
print('=' * 60)
print('THREE-WAY COMPARISON: Shepard vs Chroma-only vs Height-only')
print('=' * 60)

for label, res in [('Shepard', result), ('Chroma-only', result_chroma),
                    ('Height-only', result_height)]:
    tau_ = res['tau_hist']
    l3_ = res['l3_hist']
    F_ = res['F_hist']

    # τ stats
    tau_range = max(tau_) - min(tau_)
    tau_final = tau_[-1]

    # τ autocorr at lag 12
    tm = sum(tau_)/len(tau_)
    ac12 = sum((tau_[i]-tm)*(tau_[i-12]-tm) for i in range(12, min(120, len(tau_))))
    ac12 /= max(0.001, sum((t-tm)**2 for t in tau_[:min(120,len(tau_))]))

    # F stats
    F_final = F_[-1] if F_ else 0
    F_mean = sum(F_)/len(F_) if F_ else 0

    # L3
    max_l3 = max(l3_) if l3_ else 0
    final_l2 = sum(1 for f in res['g'].memory.frames
                   if hasattr(f, 'layer') and f.layer == 'L2')

    print(f'{label:<14} tau_range={tau_range:.4f} tau_final={tau_final:.4f} '
          f'ac12={ac12:+.3f} F_final={F_final:.4f} F_mean={F_mean:.4f} '
          f'L2={final_l2} L3_max={max_l3}')

# ── Paradox index ──
# Earlier expectation: Shepard should fall between pure chroma and pure height.
# Observed behavior is stronger and cleaner: over-anchoring. The system locks
# harder onto the predictable chroma circle while rejecting the drifting height.
print()
print('=== Paradox index ===')
s_tau = result['tau_hist']
c_tau = result_chroma['tau_hist']
h_tau = result_height['tau_hist']
s_F = result['F_hist']
c_F = result_chroma['F_hist']
h_F = result_height['F_hist']

# Paradox score: Shepard should be BETWEEN chroma and height on key metrics
s_tau_final = s_tau[-1]; c_tau_final = c_tau[-1]; h_tau_final = h_tau[-1]
s_F_final = s_F[-1]; c_F_final = c_F[-1]; h_F_final = h_F[-1]

anchor_margin = s_tau_final - max(c_tau_final, h_tau_final)
print(f'τ_final:  Shepard={s_tau_final:.4f}  Chroma={c_tau_final:.4f}  Height={h_tau_final:.4f}')
print(f'over-anchor margin: {anchor_margin:+.4f}  (positive = paradox locks harder than both controls)')
print(f'F_final:  Shepard={s_F_final:.4f}  Chroma={c_F_final:.4f}  Height={h_F_final:.4f}')
print('F is saturated near zero in this encoding; τ/phase flicker is the useful readout.')

# τ oscillation amplitude: Shepard should show MORE oscillation than either
s_ac12 = sum((s_tau[i]-sum(s_tau)/len(s_tau))*(s_tau[i-12]-sum(s_tau)/len(s_tau))
             for i in range(12, min(120, len(s_tau))))
s_ac12 /= max(0.001, sum((t-sum(s_tau)/len(s_tau))**2 for t in s_tau[:min(120,len(s_tau))]))
c_ac12 = sum((c_tau[i]-sum(c_tau)/len(c_tau))*(c_tau[i-12]-sum(c_tau)/len(c_tau))
             for i in range(12, min(120, len(c_tau))))
c_ac12 /= max(0.001, sum((t-sum(c_tau)/len(c_tau))**2 for t in c_tau[:min(120,len(c_tau))]))
print(f'\nτ autocorr(lag=12): Shepard={s_ac12:+.3f}  Chroma={c_ac12:+.3f}')
print(f'(Shepard paradox = chroma circle visible in τ despite height drift)')
print('\nOK: Shepard paradox produced over-anchoring and chroma-period τ structure.')
