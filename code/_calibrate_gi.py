"""CALIB-GI: Self-observation interval × cavity count scan.

GI optimal depends on number of cavities:
  - n=2: 1 exchange pair, cycle = GI steps
  - n=3: 3 exchange pairs, cycle = 2×GI steps (each cav talks to 2 others)
  - n=5: 10 exchange pairs, cycle = 4×GI steps

Hypothesis: optimal GI scales inversely with cavity count.
  GI_opt × (n_cavities - 1) ≈ constant (full communication cycle)

Scan: GI × n_cavities, measure cavity_diff and tau stability.
"""
import math, random, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from geruon import Geruon, GAMMA, TAU_0

class MiniSelf:
    def __init__(self, n_cavities, cap, vec_dim, gi):
        # Standard Self kappas for n=3, geometrically spaced for other n
        if n_cavities == 1:
            kappas = [3.0]
        elif n_cavities == 2:
            kappas = [0.5, 10.0]
        elif n_cavities == 3:
            kappas = [0.5, 10.0, 100.0]  # standard Self lens set
        elif n_cavities == 5:
            kappas = [0.3, 1.0, 3.0, 10.0, 50.0]
        elif n_cavities == 8:
            kappas = [0.2, 0.5, 1.5, 3.0, 8.0, 16.0, 40.0, 100.0]
        else:
            kappas = [3.0] * n_cavities

        self.cavities = [Geruon(vec_dim=vec_dim, memory_cap=cap, kappa_tau=k)
                        for k in kappas]
        self.gi = gi
        self.step = 0
        self.n = n_cavities

    def process(self, vec):
        for g in self.cavities:
            g.process_vec(list(vec), 'self')

        if self.step % self.gi == 0 and self.step > 0:
            arrows = [list(g.arrow_output()) for g in self.cavities]
            for ci, g in enumerate(self.cavities):
                for cj, arrow in enumerate(arrows):
                    if ci != cj:
                        g.process_vec(arrow, f'cav{cj}')

        self.step += 1

    def readout(self):
        taus = [g.tau for g in self.cavities]
        return {
            'tau_mean': sum(taus)/len(taus),
            'tau_range': max(taus) - min(taus),
            'tau_std': (sum((t - sum(taus)/len(taus))**2 for t in taus) / len(taus)) ** 0.5,
        }


def run_gi_n_test(gi, n_cavities, n_steps=500, seed=42):
    """Run MiniSelf(n_cavities) at given GI on sine→chaotic transition."""
    random.seed(seed)

    stream = []
    phase_labels = []
    x = 0.6

    for i in range(n_steps):
        if i < n_steps // 2:
            v0 = math.sin(2 * math.pi * i / 16) * 0.4 + 0.5
            phase_labels.append(0)
        else:
            x = 3.9 * x * (1 - x)
            v0 = x
            phase_labels.append(1)

        v1 = random.gauss(0.5, 0.05)
        v2 = 0.3 if i % 3 == 0 else 0.7
        stream.append([v0, v1, v2])

    cap = 16
    self_ = MiniSelf(n_cavities, cap, vec_dim=3, gi=gi)

    history = []
    for vec in stream:
        self_.process(vec)
        history.append(self_.readout())

    # Cavity differentiation in steady state (last 100 steps per phase)
    p0 = [h for i, h in enumerate(history) if phase_labels[i] == 0][-100:]
    p1 = [h for i, h in enumerate(history) if phase_labels[i] == 1][-100:]

    range0 = sum(h['tau_range'] for h in p0) / 100
    range1 = sum(h['tau_range'] for h in p1) / 100
    std0 = sum(h['tau_std'] for h in p0) / 100
    std1 = sum(h['tau_std'] for h in p1) / 100
    tau0 = sum(h['tau_mean'] for h in p0) / 100
    tau1 = sum(h['tau_mean'] for h in p1) / 100

    cavity_diff = (range0 + range1) / 2
    tau_sep = tau0 - tau1  # phase discrimination

    return {
        'cavity_diff': cavity_diff,
        'tau_sep': tau_sep,
        'tau0': tau0, 'tau1': tau1,
        'std0': std0, 'std1': std1,
    }


# ── 2D Scan: GI × n_cavities ──
GI_VALUES = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16]
N_CAVITIES = [1, 2, 3, 5, 8]
N_REPS = 5

print('CALIB-GI: GI × n_cavities scan')
print(f'GI: {GI_VALUES}')
print(f'Cavities: {N_CAVITIES}')
print()

# Collect all results
all_results = {}
for n in N_CAVITIES:
    for gi in GI_VALUES:
        reps = [run_gi_n_test(gi, n, seed=42 + rep*100 + gi*7 + n*13) for rep in range(N_REPS)]
        all_results[(gi, n)] = reps

# ── Cavity differentiation heatmap ──
print('=== Cavity differentiation (tau_range across cavities) ===')
print(f'{"GI\\n":<8}', end='')
for n in N_CAVITIES:
    print(f'{("n="+str(n)):>12}', end='')
print()
for gi in GI_VALUES:
    print(f'{gi:<8}', end='')
    for n in N_CAVITIES:
        reps = all_results[(gi, n)]
        cd = sum(r['cavity_diff'] for r in reps) / N_REPS
        bar = '|' * int(cd * 50)
        print(f'{cd:8.4f} {bar:<4}', end=' ')
    print()

# ── Tau phase separation heatmap ──
print()
print('=== Tau phase separation (tau_sine - tau_chaotic) ===')
print(f'{"GI\\n":<8}', end='')
for n in N_CAVITIES:
    print(f'{("n="+str(n)):>12}', end='')
print()
for gi in GI_VALUES:
    print(f'{gi:<8}', end='')
    for n in N_CAVITIES:
        reps = all_results[(gi, n)]
        ts = sum(r['tau_sep'] for r in reps) / N_REPS
        print(f'{ts:+10.4f}', end=' ')
    print()

# ── Find optimal GI for each cavity count ──
print()
print('=== Optimal GI per cavity count ===')
print(f'{"n_cav":<8} {"GI_opt":>8} {"cav_diff":>10} {"tau_sep":>10} {"cycle(GI×(n-1))":>18}')
for n in N_CAVITIES:
    if n == 1:
        # No exchange possible with 1 cavity
        reps = all_results[(1, n)]
        cd = sum(r['cavity_diff'] for r in reps) / N_REPS
        print(f'{n:<8} {"N/A":>8} {cd:>10.4f} {"N/A":>10} {"N/A":>18}')
        continue

    best_gi = max(GI_VALUES, key=lambda g:
        sum(r['cavity_diff'] for r in all_results[(g, n)]) / N_REPS)
    best_reps = all_results[(best_gi, n)]
    best_cd = sum(r['cavity_diff'] for r in best_reps) / N_REPS
    best_ts = sum(r['tau_sep'] for r in best_reps) / N_REPS
    cycle = best_gi * (n - 1)
    print(f'{n:<8} {best_gi:>8} {best_cd:>10.4f} {best_ts:+10.4f} {cycle:>18}')

# ── GI_opt × (n-1) ≈ constant? ──
print()
print('GI_opt × (n_cavities - 1) — should be ~constant if hypothesis holds:')
for n in [2, 3, 5, 8]:
    best_gi = max(GI_VALUES, key=lambda g:
        sum(r['cavity_diff'] for r in all_results[(g, n)]) / N_REPS)
    print(f'  n={n}: GI_opt={best_gi}, GI×(n-1)={best_gi * (n-1)}')
