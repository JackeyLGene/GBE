"""RNA closure: save results, process-permutation, RPF/Seq/fork ablation."""
import sys, os, math, random, statistics as st, gzip, collections, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'code'))
sys.stdout.reconfigure(line_buffering=True)
import geruon, numpy, pandas as pd, pybigtools

BW_DIR = os.path.join(ROOT, 'data', 'rna', 'rpfdb',
                       'HeLa_GSE79664', 'Hsapiens_GSE79664_RPF')
TE_DIR = os.path.join(ROOT, 'data', 'rna', 'te')
GTF_PATH = os.path.join(ROOT, 'data', 'rna', 'gencode',
                        'gencode.v49.primary_assembly.annotation.gtf.gz')
DERIVED_DIR = os.path.join(ROOT, 'data', 'rna', 'derived')
os.makedirs(DERIVED_DIR, exist_ok=True)
CAP, BIAS_W = 24, 0.3; WINDOW, STRIDE = 256, 64
KAPPAS=[0.5,10.0,100.0]
n2i={'A':0,'C':1,'G':2,'T':3}

def centroid_of(g):
    frames=g.memory.frames; tw=sum(f.weight for f in frames)
    if tw<=0: return None
    return tuple(sum(f.vec[j]*f.weight for f in frames)/tw for j in range(g.vec_dim))

def cross_harm(cs, D):
    if len(cs)<3: return None
    s=0.0
    for i in range(3):
        for j in range(i+1,3):
            s+=math.sqrt(sum((cs[i][k]-cs[j][k])**2 for k in range(D)))
    return s/3.0

# ── Parse GTF ──
print("Parsing GTF...")
enst_exons=collections.defaultdict(list)
enst_strand={}; enst_chr={}
with gzip.open(GTF_PATH,'rt') as f:
    for line in f:
        if line.startswith('#'): continue
        parts=line.strip().split('\t')
        if len(parts)<9: continue
        chrom,_,feat,start,end,_,strand,_,attrs=parts
        if feat!='exon': continue
        tid=None
        for a in attrs.split(';'):
            a=a.strip()
            if a.startswith('transcript_id '):
                tid=a.split()[1].strip('"').split('.')[0]; break
        if tid: enst_exons[tid].append((int(start),int(end)))
        if tid: enst_strand[tid]=strand; enst_chr[tid]=chrom

bw_files=sorted([f for f in os.listdir(BW_DIR) if f.endswith('.bw')])
bws=[pybigtools.open(os.path.join(BW_DIR, f)) for f in bw_files]
N_RPF=len(bws)

def tx_to_geno(tx_pos, exons_sorted, strand):
    cum=0
    for estart,eend in exons_sorted:
        elen=eend-estart+1
        if cum<=tx_pos<cum+elen:
            return estart+(tx_pos-cum) if strand=='+' else eend-(tx_pos-cum)
        cum+=elen
    return None

df=pd.read_parquet(os.path.join(TE_DIR, 'te_human.parquet'))
df['cds_len']=[int(numpy.sum(r['cds'].astype(numpy.int32))) for _,r in df.iterrows()]
df['tid_clean']=[t.split('.')[0] for t in df['transcript_id']]
df=df[(df['cds_len']>200)&(df['tid_clean'].isin(enst_exons.keys()))].head(60)
print(f"  Transcripts: {len(df)}")

# ── Build per-window records ──
records=[]  # {transcript, window_idx, label, harm_fork, harm_seq, rpf_mean, rpf_views}
random.seed(42)

