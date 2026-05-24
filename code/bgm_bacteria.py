"""
BGM Experiment 2: Bacteria Grid — 64 GEME units, cold start, no G0.
Spatial heterogeneity via nutrient gradient + local neighbor communication.

Phase A: Cultivation (30 rounds, source fixed at center)
Phase B: Perturbation (10 rounds, source moves to corner)
Phase C: Recovery (10 rounds at new position)

Pure thought experiment. Barraud is an "incidental" isomorphism, not a target.
"""
import sys, os, time, math, statistics, random
sys.path.insert(0, os.path.dirname(__file__))
from geme import GEME, _VEC_DIM

VEC_DIM = _VEC_DIM
TAU_0 = 0.60

# ── Grid topology ──
GRID_SIZE = 8
N_UNITS = GRID_SIZE * GRID_SIZE

def von_neumann_neighbors(r, c):
    """Return neighbor coordinates for (r, c) in 4×4 grid."""
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
            neighbors.append((nr, nc))
    return neighbors

# ── Nutrient gradient ──
def nutrient_concentration(r, c, source_r, source_c, sigma=2.0, cmax=1.0):
    """Gaussian gradient centered at (source_r, source_c)."""
    d2 = (r - source_r) ** 2 + (c - source_c) ** 2
    return cmax * math.exp(-d2 / (2 * sigma * sigma))

def encode_concentration(conc, bins=VEC_DIM):
    """Encode scalar concentration to VEC_DIM-bin vector (Hz-binning style)."""
    v = [0.0] * bins
    idx = int(conc * (bins - 1))
    idx = max(0, min(bins - 1, idx))
    v[idx] = 1.0
    return v

def gradient_noise(vec, noise_scale=0.05):
    """Add small Gaussian noise to vector, preserving bin structure."""
    result = list(vec)
    for i in range(len(result)):
        result[i] += random.gauss(0, noise_scale)
        result[i] = max(0.0, result[i])
    s = math.sqrt(sum(x*x for x in result))
    return [x/max(s, 0.001) for x in result]

def l6_to_vec(l6_val, dim=VEC_DIM):
    """Encode L6 scalar [0, 1] to dim-bin vector."""
    v = [0.0] * dim
    idx = int(l6_val * (dim - 1))
    v[max(0, min(dim - 1, idx))] = 1.0
    return v

def blend_vectors(env_vec, neighbor_vecs, alpha=0.7):
    """Blend environmental vector with mean of neighbor L6 vectors."""
    if not neighbor_vecs:
        return list(env_vec)
    n = len(neighbor_vecs)
    neighbor_mean = [sum(neighbor_vecs[j][i] for j in range(n)) / n
                     for i in range(len(env_vec))]
    return [(1.0 - alpha) * neighbor_mean[i] + alpha * env_vec[i]
            for i in range(len(env_vec))]

# ── Metrics snapshot ──
def unit_snapshot(unit):
    """Extract key metrics from one GEME unit."""
    m = unit.metrics()
    return {
        'l4_density': round(m.get('L4_frame_count', 0) / max(m.get('frame_count', 1), 1), 4),
        'mi': round(m.get('I(phi;X)', 0), 5),
        'l6': round(unit.anomaly_score(), 3),
        'tau': round(unit._induction_threshold, 4),
        'frames': m.get('frame_count', 0),
        'doubt': m.get('doubt_mode', False),
        'pred_acc': round(m.get('pred_accuracy', 0), 3),
        'pred_total': m.get('pred_total', 0),
        'conf_thresh': round(unit.memory._conf_threshold, 4),
        'merge_dists': len(unit.memory._merge_dists),
    }


