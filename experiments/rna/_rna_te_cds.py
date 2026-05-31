"""RNA TE — per-transcript cross-harm vs TE correlation."""
import sys, os, math, random, statistics as st
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'code'))
sys.stdout.reconfigure(line_buffering=True)
import geruon, numpy, pandas as pd

TE_DIR = os.path.join(ROOT, 'data', 'rna', 'te')
WINDOW, STRIDE, CAP, BIAS_W = 48, 24, 16, 0.3
n2i = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'U': 3}

def encode_trinuc(window):
    vec = [0.0] * 64
    for i in range(len(window) - 2):
        a, b, c = window[i], window[i+1], window[i+2]
        if a in n2i and b in n2i and c in n2i:
            vec[n2i[a]*16 + n2i[b]*4 + n2i[c]] += 1
    t = sum(vec); return [v/t for v in vec] if t > 0 else vec

def encode_dinuc(window):
    vec = [0.0] * 16
    for i in range(len(window) - 1):
        a, b = window[i], window[i+1]
        if a in n2i and b in n2i:
            vec[n2i[a]*4 + n2i[b]] += 1
    t = sum(vec); return [v/t for v in vec] if t > 0 else vec

def centroid_of(g):
    frames = g.memory.frames
    tw = sum(f.weight for f in frames)
    if tw <= 0: return None
    dim = g.vec_dim
    return tuple(sum(f.vec[j]*f.weight for f in frames)/tw for j in range(dim))

def run_self(windows, n=200):
    """Run Self-layer on up to n windows, return mean cross-harm."""
    if len(windows) < 20: return None
    n = min(n, len(windows))
    bias = geruon.BiasField(vec_dim=64)
    g_tri = geruon.Geruon(vec_dim=64, memory_cap=CAP, kappa_tau=0.5, bias_field=bias, bias_weight=BIAS_W)
    g_di = geruon.Geruon(vec_dim=16, memory_cap=CAP, kappa_tau=0.5)
    harms = []
    for i in range(n):
        tri_vec, di_vec = windows[i]
        g_tri.process_vec(tri_vec, f't{i}')
        g_di.process_vec(di_vec, f'd{i}')
        c_tri = centroid_of(g_tri); c_di = centroid_of(g_di)
        if c_tri and c_di:
            h = math.sqrt(sum((c_tri[j] - (c_di[j] if j < 16 else 0.0))**2 for j in range(64)))
            harms.append(h)
    return st.mean(harms) if harms else None

# ── Load parquet & extremes TSV ──
print("Loading...")
df = pd.read_parquet(os.path.join(TE_DIR, 'te_human.parquet'))
import csv
extreme_ids = set()
with open(os.path.join(TE_DIR, 'te_human_pilot_extremes_1500.tsv'), 'r') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        extreme_ids.add(row['transcript_id'])
df = df[df['transcript_id'].isin(extreme_ids)].copy()
print(f"Extremes: {len(df)}")

# ── Per-transcript: extract windows, compute cross-harm ──
# Use a random sample of N transcripts
random.seed(42)
sample = df.sample(min(120, len(df)), random_state=42)
results = []

for idx, (_, row) in enumerate(sample.iterrows()):
    seq = row['sequence']
    te = row['target']
    if len(seq) < WINDOW + STRIDE * 10: continue

    # Extract windows from full transcript
    wins = []
    for i in range(0, len(seq) - WINDOW + 1, STRIDE):
        w = seq[i:i+WINDOW]
        if 'N' in w or len(w) < WINDOW: continue
        wins.append((encode_trinuc(w), encode_dinuc(w)))
        if len(wins) >= 200: break

    if len(wins) < 20: continue
    h = run_self(wins, n=150)
    if h is not None:
        results.append((te, h, len(wins)))
        if (idx+1) % 20 == 0:
            print(f"  {idx+1}/{len(sample)} transcripts...")

print(f"\nScored: {len(results)} transcripts")

# ── Correlation ──
te_vals = [r[0] for r in results]
h_vals = [r[1] for r in results]
r_val = numpy.corrcoef(te_vals, h_vals)[0, 1]
print(f"\n{'='*60}")
print(f"PER-TRANSCRIPT TE vs CROSS-HARM")
print(f"  n = {len(results)} transcripts")
print(f"  TE range: [{min(te_vals):.2f}, {max(te_vals):.2f}]")
print(f"  harm range: [{min(h_vals):.4f}, {max(h_vals):.4f}]")
print(f"  r(TE, cross-harm) = {r_val:.4f}")

# Bootstrap
bs_r = []
for trial in range(20):
    idx = random.sample(range(len(results)), min(80, len(results)))
    te_b = [te_vals[i] for i in idx]
    h_b = [h_vals[i] for i in idx]
    bs_r.append(numpy.corrcoef(te_b, h_b)[0, 1])
print(f"  Bootstrap r: {st.mean(bs_r):.3f} ± {st.stdev(bs_r):.3f}")

# High vs Low split
med = numpy.median(te_vals)
high_h = [h_vals[i] for i in range(len(results)) if te_vals[i] > med]
low_h = [h_vals[i] for i in range(len(results)) if te_vals[i] < med]
def cd(a,b):
    p = math.sqrt((numpy.var(a)+numpy.var(b))/2)
    return (st.mean(a)-st.mean(b))/max(p,0.0001)
print(f"  High TE harm: {st.mean(high_h):.4f}, Low TE harm: {st.mean(low_h):.4f}, d={cd(high_h, low_h):.3f}")
