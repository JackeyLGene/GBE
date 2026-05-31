"""EE Passive Instrument Calibration — Layer 1 (v2).

Key fix: use CONTINUOUS-VALUED streams where structural changes
actually change the statistical properties Geruon measures.

FIXED READOUT POLICY (R1-R8, frozen — same as v1).
"""
import math, random, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from geruon import Geruon, GAMMA, TAU_0
from collections import deque

# ═══════════════════════════════════════════════════════════
# FIXED READOUT POLICY (same as v1, unchanged)
# ═══════════════════════════════════════════════════════════

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

    l2 = sum(1 for f in frames if hasattr(f, 'layer') and f.layer == 'L2')
    l3 = sum(1 for f in frames if hasattr(f, 'layer') and f.layer == 'L3')

    if len(frames) >= 2:
        latest = frames[-1].vec
        prev = frames[-2].vec
        frame_disp = math.sqrt(sum((latest[i]-prev[i])**2 for i in range(min(len(latest),len(prev)))))
    else:
        frame_disp = 0.0

    n_frames = len(frames)
    total_w = sum(f.weight for f in frames)

    return {'tau': tau, 'dtaudt': dtaudt, 'centroid_mag': centroid_mag,
            'F': F, 'l2': l2, 'l3': l3, 'frame_disp': frame_disp,
            'n_frames': n_frames, 'total_w': total_w}


def run_with_readout(vec_stream, kappa=3.0, cap=16, d=None):
    if d is None: d = len(vec_stream[0])
    g = Geruon(vec_dim=d, memory_cap=cap, kappa_tau=kappa)
    history = []
    for vec in vec_stream:
        g.process_vec(list(vec), 'calib')
        history.append(readout(g))
    return history, g


# ═══════════════════════════════════════════════════════════
# CALIB-κ: Environmental reversal → migration latency
# ═══════════════════════════════════════════════════════════

def calib_kappa(kappa_values=None, n_steps=600, d=3, n_reps=3):
    """Two SINE WAVES with different frequencies.
    Phase 1 (steps 0-300): sin(2π·t/20) on dim 0, dim 1-2 are noise
    Phase 2 (steps 300-600): sin(2π·t/8) on dim 0 (FREQUENCY DOUBLES)

    The reversal is a structural change Geruon should detect:
    the pattern speeds up → prediction errors increase → τ drops → re-stabilizes.
    """
    if kappa_values is None:
        kappa_values = [0.5, 1.0, 3.0, 5.0, 10.0, 20.0]

    results = {}
    for kappa in kappa_values:
        kappa_results = []
        for rep in range(n_reps):
            random.seed(42 + rep * 100)
            stream = []
            for i in range(n_steps):
                if i < n_steps // 2:
                    freq = 2 * math.pi / 20  # slow
                else:
                    freq = 2 * math.pi / 8   # fast
                v0 = math.sin(freq * i) * 0.4 + 0.5
                v1 = random.gauss(0.5, 0.05)
                v2 = random.gauss(0.5, 0.05)
                stream.append([v0, v1, v2])

            history, g = run_with_readout(stream, kappa=kappa, d=d, cap=24)

            rev = n_steps // 2

            # Pre-reversal baseline
            pre_tau = sum(h['tau'] for h in history[rev-80:rev]) / 80
            pre_pe = sum(h['frame_disp'] for h in history[rev-80:rev]) / 80

            # Post-reversal τ trajectory
            post_tau = [h['tau'] for h in history[rev:]]
            post_pe = [h['frame_disp'] for h in history[rev:]]

            tau_min = min(post_tau)
            tau_min_at = post_tau.index(tau_min)

            pe_max = max(post_pe[:50])  # peak frame displacement in first 50 steps
            pe_max_at = post_pe[:50].index(pe_max)

            # Stabilization: steps until τ returns to within 1% of pre_tau
            stable_at = n_steps - rev
            for i in range(20, len(post_tau)):
                w = post_tau[max(0,i-20):i+1]
                wa = sum(w)/len(w)
                if abs(wa - pre_tau) / max(pre_tau, 0.01) < 0.015:
                    stable_at = i
                    break

            kappa_results.append({
                'pre_tau': pre_tau, 'tau_min': tau_min, 'tau_min_at': tau_min_at,
                'stable_at': stable_at, 'pre_pe': pre_pe, 'pe_max': pe_max,
                'pe_max_at': pe_max_at,
            })

        results[kappa] = kappa_results
    return results