# ── Bacteria Grid ──
class BacteriaGrid:
    def __init__(self, alpha=0.7, cold_start=True, seed_base=42):
        self.alpha = alpha
        self.seed_base = seed_base
        self.units = {}       # (r, c) → GEME
        self.neighbors = {}   # (r, c) → [(nr, nc), ...]
        self.t = 0

        # Build neighbor topology
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.neighbors[(r, c)] = von_neumann_neighbors(r, c)

        # Create units
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                g = GEME(memory_cap=16)
                g.memory.preserve_sig = True
                g.memory.quantum_mode = True
                g.memory.cooccur_thresh = 0.08

                if cold_start:
                    # No preloaded merge knowledge — system discovers from data
                    g.memory._merge_dists = []
                    g.memory._learn_dists = []
                    g._induction_threshold = TAU_0
                else:
                    # Warm start — preloaded calibration (like Bach GEMENet)
                    g.memory._merge_dists = [0.3] * 30
                    g._induction_threshold = 3.0

                g.memory._qrand = random.Random(seed_base + r * GRID_SIZE + c)
                self.units[(r, c)] = g

    def step(self, source_r, source_c, noise_scale=0.05):
        """One time step: each unit reads local concentration + noise + neighbor L6."""
        self.t += 1
        step_data = {}

        # Phase 1: compute inputs for all units
        inputs = {}
        signatures = {}
        l6_outputs = {}
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                unit = self.units[(r, c)]
                conc = nutrient_concentration(r, c, source_r, source_c)
                env_vec = encode_concentration(conc)
                # Add temporal noise — creates per-step variation for co-occurrence learning
                noisy_vec = gradient_noise(env_vec, noise_scale)
                # Gather neighbor L6 outputs
                neighbor_l6s = []
                for nr, nc in self.neighbors[(r, c)]:
                    if (nr, nc) in l6_outputs:
                        neighbor_l6s.append(l6_to_vec(l6_outputs[(nr, nc)]))
                if not neighbor_l6s:
                    neighbor_l6s = [[0.0] * VEC_DIM]
                blended = blend_vectors(noisy_vec, neighbor_l6s, alpha=self.alpha)
                inputs[(r, c)] = blended
                # Signature = observer's spatial identity
                # Role: corner(2nbr)/edge(3nbr)/interior(4nbr) + concentration level
                n_nbrs = len(self.neighbors[(r, c)])
                if n_nbrs == 2: role = 'C'
                elif n_nbrs == 3: role = 'E'
                else: role = 'I'
                conc_bin = int(conc * 10)
                signatures[(r, c)] = f'{role}{n_nbrs}_g{conc_bin}'

        # Phase 2: process inputs and record outputs
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                unit = self.units[(r, c)]
                unit.process_vec(inputs[(r, c)], signatures[(r, c)])
                unit.memory.self_observe()
                l6_outputs[(r, c)] = unit.anomaly_score()
                step_data[(r, c)] = unit_snapshot(unit)

        return step_data

    def run_phase(self, source_r, source_c, rounds, label='', noise_scale=0.05):
        """Run multiple rounds of step() with fixed source position.
        Returns trajectory: list of per-step snapshots."""
        traj = []
        for rnd in range(rounds):
            snap = self.step(source_r, source_c, noise_scale=noise_scale)
            snap['_round'] = rnd + 1
            snap['_phase'] = label
            snap['_source'] = (source_r, source_c)
            traj.append(snap)
        return traj


# ── Experiment runner ──
def run_experiment(alpha=0.7, cold_start=True, label=''):
    """Full Phase A -> Phase B -> Phase C experiment."""
    grid = BacteriaGrid(alpha=alpha, cold_start=cold_start)

    # Phase A: Cultivation — source at center, 30 rounds (learning)
    phase_a = grid.run_phase(3.5, 3.5, rounds=30, label=f'{label}_A')

    # Phase B: Perturbation — source moves to corner, 10 rounds
    phase_b = grid.run_phase(7.0, 7.0, rounds=10, label=f'{label}_B')

    # Phase C: Recovery — source stays at corner, 10 rounds
    phase_c = grid.run_phase(7.0, 7.0, rounds=10, label=f'{label}_C')

    return {
        'phase_a': phase_a,
        'phase_b': phase_b,
        'phase_c': phase_c,
        'grid': grid,
        'config': {'alpha': alpha, 'cold_start': cold_start, 'label': label},
    }


