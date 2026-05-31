"""κ_τ calibration: Direct τ response to stream structure.

Simplest possible calibration:
  1. Feed deterministic alternating pattern (A,B,A,B,...) at varying frequencies
  2. Measure: τ convergence speed, final τ, τ stability
  3. κ_τ controls how strongly τ couples to the stream's temporal structure

Also test:
  - Sudden transition: deterministic → random → deterministic
  - κ_τ controls τ's response speed to the transition
"""
import math, random, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from geruon import Geruon, GAMMA, TAU_0

# ── Test 1: Deterministic alternating pattern ──
def test_alternating(kappa, n_steps=500, d=2):
    """Feed A,B,A,B,... pattern. Measure τ convergence."""
    g = Geruon(vec_dim=d, memory_cap=12, kappa_tau=kappa)
    tau_hist = []

    for i in range(n_steps):
        # Alternating pattern: [1,0] → [0,1] → [1,0] → ...
        if i % 2 == 0:
            vec = [1.0, 0.0]
        else:
            vec = [0.0, 1.0]
        g.process_vec(vec, 'alt')
        tau_hist.append(g.tau)

    # Metrics
    final_tau = sum(tau_hist[-50:]) / 50  # last 50 steps
    # Convergence: steps until τ within 1% of final
    converged_at = n_steps
    for i in range(50, n_steps):
        recent_mean = sum(tau_hist[i-50:i]) / 50
        if abs(recent_mean - final_tau) / max(final_tau, 0.01) < 0.01:
            converged_at = i
            break

    tau_stability = (sum((t - final_tau)**2 for t in tau_hist[-100:]) / 100) ** 0.5

    return {
        'final_tau': final_tau,
        'converged_at': converged_at,
        'tau_stability': tau_stability,
        'tau_hist': tau_hist,
    }


# ── Test 2: Transition response (structured → random → structured) ──
def test_transition(kappa, n_structured=150, n_random=100, d=2):
    """Feed structured pattern, then random, then structured again.
    Measure τ response speed to the transition."""
    g = Geruon(vec_dim=d, memory_cap=12, kappa_tau=kappa)
    tau_hist = []

    phase = 0  # 0=structured, 1=random, 2=structured
    step_in_phase = 0

    for i in range(n_structured * 2 + n_random):
        if i < n_structured:
            phase = 0; step_in_phase = i
        elif i < n_structured + n_random:
            if phase == 0: transition_to_random = i
            phase = 1; step_in_phase = i - n_structured
        else:
            if phase == 1: transition_to_structured = i
            phase = 2; step_in_phase = i - n_structured - n_random

        if phase == 0 or phase == 2:
            vec = [1.0, 0.0] if step_in_phase % 2 == 0 else [0.0, 1.0]
        else:
            vec = [random.random(), random.random()]

        g.process_vec(vec, 'trans')
        tau_hist.append(g.tau)

    # τ response to random transition: how much does τ drop?
    pre_random_tau = sum(tau_hist[n_structured-30:n_structured]) / 30
    post_random_tau_min = min(tau_hist[n_structured:n_structured + n_random])
    tau_drop_random = pre_random_tau - post_random_tau_min

    # τ recovery: after returning to structured
    pre_recovery_tau = sum(tau_hist[n_structured+n_random-10:n_structured+n_random]) / 10
    post_recovery_tau = sum(tau_hist[-50:]) / 50
    tau_recovery = post_recovery_tau - pre_recovery_tau

    return {
        'tau_drop_random': tau_drop_random,
        'tau_recovery': tau_recovery,
        'pre_random_tau': pre_random_tau,
        'random_min_tau': post_random_tau_min,
        'final_tau': post_recovery_tau,
        'tau_hist': tau_hist,
    }


# ── Run ──
KAPPAS = [0.1, 0.5, 1.0, 3.0, 5.0, 10.0, 20.0]
N_REPS = 5

print('κ_τ Calibration: Direct τ response to stream structure')
print()

# Test 1
print('=== Test 1: Alternating pattern (500 steps) ===')
print(f'{"κ_τ":<8} {"τ_final":>8} {"converge@":>9} {"σ(τ)":>8}')
print('─' * 40)

for kappa in KAPPAS:
    results = [test_alternating(kappa) for _ in range(N_REPS)]
    taus = [r['final_tau'] for r in results]
    convs = [r['converged_at'] for r in results]
    stabs = [r['tau_stability'] for r in results]
    print(f'{kappa:<8.1f} {sum(taus)/len(taus):8.4f} {sum(convs)/len(convs):9.0f} '
          f'{sum(stabs)/len(stabs):8.4f}')

# Test 2
print()
print('=== Test 2: Structured → Random → Structured transition ===')
print(f'{"κ_τ":<8} {"τ_pre":>8} {"τ_random":>8} {"τ_drop":>8} {"τ_recover":>8} {"τ_final":>8}')
print('─' * 60)

for kappa in KAPPAS:
    results = [test_transition(kappa) for _ in range(N_REPS)]
    pre = sum(r['pre_random_tau'] for r in results) / N_REPS
    rmin = sum(r['random_min_tau'] for r in results) / N_REPS
    drop = sum(r['tau_drop_random'] for r in results) / N_REPS
    rec = sum(r['tau_recovery'] for r in results) / N_REPS
    fin = sum(r['final_tau'] for r in results) / N_REPS
    print(f'{kappa:<8.1f} {pre:8.4f} {rmin:8.4f} {drop:+8.4f} {rec:+8.4f} {fin:8.4f}')

# ── Find κ_τ sweet spot ──
print()
print('─' * 60)
print('SWEET SPOT ANALYSIS')
print()

# The ideal κ_τ should:
# 1. Converge reasonably fast on structured pattern (converge < 200 steps)
# 2. Drop τ noticeably when environment becomes random (τ_drop > 0.02)
# 3. Recover τ when structure returns (τ_recovery > 0.02)
# 4. Not be too jittery (σ(τ) < 0.01)

for kappa in KAPPAS:
    alt_results = [test_alternating(kappa) for _ in range(N_REPS)]
    trans_results = [test_transition(kappa) for _ in range(N_REPS)]

    conv = sum(r['converged_at'] for r in alt_results) / N_REPS
    stab = sum(r['tau_stability'] for r in alt_results) / N_REPS
    drop = sum(r['tau_drop_random'] for r in trans_results) / N_REPS
    rec = sum(r['tau_recovery'] for r in trans_results) / N_REPS

    scores = []
    scores.append(1.0 if conv < 200 else max(0, 1 - (conv-200)/300))  # converge fast
    scores.append(1.0 if stab < 0.01 else max(0, 1 - stab/0.05))     # stable
    scores.append(min(1.0, drop / 0.05))                              # drops on noise
    scores.append(min(1.0, rec / 0.05))                               # recovers

    total = sum(scores) / len(scores)
    bar = '▓' * int(total * 20)
    print(f'κ={kappa:<5.1f} converge={conv:5.0f} σ={stab:.4f} drop={drop:+.4f} rec={rec:+.4f} '
          f'score={total:.2f} {bar}')
