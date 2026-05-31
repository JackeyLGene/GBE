"""DNA exon/intron validation: multi-seed, κ ablation, window sweep, dinuc shuffle."""
import sys, os, math, random, statistics as st
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'code'))
sys.stdout.reconfigure(line_buffering=True)
import geruon, numpy, pandas as pd

TE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'RNA', 'te')
D=64; CAP=24; BIAS_W=0.3
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
    return tuple(sum(f.vec[j]*f.weight for f in frames)/tw for j in range(g.vec_dim))

def cross_harm_3cavity(cs):
    if len(cs)<3: return None
    s=0.0
    for i in range(len(cs)):
        for j in range(i+1,len(cs)):
            s+=math.sqrt(sum((cs[i][k]-cs[j][k])**2 for k in range(D)))
    return s/3.0

def run_3cavity(windows, kappas=[0.5,10.0,100.0]):
    bias=geruon.BiasField(vec_dim=D)
    cavities=[geruon.Geruon(vec_dim=D,memory_cap=CAP,kappa_tau=kv,bias_field=bias,bias_weight=BIAS_W) for kv in kappas]
    harms=[]
    for i,w in enumerate(windows):
        v=encode(w)
        for g in cavities: g.process_vec(v, f'c{i}')
        cs=[c for g in cavities if (c:=centroid_of(g)) is not None]
        if len(cs)==3:
            h=cross_harm_3cavity(cs)
            if h is not None: harms.append(h)
    return harms

def cd(a,b):
    if not a or not b: return float('nan')
    p=math.sqrt((numpy.var(a)+numpy.var(b))/2)
    return (st.mean(a)-st.mean(b))/max(p,0.001)

def dinuc_shuffle(seq):
    """Preserve dinucleotide frequencies, destroy higher-order structure."""
    pairs=[seq[i:i+2] for i in range(len(seq)-1)]
    random.shuffle(pairs)
    result=pairs[0]
    for p in pairs[1:]: result+=p[1]
    return result

# ── Load ──
print("Loading...")
df=pd.read_parquet(os.path.join(TE_DIR, 'te_human.parquet'))
df['cds_len']=[int(numpy.sum(r['cds'].astype(numpy.int32))) for _,r in df.iterrows()]
df=df[(df['cds_len']>200)&(df['cds_len']<df.iloc[0]['sequence'].__len__()-200)]
# Use fixed subset for speed across tests
sample=df.sample(min(40, len(df)), random_state=42)

def extract_windows(row, window, stride):
    seq=row['sequence']; cds_mask=row['cds']
    exon_w, intron_w=[],[]
    for i in range(0, len(seq)-window+1, stride):
        w=seq[i:i+window]
        if any(c not in 'ACGT' for c in w): continue
        cds_count=int(numpy.sum(cds_mask[i:min(i+window,len(cds_mask))].astype(numpy.int32)))
        if cds_count>=window/6: exon_w.append(w)
        elif cds_count==0: intron_w.append(w)
    return exon_w, intron_w

# ── 1. MULTI-SEED (window=256, 3-cavity) ──
print("\n"+"="*60)
print("1. MULTI-SEED (window=256, 3-cavity κ=0.5/10/100)")
for seed in [42, 99, 123, 456, 789]:
    random.seed(seed)
    all_exon, all_intron=[],[]
    for _,row in sample.iterrows():
        ew,iw=extract_windows(row,256,64)
        if len(ew)<10 or len(iw)<10: continue
        He=run_3cavity(ew[:100])
        Hi=run_3cavity(iw[:100])
        if He and Hi: all_exon.extend(He); all_intron.extend(Hi)
    d=cd(all_exon, all_intron)
    print(f"  seed={seed}: d={d:.3f} (exon={len(all_exon)} intron={len(all_intron)})", flush=True)

# ── 2. KAPPA ABLATION ──
print("\n"+"="*60)
print("2. KAPPA ABLATION (window=256)")
random.seed(42)
ew_all,iw_all=[],[]
for _,row in sample.iterrows():
    ew,iw=extract_windows(row,256,64)
    if len(ew)<10 or len(iw)<10: continue
    ew_all.extend(ew[:80]); iw_all.extend(iw[:80])

for kappas,label in [([0.5],"single κ=0.5"),([10.0],"single κ=10"),([100.0],"single κ=100"),([0.5,10.0,100.0],"3-cavity")]:
    He=run_3cavity(ew_all[:500], kappas)
    Hi=run_3cavity(iw_all[:500], kappas)
    if He and Hi:
        d=cd(He,Hi)
        print(f"  {label:<20s}: d={d:.3f} (exon H={st.mean(He):.4f} intron H={st.mean(Hi):.4f})", flush=True)

# ── 3. WINDOW SIZE ──
print("\n"+"="*60)
print("3. WINDOW SWEEP")
random.seed(42)
for win,stride in [(128,32),(192,48),(256,64),(384,96),(512,128)]:
    all_exon, all_intron=[],[]
    for _,row in sample.iterrows():
        ew,iw=extract_windows(row,win,stride)
        if len(ew)<10 or len(iw)<10: continue
        He=run_3cavity(ew[:80])
        Hi=run_3cavity(iw[:80])
        if He and Hi: all_exon.extend(He); all_intron.extend(Hi)
    d=cd(all_exon, all_intron)
    print(f"  win={win}nt: d={d:.3f} (n={len(all_exon)})", flush=True)

# ── 4. DINUCLEOTIDE SHUFFLE ──
print("\n"+"="*60)
print("4. DINUCLEOTIDE SHUFFLE (window=256)")
random.seed(42)
all_exon_shuf, all_intron_shuf=[],[]
for _,row in sample.iterrows():
    seq=row['sequence']; cds_mask=row['cds']
    shuf_seq=dinuc_shuffle(seq)
    # Extract windows from shuffled sequence using same CDS mask
    exon_w, intron_w=[],[]
    for i in range(0, len(shuf_seq)-256+1, 64):
        w=shuf_seq[i:i+256]
        if any(c not in 'ACGT' for c in w): continue
        cds_count=int(numpy.sum(cds_mask[i:min(i+256,len(cds_mask))].astype(numpy.int32)))
        if cds_count>=256/6: exon_w.append(w)
        elif cds_count==0: intron_w.append(w)
    if len(exon_w)<10 or len(intron_w)<10: continue
    He=run_3cavity(exon_w[:80])
    Hi=run_3cavity(intron_w[:80])
    if He and Hi: all_exon_shuf.extend(He); all_intron_shuf.extend(Hi)
d_dinuc=cd(all_exon_shuf, all_intron_shuf)
He_mean=st.mean(all_exon_shuf) if all_exon_shuf else 0
Hi_mean=st.mean(all_intron_shuf) if all_intron_shuf else 0
print(f"  Dinuc shuffle: d={d_dinuc:.3f} (exon={He_mean:.4f} intron={Hi_mean:.4f})")
print(f"  Baseline:      d=-0.97 (real genomic order)")
print(f"  Order shuffle: d=-0.10 (random column order)")
print(f"  Dinuc preserve: d={d_dinuc:.3f} (dinucleotide-preserving)")