# ── Analysis ──
def spatial_response(trajectory, metric='l4_density'):
    """Extract spatial response: for each unit position, get metric value at each step."""
    positions = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
    result = {}
    for pos in positions:
        result[pos] = [snap[pos][metric] for snap in trajectory]
    return result


def distance_from_source(r, c, source_r, source_c):
    return math.sqrt((r - source_r) ** 2 + (c - source_c) ** 2)


def response_by_distance(trajectory, source_r, source_c, metric='l4_density'):
    """Group units by distance from source, compute mean metric per distance group."""
    dist_groups = {}
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            d = round(distance_from_source(r, c, source_r, source_c), 2)
            if d not in dist_groups:
                dist_groups[d] = []
            vals = [snap[(r, c)][metric] for snap in trajectory]
            dist_groups[d].append(statistics.mean(vals) if vals else 0)

    return {d: statistics.mean(vals) for d, vals in sorted(dist_groups.items())}


def print_grid_snapshot(snap, metric='l4_density'):
    """Print 4×4 heatmap of a metric from a snapshot."""
    print(f'  {metric}:')
    for r in range(GRID_SIZE):
        row_str = '    '
        for c in range(GRID_SIZE):
            val = snap[(r, c)][metric]
            row_str += f'{val:>8.4f} '
        print(row_str)


