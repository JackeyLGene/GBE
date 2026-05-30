"""Phase 2: Codex as evolutionary engine — efficiency, not survival.

Mixed Codex (true + wrong entries), run on true piece.
Measure: correct entries gain weight, wrong entries are eliminated.
"""
import pickle, math, random, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import geruon, we_core
from geruon import BiasField, Codex

random.seed(42)
D=12; CAP=12; GI=4; WINDOW=8; SENS=5.0; N_GENS=10

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

# ── Build initial mixed Codex ──
# Use existing true_codex + wrong_codex, merge into one
true_cx = Codex.load('data/wtc_phase2/codex_true_cap12.json')
wrong_cx = Codex.load('data/wtc_phase2/codex_wrong_cap12.json')

# Create mixed Codex: tag each entry with source
mixed = Codex.empty(name='mixed', vec_dim=D)
for sym, vec in true_cx._table.items():
    w = true_cx._entry_weight.get(sym, 1.0)
    mixed._table['TRUE_'+sym] = tuple(vec)
    mixed._entry_weight['TRUE_'+sym] = w
for sym, vec in wrong_cx._table.items():
    w = wrong_cx._entry_weight.get(sym, 1.0)
    mixed._table['WRONG_'+sym] = tuple(vec)
    mixed._entry_weight['WRONG_'+sym] = w

print('Initial Codex: %d true + %d wrong = %d total' % (
    len(true_cx), len(wrong_cx), len(mixed)))

# Source tracking
source_map = {}
for sym in mixed._table:
    source_map[sym] = 'TRUE' if 'TRUE' in sym else 'WRONG'

# ── Run on wtc_00 for N_GENS ──
with open('data/wtc_pieces/wtc_00.pkl','rb') as f:
    events,_ = pickle.load(f)
cv, iv = encode(events)

weight_history = {'TRUE': [], 'WRONG': []}  # gen → total weight

codex = mixed
field = BiasField(vec_dim=D)

for gen_idx in range(N_GENS):
    wc = we_core.We(n_selves=1,vec_dim=D,cap=CAP,seed=42,cavity_quantum=False,collective_quantum=False,stress_sensitivity=SENS,enable_active_codex_query=False,inherited_alpha=0.05)
    if gen_idx > 0:
        wc._prev_codex = codex
    wc.init_generation(); cs = wc.selves[0]
    wi = we_core.We(n_selves=1,vec_dim=D,cap=CAP,seed=99,cavity_quantum=False,collective_quantum=False)
    wi.init_generation(); is_ = wi.selves[0]
    field2 = BiasField(vec_dim=D)
    for g in cs+is_: g.bias_field = field2
    hg = geruon.Geruon(vec_dim=D,memory_cap=CAP//2,kappa_tau=10)
    hg.codex = codex; hg.bias_field = field

    dtaus=[]; harm=0; abstractions=0
    for idx in range(len(cv)):
        for g in cs: g.process_vec(nrm(cv[idx]),'C')
        for g in is_: g.process_vec(nrm(iv[idx]),'I')
        dtaus.append(cs[0].dtaudt)
        if idx>0 and idx%(GI*GI)==0:
            for src in [cs,is_]:
                for g_src in src:
                    a=list(g_src.arrow_output()); field.deposit(a,weight=0.5)
                    for g_dst in (is_ if src==cs else cs):
                        nb=len(g_dst.memory.frames); g_dst.process_vec(a,'X')
                        if len(g_dst.memory.frames)>nb: pass
            hg.process_vec(nrm(list(cs[0].arrow_output())),'H')
            if len(dtaus)>=50:
                sd=sorted(dtaus[-500:]) if len(dtaus)>=500 else sorted(dtaus)
                p90=sd[int(len(sd)*0.9)]; thresh=max(p90/SENS,0.0001)
                if cs[0].dtaudt>thresh and cs[0].tau>0.55:
                    ca=list(cs[0].arrow_output()); ia=list(is_[0].arrow_output())
                    outer=[]
                    for a in range(D):
                        for b in range(D): outer.append((abs(ca[a]*ia[b]),a,b))
                    outer.sort(key=lambda x:-x[0])
                    joint=[0.0]*D
                    for jj,(val,a,b) in enumerate(outer[:6]):
                        joint[min(jj*2,D-2)]=ca[a]; joint[min(jj*2+1,D-1)]=ia[b]
                    ns=math.sqrt(sum(x*x for x in joint))
                    if ns>0: joint=[x/ns for x in joint]
                    if len(codex)<200: codex.add('NEW_g%d_%d'%(gen_idx,abstractions),tuple(joint))
                    abstractions+=1
    hg.enrich()

    # Track weights by source
    tw = 0.0; ww = 0.0
    for sym in codex._table:
        w = codex._entry_weight.get(sym, 1.0)
        if sym in source_map:
            if source_map[sym] == 'TRUE': tw += w
            else: ww += w
        else:
            # New entry — classify by proximity to true/wrong
            source_map[sym] = 'NEW'
    weight_history['TRUE'].append(tw)
    weight_history['WRONG'].append(ww)

    true_w = sum(codex._entry_weight.get(s,1.0) for s in codex._table if source_map.get(s)=='TRUE')
    wrong_w = sum(codex._entry_weight.get(s,1.0) for s in codex._table if source_map.get(s)=='WRONG')
    new_w = sum(codex._entry_weight.get(s,1.0) for s in codex._table if source_map.get(s)=='NEW')
    print('Gen%d: harm=%d abs=%d codex=%d TRUE_w=%.0f WRONG_w=%.0f NEW_w=%.0f' % (
        gen_idx+1, harm, abstractions, len(codex._table), true_w, wrong_w, new_w))

# ── Final analysis ──
print()
print('=== Weight trajectory ===')
print('%-6s %10s %10s %10s' % ('Gen','TRUE_w','WRONG_w','Ratio'))
for g in range(N_GENS):
    tw = weight_history['TRUE'][g]
    ww = weight_history['WRONG'][g]
    ratio = tw/max(1,ww)
    marker = ' ← SELECTION' if g>0 and ratio > weight_history['TRUE'][0]/max(1,weight_history['WRONG'][0])*1.1 else ''
    print('%-6d %10.0f %10.0f %9.2f%s' % (g+1, tw, ww, ratio, marker))
