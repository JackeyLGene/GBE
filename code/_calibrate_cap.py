"""CALIB-cap: Sine wave quantization → effective capacity.

Generate sine wave quantized at different bit depths:
  2-bit → 4 distinct values per period
  3-bit → 8 distinct values
  4-bit → 16 distinct values
  ...
  8-bit → 256 distinct values

Geruon with cap=N should track streams with ≤N distinct states.
When distinct_states > cap, frames overflow → pred_err jumps.

Measure: for each cap, at what bit depth does pred_err cross threshold?
This gives: effective_capacity(cap) = max distinct states tracked.
"""
import math, random, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from geruon import Geruon, GAMMA, TAU_0

def quantize_sine(t, period, bits):
    """Quantize sin(2π·t/period) to 2^bits levels in [0,1]."""
    raw = math.sin(2 * math.pi * t / period) * 0.45 + 0.5  # [0.05, 0.95]
    levels = 2 ** bits
    quantized = round(raw * (levels - 1)) / (levels - 1)
    return quantized

def generate_stream(period, bits, n_steps, d=1):
    """Generate a 1D sine wave stream at given bit depth."""
    return [[quantize_sine(i, period, bits)] for i in range(n_steps)]

def run_cap_test(cap, bits, period=20, n_steps=500):
    """Run Geruon on a quantized sine stream. Return steady-state pred_err."""
    stream = generate_stream(period, bits, n_steps, d=1)
    g = Geruon(vec_dim=1, memory_cap=cap, kappa_tau=3)

    pred_errs = []
    for i, vec in enumerate(stream):
        g.process_vec(vec, 'sine')
        # pred_err = distance to nearest frame (internal surprise)
        frames = g.memory.frames
        if len(frames) >= 2:
            # Distance between latest input and closest frame
            min_dist = min(
                math.sqrt(sum((vec[j] - f.vec[j])**2 for j in range(min(len(vec), len(f.vec)))))
                for f in frames[:-1]  # exclude the frame just created
            ) if len(frames) > 1 else 1.0
            pred_errs.append(min_dist)
        else:
            pred_errs.append(0.0)

    # Steady-state pred_err (last 200 steps, after τ has converged)
    steady = pred_errs[-200:] if len(pred_errs) > 200 else pred_errs[100:]
    mean_pe = sum(steady) / len(steady)

    # Also track n_frames (how many distinct frames are maintained)
    final_n_frames = len(g.memory.frames)

    # Distinct values in frame economy (based on quantized vec values)
    frame_vals = set()
    for f in g.memory.frames:
        if f.weight > 0.01 and len(f.vec) > 0:
            frame_vals.add(round(f.vec[0], 4))
    n_distinct = len(frame_vals)

    return mean_pe, final_n_frames, n_distinct


# ── Run calibration ──
CAPS = [4, 6, 8, 10, 12, 16, 20, 24, 32]
BITS = [1, 2, 3, 4, 5, 6, 7, 8]  # 2^1=2 to 2^8=256 distinct values
PERIOD = 20
N_STEPS = 500
N_REPS = 3

print(f'CALIB-cap: Sine Wave Quantization')
print(f'Period={PERIOD}, {N_STEPS} steps, {N_REPS} reps')
print(f'Bits: {BITS} → distinct values: {[2**b for b in BITS]}')
print(f'Caps: {CAPS}')
print()

# Collect results
results = {}
for cap in CAPS:
    cap_results = {}
    for bits in BITS:
        reps = []
        for rep in range(N_REPS):
            pe, nf, nd = run_cap_test(cap, bits, period=PERIOD, n_steps=N_STEPS)
            reps.append((pe, nf, nd))
        cap_results[bits] = reps
    results[cap] = cap_results

# ── Report: pred_err by (cap, bits) ──
print('=== pred_err (steady-state mean) ===')
print(f'{"cap\\bits":<8}', end='')
for b in BITS:
    print(f'{("b="+str(b)):>10}', end='')
print(f'{"states=":>10}', end='')
for b in BITS:
    print(f'{2**b:>10}', end='')
print()
for cap in CAPS:
    print(f'{cap:<8}', end='')
    for b in BITS:
        reps = results[cap][b]
        pe = sum(r[0] for r in reps) / len(reps)
        # Mark if PE is elevated (overflow indicator)
        marker = ''
        print(f'{pe:10.4f}', end='')
    print()