# ═══════════════════════════════════════════════════════════
# CALIB-cap: Lag-N temporal dependency
# ═══════════════════════════════════════════════════════════

def calib_cap(cap_values=None, n_steps=500, d=3, n_reps=3):
    """Stream where vec[t] = f(vec[t-N]): a rotation + noise.
    For a given lag N, vec[t] = rotate(vec[t-N]) + small_noise.
    Geruon with sufficient cap should form associations at lag N,
    reducing frame displacement for that N.

    Measure frame displacement for lags 1,2,3,4,6,8,10. The max lag where
    frame displacement is detectably lower than baseline = effective capacity.
    """
    if cap_values is None:
        cap_values = [6, 10, 16, 24, 36]

    results = {}
    for cap in cap_values:
        cap_results = []
        for rep in range(n_reps):
            random.seed(42 + rep * 100)
            lags = [1, 2, 3, 4, 6, 8, 10]
            lag_scores = {}

            for lag in lags:
                buf = deque(maxlen=lag)
                stream = []
                for i in range(n_steps):
                    if i >= lag:
                        # vec[t] = rotate vector from lag steps ago
                        old = list(buf[0])
                        vec = [old[-1]] + old[:-1]  # shift right
                        vec = [v + random.gauss(0, 0.03) for v in vec]
                    else:
                        vec = [random.random() for _ in range(d)]
                    stream.append(vec)
                    buf.append(list(vec))

                history, g = run_with_readout(stream, kappa=3.0, cap=cap, d=d)
                pe_steady = sum(h['frame_disp'] for h in history[-200:]) / 200
                lag_scores[lag] = pe_steady

            cap_results.append(lag_scores)
        results[cap] = cap_results
    return results


# ═══════════════════════════════════════════════════════════
# CALIB-δ: Category boundary → frame purity
# ═══════════════════════════════════════════════════════════

