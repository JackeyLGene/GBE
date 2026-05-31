"""NASDAQ OHLCV action encoding — volume + direction + conviction.

Dim0: log(volume) — how much action happened
Dim1: (close-open)/(high-low) — who won (buyers=+1, sellers=-1)
Dim2: volume * |close-open|/(high-low) / max_vol — committed action ($ behind the move)
"""

import csv, math, sys, io, collections, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'code'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from geruon import Geruon

rows = []
with open(os.path.join(ROOT, 'data', 'econ_data', 'nasdaq_ohlcv.csv'),'r',encoding='utf-8') as f:
    for r in csv.DictReader(f):
        rows.append((r['date'], float(r['open']), float(r['high']),
                      float(r['low']), float(r['close']), float(r['volume'])))
print('NASDAQ OHLCV: %d days (%s - %s)' % (len(rows), rows[0][0], rows[-1][0]))

# ── Build action vectors ──
D = 3
daily = []
max_committed = 0
# First pass: compute max committed volume for normalization
for date, o, h, l, c, v in rows:
    spread = h - l
    if spread > 0:
        committed = v * abs(c - o) / spread
    else:
        committed = 0
    if committed > max_committed: max_committed = committed

for date, o, h, l, c, v in rows:
    spread = h - l
    if spread > 1e-6:
        direction = (c - o) / spread   # [-1, 1], who won
        committed = v * abs(c - o) / spread / max(1, max_committed)
    else:
        direction = 0.0
        committed = 0.0
    log_vol = math.log(v + 1)
    daily.append((date, [log_vol, direction, committed]))

# Normalize
av = {d: [daily[j][1][d] for j in range(len(daily))] for d in range(D)}
lo = {d: min(av[d]) for d in range(D)}
hi = {d: max(av[d]) for d in range(D)}
for d in range(D):
    if hi[d]-lo[d] < 1e-10: hi[d] = lo[d] + 1.0

def encode(vec):
    return [(vec[d]-lo[d])/(hi[d]-lo[d]) for d in range(D)]

def nrm(v):
    s = math.sqrt(sum(x*x for x in v))
    return [x/s for x in v] if s>0 else v[:]

print('D=%d (log_vol, direction, committed_vol)' % D)
print('Direction range: [%.2f, %.2f]' % (min(av[1]), max(av[1])))
print('LogVol range: [%.1f, %.1f]' % (min(av[0]), max(av[0])))

# ── κ sweep ──
CAP = 16
print('\n=== Kappa sweep (NASDAQ action, cap=%d, %d events) ===' % (CAP, len(daily)))
print('%-8s %10s %10s %10s %10s %10s' % ('Kappa','MeanDisp','StdDisp','MaxDisp','Tau','Phase'))

best_k = 1; best_score = -1
for kv in [0.5, 1, 3, 5, 10]:
    g = Geruon(vec_dim=D, memory_cap=CAP, kappa_tau=kv)
    prev = [0.0]*D; disps = []
    for date, vec in daily:
        g.process_vec(nrm(encode(vec)), 'D')
        cur = list(g.arrow_output())
        disps.append(math.sqrt(sum((x-y)**2 for x,y in zip(prev,cur))))
        prev = cur
    md = sum(disps)/len(disps); sd = math.sqrt(sum((x-md)**2 for x in disps)/len(disps))
    mx = max(disps)
    score = sd*10.0 + (1.0-abs(g.tau-0.67))
    print('%-8s %10.4f %10.4f %10.4f %10.4f %10s' % (str(kv),md,sd,mx,g.tau,str(g.phase)[:15]))
    if score>best_score: best_score=score; best_k=kv
print('Best kappa = %.1f' % best_k)

# ── Full run ──
g = Geruon(vec_dim=D, memory_cap=CAP, kappa_tau=best_k)
prev = [0.0]*D; daily_rds = []
for date, vec in daily:
    g.process_vec(nrm(encode(vec)), 'D')
    cur = list(g.arrow_output())
    d = math.sqrt(sum((x-y)**2 for x,y in zip(prev,cur)))
    parts = date.split('-'); ym = parts[0]+'-'+parts[1] if len(parts)>=2 else date
    daily_rds.append({'date':date,'ym':ym,'disp':d,'tau':g.tau,'phase':str(g.phase)})
    prev = cur

