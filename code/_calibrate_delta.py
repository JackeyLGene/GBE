"""CALIB-δ: Merge threshold — with controlled noise.

Two clusters A and B at fixed separation d.
Add Gaussian noise σ to each value.
Vary σ from 0 to d*2. At some σ, the clusters overlap enough
that Geruon merges them → n_distinct drops from 2 to 1.

The critical σ/d ratio = effective δ (in units of cluster separation).

Also test: pure sine wave-bit concept for δ.
One sine wave, quantized. As bit depth DECREASES (coarser quantization),
adjacent values get closer → Geruon should merge them at some bit depth.
"""
import math, random, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from geruon import Geruon, GAMMA, TAU_0

# ═══════════════════════════════════════════════════
# TEST A: Two clusters + noise → merge at critical σ
# ═══════════════════════════════════════════════════

def run_noise_test(separation, noise_sigma, cap=16, n_steps=600):
    """Feed A=0.3+noise, B=0.3+sep+noise alternating.
    Measure n_distinct frames."""
    vec_a_center = 0.3
    vec_b_center = 0.3 + separation

    stream = []
    for i in range(n_steps):
        if i % 2 == 0:
            v = vec_a_center + random.gauss(0, noise_sigma)
        else:
            v = vec_b_center + random.gauss(0, noise_sigma)
        stream.append([v, 0.5])

    g = Geruon(vec_dim=2, memory_cap=cap, kappa_tau=3)
    for vec in stream:
        g.process_vec(list(vec), 'noise')

    frames = [f for f in g.memory.frames if f.weight > 0.01]
    distinct_vals = set()
    for f in frames:
        if len(f.vec) > 0:
            distinct_vals.add(round(f.vec[0], 2))  # round to 2dp for cluster detection
    n_distinct = len(distinct_vals)

    # Also check: are there 2 clusters in frame space?
    if len(frames) >= 2:
        vals = sorted([f.vec[0] for f in frames])
        gap = vals[-1] - vals[0]
    else:
        gap = 0

    return n_distinct, gap, len(frames)


# ── TEST A: Fixed separation, vary noise ──
SEPARATIONS = [0.05, 0.10, 0.20]
NOISE_LEVELS = [0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.15, 0.20]
N_REPS = 3

print('CALIB-δ: Merge under noise')
print('Two clusters with separation d, Gaussian noise σ.')
print('Critical σ where n_distinct drops to 1 → δ_eff ≈ σ_crit')
print()

for sep in SEPARATIONS:
    print(f'--- Separation d = {sep:.2f} ---')
    print(f'{"σ":>8}', end='')
    for cap in [8, 12, 16]:
        print(f'{("cap="+str(cap)):>12}', end='')
    print(f'{"σ/d":>8}')
    for sigma in NOISE_LEVELS:
        print(f'{sigma:8.3f}', end='')
        for cap in [8, 12, 16]:
            reps = [run_noise_test(sep, sigma, cap=cap) for _ in range(N_REPS)]
            nd = sum(r[0] for r in reps) / N_REPS
            print(f'{nd:12.1f}', end='')
        # Show σ/d ratio
        ratio = sigma / sep
        marker = ' <--' if 0.4 < ratio < 0.7 else ''
        print(f'{ratio:8.2f}{marker}')

# ── Find critical σ for each (sep, cap) ──
print()
print('=== Critical σ (n_distinct drops to 1.5) ===')
print(f'{"sep":<8} {"cap":<8} {"σ_crit":>8} {"σ_crit/d":>8}')
for sep in SEPARATIONS:
    for cap in [8, 12, 16]:
        sigma_crit = None
        for sigma in NOISE_LEVELS:
            reps = [run_noise_test(sep, sigma, cap=cap) for _ in range(N_REPS)]
            nd = sum(r[0] for r in reps) / N_REPS
            if nd <= 1.5:
                sigma_crit = sigma
                break
        if sigma_crit is None:
            sigma_crit = NOISE_LEVELS[-1]
        print(f'{sep:<8.2f} {cap:<8} {sigma_crit:8.3f} {sigma_crit/sep:8.2f}')


# ═══════════════════════════════════════════════════
# TEST B: Sine wave quantization (the "bit" concept for δ)
# ═══════════════════════════════════════════════════

print()
print('=' * 60)
print('TEST B: Sine quantization — coarse bits force merging')
print('=' * 60)

def quantize_sine(t, period, bits):
    raw = math.sin(2 * math.pi * t / period) * 0.45 + 0.5
    levels = 2 ** bits
    return round(raw * (levels - 1)) / (levels - 1)

BITS = [1, 2, 3, 4, 5, 6]
PERIOD = 20
N_STEPS = 500

print(f'{"bits":<8} {"levels":>8}', end='')
for cap in [8, 12, 16, 24]:
    print(f'{("cap="+str(cap)):>12}', end='')
print()
for bits in BITS:
    levels = 2 ** bits
    # Generate quantized sine stream
    stream = [[quantize_sine(i, PERIOD, bits)] for i in range(N_STEPS)]

    print(f'{bits:<8} {levels:>8}', end='')
    for cap in [8, 12, 16, 24]:
        reps = []
        for _ in range(N_REPS):
            g = Geruon(vec_dim=1, memory_cap=cap, kappa_tau=3)
            for vec in stream:
                g.process_vec(list(vec), 'sine')
            frames = [f for f in g.memory.frames if f.weight > 0.01]
            distinct = len(set(round(f.vec[0], 3) for f in frames if len(f.vec) > 0))
            reps.append(distinct)

        nd = sum(reps) / len(reps)
        bar = '▓' * int(nd) if nd < 20 else '▓' * min(20, int(nd))
        print(f'{nd:6.1f}/{levels:<4} {bar:<12}', end=' ')
    print()

# Key insight: n_distinct / levels = compression ratio
print()
print('=== Compression ratio (n_distinct / levels) ===')
print(f'{"bits":<8} {"levels":>8}', end='')
for cap in [8, 12, 16, 24]:
    print(f'{("cap="+str(cap)):>12}', end='')
print()
for bits in BITS:
    levels = 2 ** bits
    stream = [[quantize_sine(i, PERIOD, bits)] for i in range(N_STEPS)]
    print(f'{bits:<8} {levels:>8}', end='')
    for cap in [8, 12, 16, 24]:
        reps = []
        for _ in range(N_REPS):
            g = Geruon(vec_dim=1, memory_cap=cap, kappa_tau=3)
            for vec in stream:
                g.process_vec(list(vec), 'sine')
            frames = [f for f in g.memory.frames if f.weight > 0.01]
            distinct = len(set(round(f.vec[0], 3) for f in frames if len(f.vec) > 0))
            reps.append(distinct)
        nd = sum(reps) / len(reps)
        ratio = nd / levels * 100
        print(f'{ratio:11.1f}%', end=' ')
    print()
