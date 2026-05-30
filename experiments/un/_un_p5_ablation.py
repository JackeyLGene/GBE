"""UN P5 Ablation — No-P5, P5-only, Random-5, No-USA. Matches calibrate encode()."""
import csv, math, collections, sys, os, random
sys.stdout.reconfigure(encoding='utf-8')
from geruon import Geruon

P5 = ['USA','GBR','FRA','RUS','CHN']; D=12; CAP=64; KAPPA=3

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'un_votes')
ideal = collections.defaultdict(dict)
with open(os.path.join(data_dir, 'Idealpointestimates1946-2025.tab'), 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        ideal[int(row['year'])][row['iso3c']] = float(row['IdealPointFP'])

fred = {}
fred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'econ_data', 'fred_annual.csv')
if os.path.exists(fred_path):
    with open(fred_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            yr = int(list(row.values())[0])
            vs = [float(v) for v in list(row.values())[1:] if v]
            if vs: fred[yr] = vs

yrs = sorted(ideal.keys())
all_countries = sorted(set(c for y in yrs for c in ideal[y] if c and c not in P5))

def encode_generic(yr, p5_list, add_fred=True):
    """Exact same logic as calibrate encode() but with configurable P5 block."""
    ips = ideal.get(yr, {}); vals = list(ips.values()); n = len(vals)
    if n == 0: return [0.0] * D
    m = sum(vals) / n
    std = math.sqrt(sum((x - m) ** 2 for x in vals) / max(n, 1))
    pos = [x for x in vals if x > 0]; neg = [x for x in vals if x < 0]
    pl = abs(sum(pos) / max(1, len(pos)) - sum(neg) / max(1, len(neg))) if pos and neg else 0
    v = [m, std, pl, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    if p5_list:
        p5v = [ips.get(c, 0.0) for c in p5_list]
        p5m = sum(p5v) / max(len(p5v), 1)
        v[3] = p5m
        v[4] = math.sqrt(sum((x - p5m) ** 2 for x in p5v) / max(len(p5v), 1))
        for i, x in enumerate(p5v[:5]):
            v[5 + i] = x
    if add_fred and yr in fred:
        fv = fred[yr]
        v[10] = fv[3] / 10.0
        v[11] = fv[5] / 10.0
    return v

def nrm(v):
    s = math.sqrt(sum(x*x for x in v))
    return [x/s for x in v] if s>0 else v[:]

def run_displacement(encoding_fn, desc=""):
    """Matches _un_calibrate.py exactly: nrm(encode) → process_vec → arrow_output displacement."""
    g = Geruon(vec_dim=D, memory_cap=CAP, kappa_tau=KAPPA)
    prev = [0.0]*D
    disps = {}
    for yr in yrs:
        v = nrm(encoding_fn(yr))
        g.process_vec(v, f'Y{yr}')
        c = list(g.arrow_output())
        d = math.sqrt(sum((x-y)**2 for x, y in zip(prev, c)))
        disps[yr] = d
        prev = c
    return disps

def rank_and_val(disps, yr):
    valid = [(y, v) for y, v in disps.items() if y != 1946]
    valid.sort(key=lambda x: x[1], reverse=True)
    for i, (y, v) in enumerate(valid):
        if y == yr: return i + 1, v
    return -1, 0

# ── Run all variants ──
print("No-P5...");     d_nop5 = run_displacement(lambda yr: encode_generic(yr, None))
print("P5-aug...");    d_p5 = run_displacement(lambda yr: encode_generic(yr, P5))
print("P5-only...");   d_p5only = run_displacement(lambda yr: encode_generic(yr, P5, add_fred=False))
print("No-USA...");    d_nousa = run_displacement(lambda yr: encode_generic(yr, [c for c in P5 if c != 'USA']))
print("No-RUS...");    d_norus = run_displacement(lambda yr: encode_generic(yr, [c for c in P5 if c != 'RUS']))

# Random-5 (5 trials)
random.seed(42)
r5_trials = []
for trial in range(5):
    r5 = random.sample(all_countries, 5)
    d = run_displacement(lambda yr, r=r5: encode_generic(yr, r))
    r5_trials.append(d)
    print(f"Random-5 #{trial}: {r5[:3]}...")

# ── Table ──
print("\n" + "=" * 70)
print("P5 ABLATION: 2025 Displacement Ranking")
print(f"{'Encoding':<22s} {'2025 disp':>10s} {'Rank':>6s}  {'Top-3 years (excl 1946)':<30s}")
print("-" * 70)

for name, d in [("No-P5", d_nop5), ("P5-augmented", d_p5),
                ("P5-only", d_p5only), ("No-USA", d_nousa), ("No-RUS", d_norus)]:
    r, v = rank_and_val(d, 2025)
    top3 = sorted([(y, vv) for y, vv in d.items() if y != 1946], key=lambda x: x[1], reverse=True)[:3]
    top_str = ', '.join(f'{y}:{vv:.4f}' for y, vv in top3)
    print(f"{name:<22s} {v:>10.4f} {r:>4d}/78  {top_str}")

# Random-5 summary
r5_vals = [d.get(2025, 0) for d in r5_trials]
r5_ranks = [rank_and_val(d, 2025)[0] for d in r5_trials]
print(f"{'Random-5 (mean)':<22s} {sum(r5_vals)/len(r5_vals):>10.4f} {int(sum(r5_ranks)/len(r5_ranks)):>4d}/78  range [{min(r5_vals):.4f}, {max(r5_vals):.4f}]")

# ── Critical check ──
r, v = rank_and_val(d_nop5, 2025)
print(f"\n=== Critical: No-P5 2025 = {v:.4f}, rank {r}/78 ===")
if r <= 5:
    print("  >>> PASS: No-P5 signal is historically extreme")
elif r <= 15:
    print("  >>> WEAK: No-P5 signal is elevated but not extreme")
else:
    print("  >>> FAIL: No-P5 signal is not historically distinguishable")
