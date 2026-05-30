"""UN Vote-Event Prediction Pipeline — 投票事件粒度，帧经济真实竞争.

每个投票 = (国家, 决议, yes/no/abstain) = 一个认知决策事件.
1993-2019: 投票 + FRED 重叠期, 约 40 万事件.
"""

import csv, math, random, collections, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from geruon import Geruon
random.seed(42)

# ── 1. Load ──

# Resolution metadata: rcid -> year
res_meta = {}
with open('data/un_votes/roll_calls.csv','r',encoding='utf-8') as f:
    for row in csv.DictReader(f):
        rcid = int(row['rcid'])
        d = row.get('date','')
        yr = int(d[:4]) if len(d)>=4 and d[:4].isdigit() else 0
        res_meta[rcid] = yr

# Vote events: (rcid, country_code, vote, year)
events = []
with open('data/un_votes/unvotes.csv','r',encoding='utf-8') as f:
    for row in csv.DictReader(f):
        rcid = int(row['rcid'])
        yr = res_meta.get(rcid, 0)
        if yr < 1993 or yr > 2019: continue
        events.append((rcid, yr, row['country_code'], row['vote']))

# Sort by year, then rcid
events.sort(key=lambda x: (x[1], x[0]))
print('Events: %d votes (%d-%d)' % (len(events), events[0][1], events[-1][1]))

# FRED
fred = {}
with open('data/econ_data/fred_annual.csv','r',encoding='utf-8') as f:
    for row in csv.DictReader(f):
        yr = int(list(row.values())[0])
        vs = [float(v) for v in list(row.values())[1:] if v]
        if vs: fred[yr] = vs

# ── 2. Group votes by resolution ──

# Build resolution-level vote distributions
res_votes = collections.defaultdict(lambda: {'y':0, 'yes':0, 'no':0, 'abstain':0, 'p5':{}, 'total':0})
for rcid, yr, cc, vote in events:
    rv = res_votes[rcid]
    rv['y'] = yr
    rv['total'] += 1
    rv[vote] = rv.get(vote, 0) + 1
    if cc in ('USA','GBR','FRA','RUS','CHN'):
        rv['p5'][cc] = vote

res_list = sorted(res_votes.items(), key=lambda x: (x[1]['y'], x[0]))
print('Resolutions: %d (%d-%d)' % (len(res_list), res_list[0][1]['y'], res_list[-1][1]['y']))

# ── 3. Resolution encoding ──

D = 16