# ── Main ──
if __name__ == '__main__':
    t0 = time.time()

    print('=' * 65)
    print('BGM Experiment 2: Bacteria Grid (16 GEME, cold start, no G0)')
    print('=' * 65)

    # ── Primary experiment: cold start, alpha=0.7 ──
    print('\n' + '=' * 65)
    print('PRIMARY: Cold start, alpha=0.7, local communication')
    print('=' * 65)
    result = run_experiment(alpha=0.7, cold_start=True, label='cold_a07')

    # Phase A: final snapshot
    print('\nPhase A (cultivation) — final snapshot:')
    print_grid_snapshot(result['phase_a'][-1], 'l4_density')
    print_grid_snapshot(result['phase_a'][-1], 'mi')

    # Phase B: per-step spatial response
    print('\nPhase B (perturbation) — L4 density per step:')
    for i, snap in enumerate(result['phase_b']):
        print(f'  Step {i+1}:')
        print_grid_snapshot(snap, 'l4_density')

    # Phase B: L6 anomaly per step
    print('\nPhase B (perturbation) — L6 anomaly score per step:')
    for i, snap in enumerate(result['phase_b']):
        print(f'  Step {i+1}:')
        print_grid_snapshot(snap, 'l6')

    # Phase C: final snapshot
    print('\nPhase C (recovery) — final snapshot:')
    print_grid_snapshot(result['phase_c'][-1], 'l4_density')
    print_grid_snapshot(result['phase_c'][-1], 'mi')

    # ── Gradient correlation (spatial efficiency metric) ──
    def gradient_corr(snapshot, source_r, source_c, metric='l6', sigma=1.0):
        """Pearson r between unit metric and nutrient gradient distance."""
        unit_keys = [k for k in snapshot if isinstance(k, tuple)]
        actual = []
        expected = []
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                d2 = (r - source_r) ** 2 + (c - source_c) ** 2
                expected.append(math.exp(-d2 / (2 * sigma * sigma)))
                actual.append(snapshot[(r, c)][metric])
        n = len(actual)
        mx = sum(actual) / n; my = sum(expected) / n
        num = sum((actual[i] - mx) * (expected[i] - my) for i in range(n))
        dx = math.sqrt(sum((actual[i] - mx) ** 2 for i in range(n)))
        dy = math.sqrt(sum((expected[i] - my) ** 2 for i in range(n)))
        return num / (dx * dy) if dx * dy > 0 else 0.0

    print('\n' + '=' * 65)
    print('GRADIENT CORRELATION: L6/L4/MI vs nutrient gradient')
    print('=' * 65)
    phase_sources = [('Phase A (center)', result['phase_a'], 1.5, 1.5),
                     ('Phase B (corner)', result['phase_b'], 3.0, 3.0),
                     ('Phase C (corner)', result['phase_c'], 3.0, 3.0)]
    for phase_name, phase_data, sr, sc in phase_sources:
        snap = phase_data[-1]
        r_l6 = gradient_corr(snap, sr, sc, 'l6')
        r_l4 = gradient_corr(snap, sr, sc, 'l4_density')
        r_mi = gradient_corr(snap, sr, sc, 'mi')
        print(f'  {phase_name}: r(L6)={r_l6:+.4f}, r(L4)={r_l4:+.4f}, r(MI)={r_mi:+.4f}')

    # ── Spatial response curve ──
    print('\n' + '=' * 65)
    print('SPATIAL RESPONSE: L4 density vs distance from NEW source (Phase B)')
    print('=' * 65)
    resp = response_by_distance(result['phase_b'], 3.0, 3.0, 'l4_density')
    for d, val in sorted(resp.items()):
        bar = '#' * int(val * 100)
        print(f'  dist={d:.2f}: {val:.4f} {bar}')

    # ── Unit differentiation ──
    print('\n' + '=' * 65)
    print('DIFFERENTIATION: Phase C final — unit states')
    print('=' * 65)
    final = result['phase_c'][-1]
    print(f'  {"Pos":>6s} {"L4den":>8s} {"MI":>8s} {"L6":>6s} {"tau":>8s} {"frames":>7s} {"doubt":>6s} {"conf_th":>8s}')
    print(f'  {"-"*6} {"-"*8} {"-"*8} {"-"*6} {"-"*8} {"-"*7} {"-"*6} {"-"*8}')
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            u = final[(r, c)]
            print(f'  R{r}C{c}  {u["l4_density"]:>8.4f} {u["mi"]:>8.5f} {u["l6"]:>6.3f} '
                  f'{u["tau"]:>8.4f} {u["frames"]:>7d} {str(u["doubt"]):>6s} {u["conf_thresh"]:>8.4f}')

    # ── Sensitivity: alpha sweep ──
    print('\n' + '=' * 65)
    print('SENSITIVITY: Alpha sweep (cold start)')
    print('=' * 65)
    for alpha in [1.0, 0.7, 0.3, 0.0]:
        r = run_experiment(alpha=alpha, cold_start=True, label=f'sweep_a{alpha:.1f}')
        final_snap = r['phase_c'][-1]
        unit_keys = [k for k in final_snap if isinstance(k, tuple)]
        l4_vals = [final_snap[pos]['l4_density'] for pos in unit_keys]
        mi_vals = [final_snap[pos]['mi'] for pos in unit_keys]
        l6_vals = [final_snap[pos]['l6'] for pos in unit_keys]
        r_l6 = gradient_corr(final_snap, 3.0, 3.0, 'l6')
        print(f'  alpha={alpha:.1f}: L4=[{min(l4_vals):.4f},{max(l4_vals):.4f}] '
              f'MI=[{min(mi_vals):.5f},{max(mi_vals):.5f}] '
              f'L6=[{min(l6_vals):.3f},{max(l6_vals):.3f}] '
              f'r(L6)={r_l6:+.4f}')

    # ── Cold vs Warm start contrast ──
    print('\n' + '=' * 65)
    print('CONTRAST: Cold start vs Warm start (alpha=0.7)')
    print('=' * 65)
    for cold in [True, False]:
        r = run_experiment(alpha=0.7, cold_start=cold, label=f'contrast_{"cold" if cold else "warm"}')
        final_snap = r['phase_c'][-1]
        unit_keys = [k for k in final_snap if isinstance(k, tuple)]
        l4_vals = [final_snap[pos]['l4_density'] for pos in unit_keys]
        mi_vals = [final_snap[pos]['mi'] for pos in unit_keys]
        conf_vals = [final_snap[pos]['conf_thresh'] for pos in unit_keys]
        start_type = 'COLD' if cold else 'WARM'
        print(f'  {start_type}: L4 spread={max(l4_vals)-min(l4_vals):.4f}, '
              f'MI spread={max(mi_vals)-min(mi_vals):.5f}, '
              f'conf_thresh range=[{min(conf_vals):.4f}, {max(conf_vals):.4f}]')

    print(f'\nTotal time: {time.time() - t0:.0f}s')