for i,r in enumerate(daily_rds):
    r['dt'] = abs(r['tau']-daily_rds[i-1]['tau']) if i>0 else 0

# ── Monthly ──
months = sorted(set(r['ym'] for r in daily_rds))
monthly = []
for ym in months:
    mds=[r for r in daily_rds if r['ym']==ym]; n=len(mds); ds=[r['disp'] for r in mds]
    monthly.append({'ym':ym,'n':n,'mean_d':sum(ds)/n,'max_d':max(ds),
                    'tau':mds[-1]['tau'],'dt':mds[-1]['dt'],'phase':mds[-1]['phase'][:10]})

# ── Precursor scan ──
dv=[m['mean_d'] for m in monthly[3:]]
dtv=[m['dt'] for m in monthly[3:]]
TF=sorted(dtv)[len(dtv)//2]*0.01
DC=sorted(dv)[len(dv)//4]*0.7
SR=3.0

print('\n=== Monthly precursor scan (NASDAQ OHLCV action) ===')
print('TAU_FREEZE=%.6f DISP_CALM=%.4f SPIKE=%.1fx'%(TF,DC,SR))
print('%-8s %8s %10s %8s %8s %s'%('Month','MeanDisp','dtau','MaxDisp','Tau','Signal'))

warnings=[]
for i in range(4,len(monthly)):
    m=monthly[i];m1=monthly[i-1];m2=monthly[i-2];m3=monthly[i-3]
    tf=m1['dt']<TF; dc=m1['mean_d']<DC
    ds=m['mean_d']>SR*m1['mean_d'] if m1['mean_d']>0.001 else False
    ff=m3['mean_d']<m2['mean_d']<m1['mean_d']<m['mean_d']
    tag=''
    if tf and dc and i>=5:
        fc=sum(1 for j in range(1,5) if monthly[i-j]['dt']<TF)
        if fc>=2: tag='*** FREEZE(x%d)+CALM ***'%fc; warnings.append((m['ym'],tag))
    if not tag and ds and dc: tag='*** SPIKE+CALM(%.1fx) ***'%(m['mean_d']/m1['mean_d']); warnings.append((m['ym'],tag))
    if not tag and ff: tag='* DISP_RISING_4M *'
    if not tag and ds: tag='** SPIKE **'
    if not tag and tf: tag='TAU_FROZEN'
    if tag: print('%-8s %8.4f %10.6f %8.4f %8.4f %s'%(m['ym'],m['mean_d'],m['dt'],m['max_d'],m['tau'],tag))

# ── Validation ──
def mtm(ym): p=ym.split('-'); return int(p[0])*12+int(p[1])
CAL=[('2001-09','9/11'),('2008-09','Lehman'),('2014-03','Crimea'),('2016-11','Trump'),('2020-03','COVID'),('2022-02','Ukraine')]
print('\n=== Historical validation ===')
hits=0
for em,name in CAL:
    pre=[(y,t) for y,t in warnings if y<em and mtm(em)-mtm(y)<=6]
    if pre:
        hits+=1
        print('  %s: HIT — %s'%(name,', '.join('%s[%s]'%(y,t.replace('*','')) for y,t in pre)))
    else:
        same=[(y,t) for y,t in warnings if y==em]
        if same: print('  %s: same-month [%s]'%(name,same[0][1]))
        else: print('  %s: MISS'%name)
print('Precursor hit rate: %d/%d'%(hits,len(CAL)))

# ── 2024-2025 ──
print('\n=== 2024-2025 monthly ===')
for m in monthly:
    if m['ym']>='2024-01':
        mk=' *** HIGH ***'if m['mean_d']>0.10 else(' * ELEV *'if m['mean_d']>0.06 else'')
        print('  %s: mean_d=%.4f max_d=%.4f tau=%.4f%s'%(m['ym'],m['mean_d'],m['max_d'],m['tau'],mk))

print('\n=== Key event months ===')
for em,label in CAL:
    matched=[m for m in monthly if m['ym']==em]
    if matched:
        m=matched[0]
        print('  %s %s: mean_d=%.4f max_d=%.4f tau=%.4f'%(em,label,m['mean_d'],m['max_d'],m['tau']))

print('\n=== Top displacement months ===')
for m in sorted(monthly,key=lambda x:-x['mean_d'])[:10]:
    print('  %s: mean_d=%.4f max_d=%.4f'%(m['ym'],m['mean_d'],m['max_d']))