# ── Capacity detection: first bit where PE jumps > 2× baseline ──
print()
print('=== Effective capacity (first bit where PE > 2× baseline) ===')
print(f'{"cap":<8} {"max_bits":>10} {"max_states":>12} {"PE_baseline":>12} {"PE_jump":>12}')
for cap in CAPS:
    baseline_pe = sum(r[0] for r in results[cap][1]) / N_REPS  # 1-bit = 2 states
    threshold = baseline_pe * 2.0
    max_bits = 1
    for b in BITS:
        pe = sum(r[0] for r in results[cap][b]) / N_REPS
        if pe <= threshold:
            max_bits = b
    max_states = 2 ** max_bits
    jump_pe = sum(r[0] for r in results[cap][BITS[-1]]) / N_REPS if len(BITS) > max_bits else 0
    print(f'{cap:<8} {max_bits:>10} {max_states:>12} {baseline_pe:>12.4f} {jump_pe:>12.4f}')

# ── Detail: n_frames and n_distinct for key (cap, bits) ──
print()
print('=== Frame detail (n_frames / n_distinct) ===')
print(f'{"cap\\bits":<8}', end='')
for b in BITS:
    print(f'{("b="+str(b)):>12}', end='')
print()
for cap in CAPS:
    print(f'{cap:<8}', end='')
    for b in BITS:
        reps = results[cap][b]
        nf = sum(r[1] for r in reps) / len(reps)
        nd = sum(r[2] for r in reps) / len(reps)
        print(f'{nf:5.0f}/{nd:4.0f}', end=' ')
    print()

# ── TEST 2: Random unique values (no temporal pattern) ──
print()
print('=' * 60)
print('TEST 2: Random unique values — pure storage capacity')
print('=' * 60)

def run_random_cap_test(cap, n_unique, n_steps=400, d=2):
    """Feed N unique random vectors in random order, repeating.
    No temporal pattern — Geruon must store each unique vector to predict.
    When n_unique > effective cap, pred_err jumps."""
    # Generate N unique random vectors
    random.seed(42)
    unique_vecs = []
    for _ in range(n_unique):
        unique_vecs.append([random.random() for _ in range(d)])

    # Stream: random order, each appears ~n_steps/n_unique times
    stream = []
    for i in range(n_steps):
        stream.append(list(unique_vecs[i % n_unique]))

    # Shuffle to avoid periodic pattern
    import random as rnd
    rnd.seed(123)
    rnd.shuffle(stream)

    g = Geruon(vec_dim=d, memory_cap=cap, kappa_tau=3)

    pred_errs = []
    for vec in stream:
        g.process_vec(list(vec), 'rand')
        frames = g.memory.frames
        if len(frames) >= 2:
            min_dist = min(
                math.sqrt(sum((vec[j] - f.vec[j])**2 for j in range(min(d, len(f.vec)))))
                for f in frames[:-1]
            ) if len(frames) > 1 else 1.0
            pred_errs.append(min_dist)
        else:
            pred_errs.append(0.0)

    steady_pe = sum(pred_errs[-150:]) / 150 if len(pred_errs) > 150 else sum(pred_errs) / len(pred_errs)
    n_distinct = len(set(round(f.vec[0], 4) for f in g.memory.frames if f.weight > 0.01 and len(f.vec) > 0))
    return steady_pe, n_distinct

N_UNIQUES = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32]
print(f'Unique values: {N_UNIQUES}')
print(f'{"cap\\K":<8}', end='')
for k in N_UNIQUES:
    print(f'{("K="+str(k)):>8}', end='')
print()
for cap in [4, 6, 8, 10, 12, 16, 20, 24, 32]:
    print(f'{cap:<8}', end='')
    for k in N_UNIQUES:
        pe, nd = run_random_cap_test(cap, k)
        # Mark if PE elevated
        print(f'{pe:8.4f}', end='')
    print()

# Capacity: find K where pred_err crosses absolute threshold
print()
print('Effective capacity (K where PE crosses threshold):')
for threshold in [0.03, 0.05, 0.08, 0.10]:
    print(f'\n  Threshold = {threshold:.2f}:')
    for cap in [4, 6, 8, 10, 12, 16, 20, 24, 32]:
        max_k = 2
        for k in N_UNIQUES:
            pe, _ = run_random_cap_test(cap, k)
            if pe <= threshold:
                max_k = k
        efficiency = max_k / cap
        bar = '▓' * int(efficiency * 20)
        print(f'    cap={cap:>3} → K_max={max_k:>3} ({efficiency*100:5.0f}% eff) {bar}')

# ── Calibration curve: required cap vs distinct states ──
print()
print('=== Calibration curve: cap → max distinct states ===')
for cap in CAPS:
    max_bits = 1
    baseline_pe = sum(r[0] for r in results[cap][1]) / N_REPS
    for b in BITS:
        pe = sum(r[0] for r in results[cap][b]) / N_REPS
        if pe <= baseline_pe * 2.0:
            max_bits = b
    print(f'  cap={cap:>3} → tracks up to {2**max_bits:>4} distinct states ({max_bits}-bit sine)')
