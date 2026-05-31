"""DNA: genomic-order Self + shuffle control, large sample."""
import sys, os, math, random, statistics as st
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'code'))
sys.stdout.reconfigure(line_buffering=True)
import geruon, numpy, pandas as pd

TE_DIR = os.path.join(ROOT, 'data', 'rna', 'te')
WINDOW, STRIDE, CAP, BIAS_W = 256, 64, 24, 0.3
D=64; KAPPAS=[0.5, 10.0, 100.0]
n2i={'A':0,'C':1,'G':2,'T':3}

def encode(w):
    vec=[0.0]*D
    for i in range(len(w)-3+1):
        idx=0; ok=True
        for j in range(3):
            c=w[i+j]
            if c not in n2i: ok=False; break
            idx=idx*4+n2i[c]
        if ok: vec[idx]+=1
    t=sum(vec); return [v/t for v in vec] if t>0 else vec

def centroid_of(g):
    frames=g.memory.frames; tw=sum(f.weight for f in frames)
    if tw<=0: return None
    return tuple(sum(f.vec[j]*f.weight for f in frames)/tw for j in range(D))

def cross_harm(cs):
    if len(cs)<3: return None
    s=0.0
    for i in range(len(cs)):
        for j in range(i+1,len(cs)):
            s+=math.sqrt(sum((cs[i][k]-cs[j][k])**2 for k in range(D)))
    return s/3.0

def run_self_trace(windows, labels):
    """Run 3-cavity Self on genomic-order windows, return (harm_list, label_list)."""
    bias=geruon.BiasField(vec_dim=D)
    cavities=[]
    for kv in KAPPAS:
        g=geruon.Geruon(vec_dim=D, memory_cap=CAP, kappa_tau=kv,
                        bias_field=bias, bias_weight=BIAS_W)
        cavities.append(g)
    harms, harm_labels=[],[]
    for i, w in enumerate(windows):
        v=encode(w)
        for g in cavities: g.process_vec(v, f'g{i}')
        cs=[c for g in cavities if (c:=centroid_of(g)) is not None]
        if len(cs)==3:
            h=cross_harm(cs)
            if h is not None:
                harms.append(h); harm_labels.append(labels[i])
    return harms, harm_labels

print("Loading...")
df=pd.read_parquet(os.path.join(TE_DIR, 'te_human.parquet'))
df['cds_len']=[int(numpy.sum(r['cds'].astype(numpy.int32))) for _,r in df.iterrows()]
df=df[(df['cds_len']>200)&(df['cds_len']<df.iloc[0]['sequence'].__len__()-200)]

random.seed(42)
sample=df.sample(min(200, len(df)), random_state=42)
all_exon, all_intron = [],[]
all_exon_shuf, all_intron_shuf = [],[]

for idx,(_,row) in enumerate(sample.iterrows()):
    seq=row['sequence']; cds_mask=row['cds']
    if len(seq)<WINDOW+STRIDE*30: continue

    windows, labels=[],[]
    for i in range(0, len(seq)-WINDOW+1, STRIDE):
        w=seq[i:i+WINDOW]
        if any(c not in 'ACGT' for c in w): continue
        cds_count=int(numpy.sum(cds_mask[i:min(i+WINDOW,len(cds_mask))].astype(numpy.int32)))
        windows.append(w)
        labels.append('exon' if cds_count>=WINDOW/6 else ('intron' if cds_count==0 else 'mix'))
        if len(windows)>=150: break
    if len(windows)<15: continue

    # Real genomic order
    harms, hl = run_self_trace(windows, labels)
    for h,l in zip(harms,hl):
        if l=='exon': all_exon.append(h)
        elif l=='intron': all_intron.append(h)

    # Shuffled order (same windows, scrambled sequence)
    shuf_idx = list(range(len(windows))); random.shuffle(shuf_idx)
    shuf_win = [windows[i] for i in shuf_idx]
    shuf_lbl = [labels[i] for i in shuf_idx]
    harms_s, hl_s = run_self_trace(shuf_win, shuf_lbl)
    for h,l in zip(harms_s, hl_s):
        if l=='exon': all_exon_shuf.append(h)
        elif l=='intron': all_intron_shuf.append(h)

    if (idx+1)%40==0: print(f"  {idx+1}/{len(sample)}...", flush=True)

# ── Results ──
print(f"\n{'='*60}")
print(f"GENOMIC-ORDER SELF ({len(sample)} transcripts)")
for label, vals, shuf_vals in [("exon", all_exon, all_exon_shuf),
                                 ("intron", all_intron, all_intron_shuf)]:
    print(f"  {label}: real={st.mean(vals):.4f}±{st.stdev(vals):.4f} (n={len(vals)})  "
          f"shuf={st.mean(shuf_vals):.4f}±{st.stdev(shuf_vals):.4f} (n={len(shuf_vals)})")

def cd(a,b):
    if not a or not b: return float('nan')
    p=math.sqrt((numpy.var(a)+numpy.var(b))/2)
    return (st.mean(a)-st.mean(b))/max(p,0.001)

d_real=cd(all_exon, all_intron)
d_shuf=cd(all_exon_shuf, all_intron_shuf)
print(f"\n  d_real (exon vs intron) = {d_real:.3f}")
print(f"  d_shuf (shuffled order)  = {d_shuf:.3f}")
print(f"  Δd = {abs(d_real)-abs(d_shuf):+.3f}")
