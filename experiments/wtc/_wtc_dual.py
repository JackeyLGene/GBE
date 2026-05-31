"""WTC Dual-Self + Harm-Geruon × 3-Gen Codex.

每个 Gen: chroma+IOI Self → harm箭 → harm-Geruon(慢) → precipitate → enrich → Codex.
Gen2/Gen3 的 harm-Geruon 继承上一代 Codex.
"""

import pickle, math, sys, io, importlib, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'code'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import geruon, we_core
from geruon import Geruon, BiasField, Codex

D=12; CAP=16; GI=4; WINDOW=8; HARM_KAPPA=10; HARM_CAP=12; N_PIECES=1  # single piece, repeated

def nrm(v):
    s=math.sqrt(sum(x*x for x in v))
    return [x/s for x in v] if s>0 else v[:]

def encode(events):
    cv=[]; iv=[]; active=set(); ioi_win=[]; prev_t=None
    for t,p,v,on in events:
        if on and v>0: active.add(p)
        else: active.discard(p)
        c=[0.0]*D
        for pitch in active: c[pitch%12]+=1.0
        s=math.sqrt(sum(x*x for x in c))
        if s>0: c=[x/s for x in c]
        cv.append(c)
        if prev_t is not None and t>prev_t:
            ioi_win.append(t-prev_t)
            if len(ioi_win)>WINDOW: ioi_win.pop(0)
        prev_t=t
        i=[0.0]*D
        for dt in ioi_win:
            bi=min(D-1,max(0,int(math.log10(dt+1)*2.5)))
            i[bi]+=1.0
        s=math.sqrt(sum(x*x for x in i))
        if s>0: i=[x/s for x in i]
        iv.append(i)
    return cv,iv

def run_piece_with_harm_geruon(cv, iv, hg, codex, field):
    """Run dual-Self on one piece, feeding harm-Geruon. Returns readings."""
    importlib.reload(geruon); importlib.reload(we_core)

    wc=we_core.We(n_selves=1,vec_dim=D,cap=CAP,seed=42,
                  cavity_quantum=False,collective_quantum=False)
    wc.init_generation(); cs=wc.selves[0]
    wi=we_core.We(n_selves=1,vec_dim=D,cap=CAP,seed=99,
                  cavity_quantum=False,collective_quantum=False)
    wi.init_generation(); is_=wi.selves[0]

    # harm-Geruon: write-only to BiasField (accumulates relational knowledge)
    hg.codex=codex
    hg.bias_field=field

    # ── BiasField → Codex translation ──
    # The BiasField accumulated cross-Self relational patterns.
    # Translate significant bias dimensions into Codex symbols that Selfs can query.
    if not field.is_empty():
        for g in cs + is_:
            # Seed frames from bias gives the Self initial structural vocabulary
            field.seed_frames(g.memory, count=4)
            # Also set codex for process-time lookup
            g.codex = codex

    n=len(cv); harm_c2i=0; harm_i2c=0
    hg_disps=[]; hg_prev=[0.0]*D

    for idx in range(n):
        for g in cs: g.process_vec(nrm(cv[idx]),'C')
        for g in is_: g.process_vec(nrm(iv[idx]),'I')
        if idx>0 and idx%(GI*GI)==0:
            for src,dst,dname in [(cs,is_,'C->I'),(is_,cs,'I->C')]:
                for g_src in src:
                    arrow=list(g_src.arrow_output())
                    field.deposit(arrow,weight=0.5)
                    for g_dst in dst:
                        nb=len(g_dst.memory.frames)
                        g_dst.process_vec(arrow,'X'+dname)
                        if len(g_dst.memory.frames)>nb:
                            if dname=='C->I': harm_c2i+=1
                            else: harm_i2c+=1

            # Feed harm-Geruon
            src_arrow=list(cs[0].arrow_output())
            hg.process_vec(nrm(src_arrow),'H')
            hg_cur=list(hg.arrow_output())
            hg_disps.append(math.sqrt(sum((x-y)**2 for x,y in zip(hg_prev,hg_cur))))
            hg_prev=hg_cur

    return {'harm':harm_c2i+harm_i2c, 'c2i':harm_c2i, 'i2c':harm_i2c,
            'hg_disp_mean':sum(hg_disps)/len(hg_disps) if hg_disps else 0,
            'hg_tau':hg.tau, 'hg_frames':len(hg.memory.frames)}

