"""Shepard scale — phase transition / inflection point detection.

Look for qualitative shifts in Geruon's behavior as the paradox develops:
  1. τ phase transitions (EXPANDING→RESTING→TENSING→CRITICAL→LOCKED)
  2. Abrupt change in τ autocorr(lag=12) strength
  3. Frame economy reorganization (new frames appearing rate)
  4. Centroid stability transition
"""
import math, random, os, sys, io
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'code'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from geruon import Geruon, BiasField, GAMMA, TAU_0, PHASE_RESTING_CEIL, PHASE_TENSING_CEIL

# ── Generate Shepard stream ──
def generate_shepard_stream(n_octaves=30, steps_per_octave=12):
    stream = []
    for i in range(n_octaves * steps_per_octave):
        ca = (i % 12) * 2 * math.pi / 12
        h = i / steps_per_octave
        stream.append([
            math.sin(ca)*0.4+0.5, math.cos(ca)*0.4+0.5,
            h/n_octaves, (h//1)/n_octaves,
        ])
    return stream

# ── Phase classification ──
def classify_phase(tau, dtaudt):
    """Classify Geruon's phase state from τ and dτ/dt."""
    if tau < 0.55: return 'EXPAND'
    if abs(dtaudt) < 0.0001: return 'RESTING'
    if tau < 0.65: return 'TENSING'
    if tau < 0.75: return 'CRITICAL'
    return 'LOCKED'

# ── Run with detailed tracking ──
N_OCTAVES = 30
stream = generate_shepard_stream(n_octaves=N_OCTAVES)
print(f'Shepard: {len(stream)} steps ({N_OCTAVES} octaves)')
print()

g = Geruon(vec_dim=4, memory_cap=16, kappa_tau=3.0)
bf = BiasField(vec_dim=4)

# Detailed tracking
tau_hist = []
phase_hist = []
dtaudt_hist = []
frame_count_hist = []
new_frame_hist = []  # new frames created per step
centroid_chroma_hist = []  # chroma angle of centroid
autocorr_sliding = []  # sliding autocorr(lag=12)

for i, vec in enumerate(stream):
    base = list(vec)
    if not bf.is_empty():
        base = bf.blend_into(base, weight=GAMMA)

    n_frames_before = len(g.memory.frames)
    g.process_vec(base, 'shepard')
    n_frames_after = len(g.memory.frames)

    arrow = list(g.arrow_output())
    bf.deposit(arrow, weight=0.2)

    tau_hist.append(g.tau)
    dtaudt_hist.append(g.dtaudt)
    phase_hist.append(classify_phase(g.tau, g.dtaudt))
    frame_count_hist.append(len(g.memory.frames))
    new_frame_hist.append(n_frames_after - n_frames_before)

    # Centroid chroma angle
    ca = math.atan2(g.arrow_output()[0]-0.5, g.arrow_output()[1]-0.5)
    centroid_chroma_hist.append(ca)

    # Sliding autocorr at lag=12 (window=60)
    if i >= 60:
        window = tau_hist[i-60:i+1]
        wm = sum(window)/len(window)
        num = sum((window[t]-wm)*(window[t-12]-wm) for t in range(12, len(window)))
        den = sum((w-wm)**2 for w in window)
        ac12 = num / max(0.001, den)
        autocorr_sliding.append(ac12)
    else:
        autocorr_sliding.append(0)

# ── Find inflection points ──
print('=== Phase timeline ===')
# Compress to octave-level summary
for octave in range(0, N_OCTAVES + 1, 3):
    start = octave * 12
    end = min(start + 36, len(stream))
    if start >= len(stream): break
    seg_tau = tau_hist[start:end]
    seg_phase = phase_hist[start:end]
    seg_new = new_frame_hist[start:end]
    seg_ac = autocorr_sliding[start:end]

    # Dominant phase in this segment
    from collections import Counter
    phase_counts = Counter(seg_phase)
    dom_phase = phase_counts.most_common(1)[0][0]

    print(f'oct {octave:2d}-{min(octave+3, N_OCTAVES):2d}: tau={sum(seg_tau)/len(seg_tau):.4f} '
          f'ac12={sum(seg_ac)/len(seg_ac):+.3f} '
          f'new_frames={sum(seg_new)/len(seg_new):.2f}/step '
          f'phase={dom_phase} ({dict(phase_counts)})')

# ── Detect qualitative shifts ──
print()
print('=== Inflection point detection ===')

# 1. When does autocorr at lag=12 first exceed 0.3?
ac_threshold = 0.3
ac_onset = None
for i, ac in enumerate(autocorr_sliding):
    if ac > ac_threshold and i > 24:
        ac_onset = i
        break
print(f'Chroma lock-on (ac12 > {ac_threshold}): step {ac_onset} (octave {ac_onset//12 if ac_onset else "N/A"})')

# 2. When does new frame rate drop below 0.1/step?
nf_onset = None
for i in range(30, len(new_frame_hist)):
    rate = sum(new_frame_hist[i-30:i]) / 30
    if rate < 0.1 and nf_onset is None:
        nf_onset = i
        break
print(f'Frame economy stabilizes (new<0.1/step): step {nf_onset} (octave {nf_onset//12 if nf_onset else "N/A"})')

# 3. Phase transitions
phase_changes = []
for i in range(1, len(phase_hist)):
    if phase_hist[i] != phase_hist[i-1]:
        phase_changes.append((i, phase_hist[i-1], phase_hist[i]))
print(f'Phase transitions: {len(phase_changes)} total')
for pc in phase_changes[:10]:
    print(f'  step {pc[0]:4d} (oct {pc[0]//12:2d}): {pc[1]:>8} -> {pc[2]:<8}')
if len(phase_changes) > 10:
    print(f'  ... ({len(phase_changes)-10} more)')
# Show last few
for pc in phase_changes[-5:]:
    print(f'  step {pc[0]:4d} (oct {pc[0]//12:2d}): {pc[1]:>8} -> {pc[2]:<8}')

# 4. τ derivative sign change (dτ/dt crosses zero)
dtau_crossings = []
for i in range(1, len(dtaudt_hist)):
    if dtaudt_hist[i-1] * dtaudt_hist[i] < 0:
        dtau_crossings.append(i)
print(f'\ndτ/dt zero crossings: {len(dtau_crossings)}')
# Distribution across octaves
crossings_by_octave = {}
for c in dtau_crossings:
    oct = c // 12
    crossings_by_octave[oct] = crossings_by_octave.get(oct, 0) + 1
print('Crossings per octave:')
for oct in sorted(crossings_by_octave.keys())[:15]:
    bar = '|' * crossings_by_octave[oct]
    print(f'  oct {oct:2d}: {crossings_by_octave[oct]:2d} {bar}')

# 5. When does τ enter LOCKED phase (τ > 0.75) for the first time?
locked_onset = None
for i, t in enumerate(tau_hist):
    if t > 0.75:
        locked_onset = i
        break
print(f'\nFirst LOCKED (τ > 0.75): step {locked_onset} (octave {locked_onset//12 if locked_onset else "N/A"})')

# ── The key inflection: when does the paradox "lock" the system? ──
print()
print('=' * 60)
print('KEY INFLECTION: Paradox Lock Point')
print('=' * 60)

# The paradox lock point = when chroma autocorr stabilizes above 0.5
# AND τ has reached its plateau AND new frame rate is near zero
lock_candidates = []
for i in range(60, len(autocorr_sliding)-12):
    ac_stable = all(autocorr_sliding[i+j] > 0.5 for j in range(12))
    tau_stable = abs(tau_hist[i] - tau_hist[-1]) < 0.01
    nf_low = sum(new_frame_hist[i-20:i]) / 20 < 0.05
    if ac_stable and tau_stable and nf_low:
        lock_candidates.append(i)
        break  # just need the first one

if lock_candidates:
    lock_point = lock_candidates[0]
    print(f'Paradox lock point: step {lock_point} (octave {lock_point//12})')
    print(f'  τ = {tau_hist[lock_point]:.4f}')
    print(f'  ac12 = {autocorr_sliding[lock_point]:+.3f}')
    print(f'  phase = {phase_hist[lock_point]}')
    print(f'  new_frame_rate = {sum(new_frame_hist[lock_point-20:lock_point])/20:.3f}/step')
else:
    print('No clear lock point found — paradox may never fully "lock"')
    # Find the closest approach
    best_i = max(range(60, len(autocorr_sliding)),
                key=lambda i: autocorr_sliding[i] - abs(tau_hist[i] - tau_hist[-1])*10)
    print(f'Closest approach: step {best_i} (oct {best_i//12})')
    print(f'  τ={tau_hist[best_i]:.4f}, ac12={autocorr_sliding[best_i]:+.3f}')

print('\nOK: Shepard phase analysis completed.')