def calib_delta(n_steps=600, d=2, n_reps=3):
    """Two Gaussian clusters in 2D space.
    Cluster A: center [0.3, 0.5], Cluster B: center [0.3+sep, 0.5]
    Vary separation ε from 0.05 to 0.60.
    Alternate between clusters every ~20 trials.

    Measure: centroid_separation between A-frames and B-frames in Geruon's memory.
    Higher F = better category separation.
    """
    separations = [0.05, 0.10, 0.15, 0.20, 0.30, 0.45, 0.60]

    results = {}
    for sep in separations:
        sep_results = []
        for rep in range(n_reps):
            random.seed(42 + rep * 100)
            stream = []
            cluster_labels = []
            in_a = True
            block_len = 18 + random.randint(0, 5)

            for i in range(n_steps):
                if i % block_len == 0:
                    in_a = not in_a
                    block_len = 18 + random.randint(0, 5)

                cx = 0.3 if in_a else 0.3 + sep
                cy = 0.5
                vec = [cx + random.gauss(0, 0.04), cy + random.gauss(0, 0.04)]
                stream.append(vec)
                cluster_labels.append(0 if in_a else 1)

            history, g = run_with_readout(stream, kappa=3.0, cap=24, d=d)

            # Frame purity analysis
            frames = g.memory.frames
            fvecs = [(list(f.vec)[:2], f.weight) for f in frames if f.weight > 0.01]

            if len(fvecs) >= 4:
                # Separate frames by dim0 median
                dim0_vals = [v[0] for v, w in fvecs]
                median_d0 = sorted(dim0_vals)[len(dim0_vals)//2]
                c0 = [(v, w) for v, w in fvecs if v[0] < median_d0]
                c1 = [(v, w) for v, w in fvecs if v[0] >= median_d0]

                if c0 and c1:
                    w0 = [x[1] for x in c0]; w1 = [x[1] for x in c1]
                    c0c = [sum(x[0][i]*x[1] for x in c0)/sum(w0) for i in range(d)]
                    c1c = [sum(x[0][i]*x[1] for x in c1)/sum(w1) for i in range(d)]
                    centroid_sep = math.sqrt(sum((c0c[i]-c1c[i])**2 for i in range(d)))
                else:
                    centroid_sep = 0.0
            else:
                centroid_sep = 0.0

            final_F = history[-1]['F'] if history else 0
            sep_results.append({'centroid_sep': centroid_sep, 'final_F': final_F,
                              'n_frames': len(fvecs)})

        results[sep] = sep_results
    return results


# ═══════════════════════════════════════════════════════════
# CALIB-γ: Unreinforced structure half-life
# ═══════════════════════════════════════════════════════════

def calib_gamma(n_structured=400, n_extinction=800, d=3, n_reps=3):
    """Phase 1: reinforce structured pattern (sine wave).
    Phase 2: feed PURE NOISE (no reinforcement of original structure).

    Track weight of ORIGINAL structure frames (by frame identity),
    NOT total_w across all frames. Total_w increases during extinction
    because new random frames accumulate — this is turnover, not decay.

    Half-life = steps until original structure frame weight drops to 50%.
    """
    results = []
    for rep in range(n_reps):
        random.seed(42 + rep * 100)

        # Phase 1: structured
        stream_structured = []
        for i in range(n_structured):
            v0 = math.sin(2 * math.pi * i / 15) * 0.4 + 0.5
            v1 = math.sin(2 * math.pi * i / 23) * 0.3 + 0.5
            v2 = 0.3 if i % 2 == 0 else 0.7
            stream_structured.append([v0, v1, v2])

        g = Geruon(vec_dim=d, memory_cap=24, kappa_tau=3.0)
        for vec in stream_structured:
            g.process_vec(list(vec), 'struct')

        # Mark original structure frames by their struct_sig key
        original_keys = set()
        for f in g.memory.frames:
            if hasattr(f, 'struct_sig') and f.struct_sig is not None:
                original_keys.add(f.struct_sig.struct_key)
            else:
                # Fallback: use id(f) for frames without struct_sig
                original_keys.add(id(f))

        original_w_start = sum(f.weight for f in g.memory.frames
                               if _frame_in_set(f, original_keys))

        # Phase 2: extinction — track only original frame weight
        orig_weights = []
        total_ws = []

        for i in range(n_extinction):
            g.process_vec([random.random() for _ in range(d)], 'noise')

            orig_w = sum(f.weight for f in g.memory.frames
                        if _frame_in_set(f, original_keys))
            orig_weights.append(orig_w)
            total_ws.append(sum(f.weight for f in g.memory.frames))

        # Half-life of original structure weight
        w_target = original_w_start * 0.5
        half_life = n_extinction
        for i, w in enumerate(orig_weights):
            if w <= w_target and i > 5:
                half_life = i
                break

        # Turnover ratio: how much new weight accumulated vs original decayed
        w_orig_end = orig_weights[-1]
        w_total_end = total_ws[-1]
        turnover_ratio = (w_total_end - w_orig_end) / max(1, original_w_start)

        results.append({
            'w_orig_start': original_w_start,
            'w_orig_end': w_orig_end,
            'w_total_end': w_total_end,
            'half_life': half_life,
            'turnover_ratio': turnover_ratio,
            'orig_weight_curve': orig_weights[::20],
            'total_weight_curve': total_ws[::20],
        })

    return results


def _frame_in_set(f, key_set):
    """Check if frame belongs to original structure set."""
    if hasattr(f, 'struct_sig') and f.struct_sig is not None:
        return f.struct_sig.struct_key in key_set
    return id(f) in key_set


# ═══════════════════════════════════════════════════════════
# CALIB-GI: Uncertainty tracking (solo Geruon version)
# ═══════════════════════════════════════════════════════════

def calib_uncertainty_tracking(n_steps=600, d=3, n_reps=3):
    """Feed alternating low-noise / high-noise phases.
    Measure: how does τ track noise level?
    This calibrates Geruon's NATURAL uncertainty response (not GI — that's for We/Self).

    Low noise: σ=0.02 around a fixed center
    High noise: σ=0.25 around a different center
    """
    results = []
    for rep in range(n_reps):
        random.seed(42 + rep * 100)
        stream = []
        noise_levels = []

        for i in range(n_steps):
            phase = (i // 80) % 2
            sigma = 0.02 if phase == 0 else 0.25
            center = [0.3, 0.5, 0.7] if phase == 0 else [0.7, 0.3, 0.5]
            vec = [max(0, min(1, c + random.gauss(0, sigma))) for c in center]
            stream.append(vec)
            noise_levels.append(sigma)

        history, g = run_with_readout(stream, kappa=3.0, cap=24, d=d)

        low_tau = []; high_tau = []
        low_pe = []; high_pe = []
        for i, h in enumerate(history):
            if noise_levels[i] < 0.1:
                low_tau.append(h['tau']); low_pe.append(h['frame_disp'])
            else:
                high_tau.append(h['tau']); high_pe.append(h['frame_disp'])

        results.append({
            'tau_low': sum(low_tau)/len(low_tau),
            'tau_high': sum(high_tau)/len(high_tau),
            'tau_diff': sum(high_tau)/len(high_tau) - sum(low_tau)/len(low_tau),
            'pe_low': sum(low_pe)/len(low_pe),
            'pe_high': sum(high_pe)/len(high_pe),
            'pe_ratio': (sum(high_pe)/len(high_pe)) / (sum(low_pe)/len(low_pe)),
        })
    return results


# ═══════════════════════════════════════════════════════════
# CALIB-τ₀: Default absorption rate for novel patterns
# ═══════════════════════════════════════════════════════════

def calib_tau0(n_steps=600, d=3, n_reps=3):
    """Phase 1 (300 steps): sine wave on dim0, periodic on dim2
    Phase 2 (300 steps): CHAOTIC pattern (logistic map values)

    The novel pattern is genuinely different in statistical structure.
    Measure: how quickly does τ drop → system opens to absorb new structure?
    """
    results = []
    for rep in range(n_reps):
        stream = []
        # Phase 1: structured periodic
        for i in range(300):
            v0 = math.sin(2 * math.pi * i / 16) * 0.4 + 0.5
            v1 = 0.3 if i % 3 == 0 else (0.5 if i % 3 == 1 else 0.7)
            v2 = (i % 10) / 10.0
            stream.append([v0, v1, v2])

        # Phase 2: chaotic (logistic map — deterministic but unpredictable)
        x = 0.6
        for i in range(300):
            x = 3.9 * x * (1 - x)  # logistic map (chaotic)
            y = 3.9 * (x + 0.1) * (1 - x - 0.1)
            z = 3.9 * (y + 0.2) * (1 - y - 0.2)
            stream.append([max(0, min(1, x)), max(0, min(1, abs(y))), max(0, min(1, abs(z)))])

        history, g = run_with_readout(stream, kappa=3.0, cap=24, d=d)

        # τ trajectory after novel pattern
        tau_novel = [h['tau'] for h in history[300:]]
        tau_pre = sum(h['tau'] for h in history[220:300]) / 80

        tau_min = min(tau_novel)
        tau_drop = tau_pre - tau_min
        tau_min_at = tau_novel.index(tau_min)

        # Initial absorption slope (first 40 steps after transition)
        slope = (tau_novel[0] - min(tau_novel[:40])) / max(1, tau_novel[:40].index(min(tau_novel[:40])))

        # Re-stabilization: when does τ plateau?
        stable_at = 300
        for i in range(40, len(tau_novel)):
            recent = tau_novel[i-20:i+1]
            rng = max(recent) - min(recent)
            if rng < 0.003:
                stable_at = i
                break

        results.append({
            'tau_pre': tau_pre, 'tau_min': tau_min, 'tau_drop': tau_drop,
            'tau_min_at': tau_min_at, 'initial_slope': slope, 'stable_at': stable_at,
        })

    return results


# ═══════════════════════════════════════════════════════════
# RUN ALL
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    print('=' * 65)
    print('EE PASSIVE INSTRUMENT CALIBRATION v2')
    print('Continuous-valued streams, fixed readout policy R1-R8')
    print('=' * 65)

    # ── CALIB-κ ──
    print('\n' + '─' * 55)
    print('CALIB-κ: Frequency Doubling → Migration Latency')
    print('─' * 55)
    kr = calib_kappa()
    print(f'{"κ_τ":<8} {"τ_pre":>8} {"τ_min":>8} {"min@":>6} {"stable@":>8} {"pe_max":>8} {"pe@":>6}')
    for k in sorted(kr.keys()):
        rs = kr[k]; n = len(rs)
        print(f'{k:<8.1f} {sum(r["pre_tau"] for r in rs)/n:8.4f} '
              f'{sum(r["tau_min"] for r in rs)/n:8.4f} '
              f'{sum(r["tau_min_at"] for r in rs)/n:6.0f} '
              f'{sum(r["stable_at"] for r in rs)/n:8.0f} '
              f'{sum(r["pe_max"] for r in rs)/n:8.4f} '
              f'{sum(r["pe_max_at"] for r in rs)/n:6.0f}')

    # ── CALIB-cap ──
    print('\n' + '─' * 55)
    print('CALIB-cap: Lag-N Rotation Dependency')
    print('─' * 55)
    cr = calib_cap()
    lags = [1,2,3,4,6,8,10]
    print(f'{"cap":<8}', end='')
    for lag in lags:
        print(f'{("lag="+str(lag)):>10}', end='')
    print()
    for cap in sorted(cr.keys()):
        rs = cr[cap]; n = len(rs)
        print(f'{cap:<8}', end='')
        for lag in lags:
            pe = sum(r[lag] for r in rs) / n
            print(f'{pe:10.4f}', end='')
        print()

    # ── CALIB-δ ──
    print('\n' + '─' * 55)
    print('CALIB-δ: Category Boundary → Frame Purity')
    print('─' * 55)
    dr = calib_delta()
    print(f'{"sep":<8} {"centroid_sep":>12} {"F_final":>8} {"n_frames":>8}')
    for sep in sorted(dr.keys()):
        rs = dr[sep]; n = len(rs)
        print(f'{sep:<8.2f} {sum(r["centroid_sep"] for r in rs)/n:12.4f} '
              f'{sum(r["final_F"] for r in rs)/n:8.4f} '
              f'{sum(r["n_frames"] for r in rs)/n:8.1f}')

    # ── CALIB-γ ──
    print('\n' + '─' * 55)
    print('CALIB-γ: Unreinforced Structure Half-Life')
    print('─' * 55)
    gr = calib_gamma()
    for i, r in enumerate(gr):
        print(f'Rep {i}: w_orig_start={r["w_orig_start"]:.1f}, '
              f'w_orig_end={r["w_orig_end"]:.1f}, w_total_end={r["w_total_end"]:.1f}, '
              f'half_life={r["half_life"]} steps, turnover={r["turnover_ratio"]:.2f}x')
    hl = sum(r['half_life'] for r in gr) / len(gr)
    tr = sum(r['turnover_ratio'] for r in gr) / len(gr)
    print(f'Mean original-structure half-life: {hl:.0f} steps')
    print(f'Mean turnover ratio (new/old weight): {tr:.2f}x')

    # ── Uncertainty tracking (replaces CALIB-GI for solo) ──
    print('\n' + '─' * 55)
    print('Uncertainty Tracking (solo Geruon — τ vs noise level)')
    print('─' * 55)
    ur = calib_uncertainty_tracking()
    for i, r in enumerate(ur):
        print(f'Rep {i}: τ_low={r["tau_low"]:.4f} τ_high={r["tau_high"]:.4f} '
              f'τ_diff={r["tau_diff"]:+.4f} pe_ratio={r["pe_ratio"]:.2f}x')
    print(f'Mean τ_diff: {sum(r["tau_diff"] for r in ur)/len(ur):+.4f} '
          f'(τ rises {sum(r["tau_diff"] for r in ur)/len(ur):+.4f} in high noise)')

    # ── CALIB-τ₀ ──
    print('\n' + '─' * 55)
    print('CALIB-τ₀: Novel Pattern Absorption (periodic → chaotic)')
    print('─' * 55)
    tr = calib_tau0()
    for i, r in enumerate(tr):
        print(f'Rep {i}: τ_pre={r["tau_pre"]:.4f} τ_min={r["tau_min"]:.4f} '
              f'drop={r["tau_drop"]:+.4f} slope={r["initial_slope"]:+.6f} '
              f'min@={r["tau_min_at"]} stable@={r["stable_at"]}')
    print(f'Mean τ_drop: {sum(r["tau_drop"] for r in tr)/len(tr):+.4f}')
    print(f'Mean absorption slope: {sum(r["initial_slope"] for r in tr)/len(tr):+.6f}')
