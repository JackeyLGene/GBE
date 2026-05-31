"""DNA: 4-species fork columns, Self cross-harm, exon/intron + shuffle."""
import sys, os, math, random, statistics as st
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'code'))
sys.stdout.reconfigure(line_buffering=True)
import geruon, numpy

HOM_DIR = os.path.join(ROOT, 'data', 'dna', 'hominid',
                       'DNA_vs_Protein_Alignments', 'DNA_Data_Hominid_Reference_Alignments',
                       'GENE_TREES_ENAMEL')
D, CAP, BIAS_W = 16, 24, 0.3; KAPPAS=[0.5,10.0,100.0]; STEP=3; MAX_COLS=2000
n2i={'A':0,'C':1,'G':2,'T':3}; ORDER=['Homo','Pan','Gorilla','Pongo']

def read_alignment(path):
    e,cl,cs=[],None,[]
    with open(path) as f:
        for line in f:
            line=line.strip()
            if line.startswith('>'):
                if cl and cs: e.append((cl,''.join(cs)))
                cl,cs=line[1:].strip(),[]
            else: cs.append(line.upper())
        if cl and cs: e.append((cl,''.join(cs)))
    return e

def sp_name(label):
    l=label.lower()
    if 'homo' in l or 'hg004' in l: return 'Homo'
    if 'pan' in l: return 'Pan'
    if 'gorilla' in l: return 'Gorilla'
    if 'pongo' in l: return 'Pongo'
    return label[:10]

def encode_column(bases):
    vec=[0.0]*D
    for si,b in enumerate(bases):
        if b in n2i: vec[si*4+n2i[b]]=1.0
    return vec

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

def run_trace(positions, seqs, n):
    bias=geruon.BiasField(vec_dim=D)
    cavities=[geruon.Geruon(vec_dim=D,memory_cap=CAP,kappa_tau=kv,bias_field=bias,bias_weight=BIAS_W) for kv in KAPPAS]
    H,cons=[],[]
    cnt=0
    for pos in positions:
        if cnt>=n: break
        bases=[s[pos] for s in seqs]
        if any(b not in 'ACGT' for b in bases): continue
        v=encode_column(bases)
        for g in cavities: g.process_vec(v, f'c{pos}')
        cs=[c for g in cavities if (c:=centroid_of(g)) is not None]
        if len(cs)==3:
            h=cross_harm(cs)
            if h is not None:
                n_same=max(sum(1 for b in bases if b==bases[0]),
                          sum(1 for b in bases if b==bases[1]),
                          sum(1 for b in bases if b==bases[2]),
                          sum(1 for b in bases if b==bases[3]))
                H.append(h); cons.append(n_same); cnt+=1
    return H,cons

# Load first gene
gf=[f for f in os.listdir(HOM_DIR) if f.endswith('.fa')][0]
entries=read_alignment(os.path.join(HOM_DIR, gf))
sm={}
for lab,seq in entries:
    sp=sp_name(lab)
    if sp not in sm: sm[sp]=seq
seqs=[sm[s] for s in ORDER]; n=min(len(s) for s in seqs)

# Real order
positions=list(range(0,n,STEP))
random.seed(42)
Hr,Cr=run_trace(positions,seqs,MAX_COLS)
random.shuffle(positions)
Hs,Cs=run_trace(positions,seqs,MAX_COLS)

# Results
for label,(H,C) in [("REAL",(Hr,Cr)),("SHUFFLED",(Hs,Cs))]:
    print(f"\n{label} ({len(H)} columns):")
    for lvl in [1,2,3,4]:
        vals=[h for h,c in zip(H,C) if c==lvl]
        if len(vals)>=2: print(f"  L{lvl} ({lvl}/4): H={st.mean(vals):.4f}±{st.stdev(vals):.4f} n={len(vals)}")
        elif vals: print(f"  L{lvl} ({lvl}/4): H={st.mean(vals):.4f} n={len(vals)}")
    v1=[h for h,c in zip(H,C) if c<=2]; v4=[h for h,c in zip(H,C) if c==4]
    if v1 and v4:
        d=(st.mean(v1)-st.mean(v4))/max(math.sqrt((numpy.var(v1)+numpy.var(v4))/2),0.001)
        print(f"  L1-2 vs L4: d={d:.3f} (L1-2 H={st.mean(v1):.4f} L4 H={st.mean(v4):.4f})")