for idx,(_,row) in enumerate(df.iterrows()):
    tid=row['tid_clean']; seq=row['sequence']; cds_mask=row['cds']
    exons=sorted(enst_exons[tid]); strand=enst_strand.get(tid,'+')
    chrom=enst_chr.get(tid,'chr1')

    # Collect columns
    columns, labels, rpf_vecs, seq_vecs=[],[],[],[]
    for i in range(0, len(seq)-WINDOW+1, STRIDE):
        w=seq[i:i+WINDOW]
        if any(c not in 'ACGT' for c in w): continue
        cds_count=int(numpy.sum(cds_mask[i:min(i+WINDOW,len(cds_mask))].astype(numpy.int32)))
        win_start=tx_to_geno(i, exons, strand)
        win_end=tx_to_geno(min(i+WINDOW, len(seq)-1), exons, strand)
        if win_start is None or win_end is None: continue

        # Sequence vector (4-dim one-hot)
        mid_base=w[len(w)//2] if len(w)//2<len(w) else w[0]
        svec=[0.0]*4
        if mid_base in n2i: svec[n2i[mid_base]]=1.0

        # RPF values
        rpfs=[]
        for vi in range(N_RPF):
            vals=bws[vi].values(chrom, min(win_start,win_end), max(win_start,win_end)+1)
            rpfs.append(float(numpy.nansum(vals)) if vals is not None else 0.0)

        seq_vecs.append(svec)
        rpf_vecs.append(rpfs)
        labels.append('CDS' if cds_count>=WINDOW/6 else ('UTR' if cds_count==0 else 'mix'))
        if len(seq_vecs)>=60: break

    if len(seq_vecs)<15: continue

    # ── Fork column: [seq(4) + rpf_log(N_RPF)] ──
    D_fork=4+N_RPF
    fork_cols=[]
    for svec, rpfs in zip(seq_vecs, rpf_vecs):
        col=svec+[math.log1p(max(r,0.01)) for r in rpfs]
        fork_cols.append(col)

    # Fork Self
    bias=geruon.BiasField(vec_dim=D_fork)
    cavities=[geruon.Geruon(vec_dim=D_fork,memory_cap=CAP,kappa_tau=kv,bias_field=bias,bias_weight=BIAS_W) for kv in KAPPAS]
    fork_harms=[]
    for col in fork_cols:
        for g in cavities: g.process_vec(col,f'f{idx}')
        cs=[c for g in cavities if (c:=centroid_of(g)) is not None]
        fork_harms.append(cross_harm(cs,D_fork) if len(cs)==3 else None)

    # Sequence-only Self (D=4)
    bias2=geruon.BiasField(vec_dim=4)
    cavities2=[geruon.Geruon(vec_dim=4,memory_cap=CAP,kappa_tau=kv,bias_field=bias2,bias_weight=BIAS_W) for kv in KAPPAS]
    seq_harms=[]
    for svec in seq_vecs:
        for g in cavities2: g.process_vec(svec,f's{idx}')
        cs=[c for g in cavities2 if (c:=centroid_of(g)) is not None]
        seq_harms.append(cross_harm(cs,4) if len(cs)==3 else None)

    # RPF-only Self (D=N_RPF)
    bias3=geruon.BiasField(vec_dim=N_RPF)
    cavities3=[geruon.Geruon(vec_dim=N_RPF,memory_cap=CAP,kappa_tau=kv,bias_field=bias3,bias_weight=BIAS_W) for kv in KAPPAS]
    rpf_cols=[[math.log1p(max(r,0.01)) for r in rpfs] for rpfs in rpf_vecs]
    rpf_harms=[]
    for col in rpf_cols:
        for g in cavities3: g.process_vec(col,f'r{idx}')
        cs=[c for g in cavities3 if (c:=centroid_of(g)) is not None]
        rpf_harms.append(cross_harm(cs,N_RPF) if len(cs)==3 else None)

    # Process-permutation: shuffle RPF across windows, keep sequence fixed
    shuf_rpfs=rpf_vecs.copy(); random.shuffle(shuf_rpfs)
    perm_cols=[]
    for svec, rpfs in zip(seq_vecs, shuf_rpfs):
        perm_cols.append(svec+[math.log1p(max(r,0.01)) for r in rpfs])
    bias4=geruon.BiasField(vec_dim=D_fork)
    cavities4=[geruon.Geruon(vec_dim=D_fork,memory_cap=CAP,kappa_tau=kv,bias_field=bias4,bias_weight=BIAS_W) for kv in KAPPAS]
    perm_harms=[]
    for col in perm_cols:
        for g in cavities4: g.process_vec(col,f'p{idx}')
        cs=[c for g in cavities4 if (c:=centroid_of(g)) is not None]
        perm_harms.append(cross_harm(cs,D_fork) if len(cs)==3 else None)

    # Save per-window records
    for i in range(len(seq_vecs)):
        if all(h is not None for h in [fork_harms[i], seq_harms[i], rpf_harms[i], perm_harms[i]]):
            records.append({
                'transcript': tid[:20],
                'window': i,
                'label': labels[i],
                'harm_fork': round(fork_harms[i],6),
                'harm_seq': round(seq_harms[i],6),
                'harm_rpf': round(rpf_harms[i],6),
                'harm_perm': round(perm_harms[i],6),
                'rpf_mean': round(numpy.mean(rpf_vecs[i]),4),
            })

    if (idx+1)%30==0: print(f"  {idx+1}/{len(df)}...", flush=True)

for bw in bws: bw.close()

# ── Save TSV/JSON ──
import csv
tsv_path=os.path.join(DERIVED_DIR, 'rna_phase2_results.tsv')
with open(tsv_path,'w',newline='') as f:
    w=csv.DictWriter(f,delimiter='\t',fieldnames=records[0].keys())
    w.writeheader(); w.writerows(records)
json_path=os.path.join(DERIVED_DIR, 'rna_phase2_results.json')
with open(json_path,'w') as f:
    json.dump({'n_windows':len(records),'records':records[:50]},f,indent=2)
print(f"\nSaved: {len(records)} windows -> {tsv_path}")

# ── Results table ──
def cd(a,b):
    if not a or not b: return float('nan')
    p=math.sqrt((numpy.var(a)+numpy.var(b))/2)
    return (st.mean(a)-st.mean(b))/max(p,0.001)

cds_idx=[i for i,r in enumerate(records) if r['label']=='CDS']
utr_idx=[i for i,r in enumerate(records) if r['label']=='UTR']

print(f"\n{'='*60}")
print(f"ABLATION: {len(records)} windows (CDS={len(cds_idx)} UTR={len(utr_idx)})")

for name, key in [('Fork [Seq+RPF]','harm_fork'),('Sequence-only','harm_seq'),
                   ('RPF-only','harm_rpf'),('Process-permuted','harm_perm')]:
    cds_h=[records[i][key] for i in cds_idx]
    utr_h=[records[i][key] for i in utr_idx]
    d=cd(cds_h, utr_h)
    print(f"  {name:<20s}: CDS={st.mean(cds_h):.4f} UTR={st.mean(utr_h):.4f} d={d:.3f}")

# Key comparison: fork vs RPF-only
print(f"\n  Fork > RPF-only? d_fork={cd([records[i]['harm_fork'] for i in cds_idx],[records[i]['harm_fork'] for i in utr_idx]):.3f} vs d_rpf={cd([records[i]['harm_rpf'] for i in cds_idx],[records[i]['harm_rpf'] for i in utr_idx]):.3f}")
print(f"  Permutation gap: d_real={cd([records[i]['harm_fork'] for i in cds_idx],[records[i]['harm_fork'] for i in utr_idx]):.3f} vs d_perm={cd([records[i]['harm_perm'] for i in cds_idx],[records[i]['harm_perm'] for i in utr_idx]):.3f}")
