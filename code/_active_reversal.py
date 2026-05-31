"""Layer 2: Active reversal learning with calibrated κ_tau=3.

Geruon MAKES CHOICES based on its internal frame economy preference.
Fixed readout policy R1-R8 from Layer 1 (no readout adjustment).

Architecture:
  1. Geruon processes trial vectors through frame economy
  2. Internal preference for A vs B = weighted evidence from frames
  3. Choose A if preference > 0, else B (softmax with β from tau)
  4. Observe reward, feed back to Geruon
  5. After reversal: tau drops → system opens → preference switches

Key metric: switching latency at κ_tau=3.
Calibration predicts: ~109 steps for tau migration → should match
the behavioral switching latency.
"""
import math, random, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from geruon import Geruon, GAMMA, TAU_0

# ── FIXED READOUT POLICY (same as Layer 1) ──
def readout(g):
    frames = g.memory.frames
    tau = g.tau
    dtaudt = g.dtaudt
    arrow = list(g.arrow_output())
    centroid_mag = math.sqrt(sum(a**2 for a in arrow))
    weights = [f.weight for f in frames if f.weight > 0.001]
    if len(weights) >= 2:
        total_w = sum(weights)
        probs = [w/total_w for w in weights]
        entropy = -sum(p * math.log(max(p, 1e-10)) for p in probs)
        h_max = math.log(len(weights))
        F = 1.0 - entropy / h_max if h_max > 0 else 0.0
    else:
        F = 0.0
    l2 = sum(1 for f in frames if hasattr(f, 'layer') and f.layer == 2)
    l3 = sum(1 for f in frames if hasattr(f, 'layer') and f.layer == 3)
    if len(frames) >= 2:
        pred_err = math.sqrt(sum((frames[-1].vec[i]-frames[-2].vec[i])**2
                                 for i in range(min(len(frames[-1].vec), len(frames[-2].vec)))))
    else:
        pred_err = 0.0
    return {'tau': tau, 'dtaudt': dtaudt, 'centroid_mag': centroid_mag,
            'F': F, 'l2': l2, 'l3': l3, 'pred_err': pred_err,
            'n_frames': len(frames), 'total_w': sum(f.weight for f in frames)}


# ── Active reversal learning agent ──
class GeruonAgent:
    """Geruon as an active agent. Makes choices based on frame economy preference."""

    def __init__(self, kappa=3.0, cap=16, beta=2.0):
        self.g = Geruon(vec_dim=3, memory_cap=cap, kappa_tau=kappa)
        self.beta = beta  # choice determinism (higher = more exploit)
        # Running preference tracker (from frame evidence)
        self.a_evidence = 5.0
        self.b_evidence = 5.0
        self.history = []

    def choose(self):
        """Choose A or B based on internal preference."""
        total = self.a_evidence + self.b_evidence
        p_a = self.a_evidence / max(1, total)

        # Softmax: temperature from tau (higher tau = more deterministic)
        temperature = 1.0 / max(0.1, self.beta * (self.g.tau / TAU_0))
        p_a = 1.0 / (1.0 + math.exp(-(p_a - 0.5) / temperature))

        # Occasional exploration (tau-dependent: lower tau = more explore)
        explore_rate = max(0.05, 0.2 * (1.0 - self.g.tau / 0.85))
        if random.random() < explore_rate:
            choose_a = random.random() < 0.5
        else:
            choose_a = random.random() < p_a

        return choose_a

    def update(self, choose_a, reward):
        """Feed trial outcome to Geruon, update evidence, collect readout."""
        # Surprise: how unexpected was this?
        expected = self.a_evidence / max(1, self.a_evidence + self.b_evidence)
        if not choose_a:
            expected = 1.0 - expected
        surprise = abs(reward - expected)

        # Input vector: [chose_A, reward, surprise]
        vec = [1.0 if choose_a else 0.0, reward, surprise]
        self.g.process_vec(vec, 'trial')

        # Update running evidence (decay + new observation)
        decay = 0.95
        self.a_evidence *= decay
        self.b_evidence *= decay
        if choose_a:
            self.a_evidence += reward * 2.0 + 0.1  # small bonus for exploration
        else:
            self.b_evidence += reward * 2.0 + 0.1

        # Collect readout
        r = readout(self.g)
        r['choice'] = choose_a
        r['reward'] = reward
        r['preference'] = (self.a_evidence - self.b_evidence) / max(1, self.a_evidence + self.b_evidence)
        self.history.append(r)
        return r