# ── Load ──
pieces_data=[]
TEST_PIECE = 0  # C major
for i in [TEST_PIECE]:
    with open('data/wtc_pieces/wtc_%02d.pkl'%i,'rb') as f:
        events,_=pickle.load(f)
    cv,iv=encode(events)
    ptype='Prelude' if i%2==0 else 'Fugue'
    pieces_data.append((cv,iv,ptype,i))

# ── 3 Gens ──
print('=== 3-Gen harm-Geruon Codex ===\n')
codex=Codex.empty(name='harm_gen0',vec_dim=D)
field=BiasField(vec_dim=D)
hg=Geruon(vec_dim=D,memory_cap=HARM_CAP,kappa_tau=HARM_KAPPA)

gen_results=[]

N_GENS=10; REPEATS=1
for gen_idx in range(N_GENS):
    gen_label='Gen%d'%(gen_idx+1)
    print('%s (Codex=%d):' % (gen_label, len(codex._table)), end=' ', flush=True)

    piece_rds=[]
    for cv,iv,ptype,pidx in pieces_data:
        for rep in range(REPEATS):
            r=run_piece_with_harm_geruon(cv,iv,hg,codex,field)
        piece_rds.append(r)

    hg.consolidate()
    for f in hg.memory.frames:
        f.activations = max(f.activations, 3)
    n_precip = hg.memory.precipitate()
    hg.enrich()
    gen_results.append(piece_rds)

    print('precip=%d Codex=%d Field(deposits=%d weight=%.1f bias_norm=%.4f)' % (
        n_precip, len(codex._table), field._count, field._total_weight,
        math.sqrt(sum(x*x for x in field.bias))))

# ── BiasField analysis ──
print('\n=== BiasField accumulation ===')
print('Total deposits: %d, total weight: %.1f' % (field._count, field._total_weight))
top_dims = sorted(range(D), key=lambda j: -abs(field.bias[j]))[:5]
dims_str = ' '.join('d%d(%.2f)' % (j, field.bias[j]) for j in top_dims)
print('Bias vector (top-5 dims): %s' % dims_str)
print('Bias norm: %.4f' % math.sqrt(sum(x*x for x in field.bias)))

# ── Readable Codex ──
print('\n=== Codex entries (readable) ===')
pitch_names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
ioi_bins = ['<1ms','1-2','2-5','5-10','10-20','20-50','50-100','0.1-0.2s','0.2-0.5','0.5-1','1-2','>2s']
entries = [(s, v, math.sqrt(sum(x*x for x in v))) for s, v in codex._table.items()]
entries.sort(key=lambda x: -x[2])
for sym, vec, nrm in entries[:12]:
    c_str = ' '.join('%s(%.2f)'%(pitch_names[j],vec[j]) for j in range(12) if abs(vec[j])>0.1)
    i_str = ' '.join('%s(%.2f)'%(ioi_bins[j],vec[j]) for j in range(12) if abs(vec[j])>0.1)
    print('  |norm=%.2f| chroma: %s  |  ioi: %s' % (nrm, c_str if c_str else '—', i_str if i_str else '—'))

# ── Cross-gen harm comparison ──
print('\n=== Cross-gen harm (does BiasField change processing?) ===')
print('%-8s %10s %10s %10s %10s' % ('Piece','Gen1','Gen5','Gen10','Delta'))
i=TEST_PIECE
ptype = 'Prelude' if i%2==0 else 'Fugue'
h1 = gen_results[0][0]['harm']
h5 = gen_results[4][0]['harm'] if len(gen_results)>4 else h1
h10 = gen_results[9][0]['harm'] if len(gen_results)>9 else h1
delta = h10 - h1
print('wtc_%02d   %10d %10d %10d  %+d' % (i, h1, h5, h10, delta))