def encode_res(rv):
    """One resolution -> D-dim vector: vote distribution + P5 + FRED"""
    t = rv['total']
    yes = rv.get('yes',0)/t
    no = rv.get('no',0)/t
    abst = rv.get('abstain',0)/t
    # Entropy
    ent = 0.0
    for p in [yes,no,abst]:
        if p>0: ent -= p*math.log(p)
    ent /= math.log(3)

    # P5 votes
    p5_map = {'USA':0,'GBR':1,'FRA':2,'RUS':3,'CHN':4}
    p5_vec = [0.0]*5
    for cc, idx in p5_map.items():
        v = rv['p5'].get(cc, 'absent')
        p5_vec[idx] = 1.0 if v=='yes' else (-1.0 if v=='no' else 0.0)
    p5_agree = 1.0 if len(set(p5_vec))==1 else 0.0

    yr = rv['y']
    v = [yes, no, abst, ent, p5_agree,
         p5_vec[0],p5_vec[1],p5_vec[2],p5_vec[3],p5_vec[4],
         float(t)/200.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    # FRED modulation
    if yr in fred:
        fv = fred[yr]
        v[11] = fv[3]/10.0; v[12] = fv[5]/10.0; v[13] = fv[0]/10000.0
    return v

def nrm(v):
    s = math.sqrt(sum(x*x for x in v))
    return [x/s for x in v] if s>0 else v[:]

# ── 4. κ sweep (resolution granularity, frame economy saturates) ──

CAP = 12  # low cap to force frame competition with ~4500 events

print('\n=== Kappa sweep (resolution granularity, cap=%d, %d events) ===' % (CAP, len(res_list)))
print('%-8s %10s %10s %10s %10s %10s %10s' % ('Kappa','MeanDisp','StdDisp','MaxDisp','F_final','Tau_final','Phase'))

best_k = None; best_score = -1

for kv in [0.5, 1, 3, 5, 10]:
    g = Geruon(vec_dim=D, memory_cap=CAP, kappa_tau=kv)
    prev = [0.0]*D; disps = []
    for rcid, rv in res_list:
        g.process_vec(nrm(encode_res(rv)), 'R%d'%rcid)
        cur = list(g.arrow_output())
        disps.append(math.sqrt(sum((x-y)**2 for x,y in zip(prev,cur))))
        prev = cur

    mean_d = sum(disps)/len(disps)
    std_d = math.sqrt(sum((x-mean_d)**2 for x in disps)/len(disps))
    fw = [f.weight for f in g.memory.frames]; nf = len(fw)
    if nf > 1:
        tw=sum(fw); probs=[x/tw for x in fw]
        F = 1.0 - sum(-p*math.log(p) for p in probs if p>0)/math.log(nf)
    else: F = 0
    # Score: F (structure) + tau health (near 0.67)
    score = F*10.0 + (1.0 - abs(g.tau - 0.67))

    print('%-8s %10.4f %10.4f %10.4f %10.4f %10.4f %10s' % (
        str(kv), mean_d, std_d, max(disps), F, g.tau, str(g.phase)[:15]))

    if score > best_score:
        best_score = score; best_k = kv

print('\nCalibrated kappa = %.1f (score=%.4f)' % (best_k, best_score))

# ── 5. Full run with calibrated κ ──

print('\n=== Full run: kappa=%.1f ===' % best_k)
g = Geruon(vec_dim=D, memory_cap=CAP, kappa_tau=best_k)
prev = [0.0]*D
res_readings = []

for rcid, rv in res_list:
    g.process_vec(nrm(encode_res(rv)), 'R%d'%rcid)
    cur = list(g.arrow_output())
    d = math.sqrt(sum((x-y)**2 for x,y in zip(prev,cur)))
    res_readings.append({
        'y': rv['y'], 'rcid': rcid, 'disp': d, 'tau': g.tau,
        'phase': str(g.phase), 'yes_pct': rv.get('yes',0)/max(1,rv['total'])
    })
    prev = cur

# ── 6. Annual aggregation ──

years = sorted(set(r['y'] for r in res_readings))
print('\n=== Annual readings ===')
print('%-6s %8s %8s %8s %8s %10s %10s' % ('Year','NRes','MeanDisp','MaxDisp','TauEnd','PhaseEnd','Yes%Mean'))

annual = []
for yr in years:
    evts = [r for r in res_readings if r['y']==yr]
    n = len(evts); ds = [r['disp'] for r in evts]
    yes_m = sum(r['yes_pct'] for r in evts)/n
    a = {'y':yr, 'n':n, 'mean_d':sum(ds)/n, 'max_d':max(ds),
         'tau':evts[-1]['tau'], 'phase':evts[-1]['phase'][:10], 'yes':yes_m}
    annual.append(a)
    print('%-6d %8d %8.4f %8.4f %8.4f %10s %10.4f' % (
        yr, n, a['mean_d'], a['max_d'], a['tau'], a['phase'], yes_m))

# ── 7. Precursor detection ──

print('\n=== Precursor scan (annual) ===')
for i, a in enumerate(annual):
    if i < 3: continue
    a1 = annual[i-1]; a2 = annual[i-2]; a3 = annual[i-3]
    d3 = '%.0f->%.0f->%.0f' % (1000*a3['mean_d'], 1000*a2['mean_d'], 1000*a1['mean_d'])

    spike = a['mean_d'] > 2.0 * a1['mean_d'] if a1['mean_d']>0 else False
    calm = a1['mean_d'] < 0.008
    rising = a3['mean_d'] < a2['mean_d'] < a1['mean_d'] < a['mean_d']

    tag = ''
    if spike and calm: tag = '*** SPIKE+CALM ***'
    elif spike: tag = '** SPIKE **'
    elif rising: tag = '* DISP_RISING *'
    print('%-6d %10.4f %10.4f %10.4f %s %s' % (a['y'], a['mean_d'], a['max_d'], a['tau'], d3, tag))

# ── 8. Historical checkpoint ──

print('\n=== Key years ===')
for yr, label in [(2001,'9/11'),(2003,'Iraq'),(2008,'FC'),(2014,'Crimea'),(2016,'Trump'),(2019,'preCOVID')]:
    evts = [r for r in res_readings if r['y']==yr]
    if evts:
        ds = [r['disp'] for r in evts]
        print('  %d %s: mean_d=%.4f max_d=%.4f tau=%.4f n=%d' % (
            yr, label, sum(ds)/len(ds), max(ds), evts[-1]['tau'], len(evts)))