# ── Run experiment ──
def run_reversal_task(n_trials=500, n_reversals=4, p_high=0.80, p_low=0.20):
    """Generate reversal schedule and run agent."""
    # Generate reversal schedule
    schedule = []
    A_is_best = True
    rev_interval = n_trials // (n_reversals + 1)
    reversals = []

    for i in range(n_trials):
        if i > 0 and i % rev_interval == 0 and len(reversals) < n_reversals:
            A_is_best = not A_is_best
            reversals.append(i)
        schedule.append(A_is_best)

    # Run agent
    agent = GeruonAgent(kappa=3.0, cap=16)
    choices = []
    rewards = []

    for i, A_is_best in enumerate(schedule):
        choose_a = agent.choose()

        # Determine reward
        if choose_a:
            p_r = p_high if A_is_best else p_low
        else:
            p_r = p_low if A_is_best else p_high
        reward = 1.0 if random.random() < p_r else 0.0

        agent.update(choose_a, reward)
        choices.append(choose_a)
        rewards.append(reward)

    return agent, choices, rewards, reversals, schedule


# ── Multiple runs ──
N_RUNS = 5
print('Layer 2: Active Reversal Learning (κ_tau=3, calibrated)')
print(f'{N_RUNS} runs, 500 trials, 4 reversals')
print()

all_switch_latencies = []
all_tau_drops = []

for run in range(N_RUNS):
    random.seed(42 + run * 100)
    agent, choices, rewards, reversals, schedule = run_reversal_task()

    # ── Analysis ──
    # 1. Switching latency: after reversal, how many trials until preference flips?
    switch_latencies = []
    for rev in reversals:
        # Preference after reversal
        prefs = [h['preference'] for h in agent.history[rev:rev+80]]
        pre_sign = 1 if agent.history[rev-1]['preference'] > 0 else -1
        target_sign = -pre_sign  # need to flip

        switched_at = 80
        for offset, p in enumerate(prefs):
            if (target_sign > 0 and p > 0.02) or (target_sign < 0 and p < -0.02):
                switched_at = offset
                break
        switch_latencies.append(switched_at)

    avg_switch = sum(switch_latencies) / len(switch_latencies)

    # 2. tau drop at reversal
    tau_drops = []
    for rev in reversals:
        pre_tau = sum(h['tau'] for h in agent.history[rev-30:rev]) / 30
        post_tau = [h['tau'] for h in agent.history[rev:rev+100]]
        tau_min = min(post_tau)
        tau_drops.append(pre_tau - tau_min)

    avg_tau_drop = sum(tau_drops) / len(tau_drops)

    # 3. Win-stay / Lose-shift
    stays = []; shifts = []
    for i in range(1, len(choices)):
        if rewards[i-1] > 0.5:
            stays.append(1.0 if choices[i] == choices[i-1] else 0.0)
        else:
            shifts.append(1.0 if choices[i] != choices[i-1] else 0.0)
    p_stay = sum(stays)/len(stays) if stays else 0
    p_shift = sum(shifts)/len(shifts) if shifts else 0

    print(f'Run {run}: switch_lat={avg_switch:.1f} trials, tau_drop={avg_tau_drop:+.4f}, '
          f'stay_win={p_stay:.3f}, shift_lose={p_shift:.3f}')

    all_switch_latencies.extend(switch_latencies)
    all_tau_drops.extend(tau_drops)

# ── Summary ──
print()
print('─' * 60)
avg_lat = sum(all_switch_latencies) / len(all_switch_latencies)
avg_drop = sum(all_tau_drops) / len(all_tau_drops)
print(f'Mean switching latency: {avg_lat:.1f} trials (calibration predicts ~109)')
print(f'Mean tau drop at reversal: {avg_drop:+.4f}')
print(f'Human benchmark: 8-15 trials switching latency')

# ── Detailed run 0: tau and preference around reversal ──
agent0, _, _, reversals0, _ = run_reversal_task()
print(f'\ntau and preference around first reversal (trial {reversals0[0]}):')
rev = reversals0[0]
for offset in range(-10, 31):
    h = agent0.history[rev + offset]
    pref_bar = 'A' if h['preference'] > 0 else 'B'
    msg = "  %+4d: tau=%.4f  pref=%+.3f %s  PE=%.4f" % (offset, h["tau"], h["preference"], pref_bar, h["pred_err"])
    print(msg)
