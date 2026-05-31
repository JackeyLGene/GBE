"""Shepard paradox — window size dependency.

Hypothesis: the paradox is visible ONLY when the cooccur_window
spans roughly 1-2 chroma circles (12-24 steps). Too small = no circle,
too large = circle buried in accumulated height drift.

Scan windows: 6, 12, 18, 24, 36, 48, 64 (default), 96
Measure: phase boundary flickering, τ_ac12, locked entries.
"""
import math, random, os, sys, io
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'code'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from geruon import Geruon, BiasField, GAMMA, TAU_0
from collections import Counter

WINDOWS = [6, 12, 18, 24, 36, 48, 64, 96]
N_OCTAVES = 24
CAP = 16

def generate_stream(n_octaves):
    stream = []
    for i in range(n_octaves * 12):
        ca = (i % 12) * 2 * math.pi / 12
        h = i / 12
        stream.append([
            math.sin(ca)*0.4+0.5, math.cos(ca)*0.4+0.5,
            h/n_octaves, (h//1)/n_octaves,
        ])
    return stream

stream = generate_stream(N_OCTAVES)
print(f'Stream: {len(stream)} steps ({N_OCTAVES} octaves)')
print()

def classify_phase(tau, dtaudt):
    if tau < 0.60: return 'EXPAND'
    if tau < 0.70: return 'RESTING'
    if tau < 0.74: return 'TENSING'
    if tau < 0.75: return 'CRITICAL'
    return 'LOCKED'

print(f'{"win":<6} {"τ_final":>8} {"ac12":>8} {"locked%":>8} {"flicker":>8} {"REST%":>8} {"CRIT%":>8} {"LOCK%":>8}')
print('-' * 70)

for win in WINDOWS:
    g = Geruon(vec_dim=4, memory_cap=CAP, kappa_tau=3.0, cooccur_window=win)
    bf = BiasField(vec_dim=4)

    tau_hist = []
    phase_hist = []
    dtaudt_hist = []

    for vec in stream:
        base = list(vec)
        if not bf.is_empty():
            base = bf.blend_into(base, weight=GAMMA)
        g.process_vec(base, 'shep')
        bf.deposit(list(g.arrow_output()), weight=0.2)
        tau_hist.append(g.tau)
        dtaudt_hist.append(g.dtaudt)
        phase_hist.append(classify_phase(g.tau, g.dtaudt))

    # Metrics
    tau_final = sum(tau_hist[-48:]) / 48

    # ac12
    tm = sum(tau_hist[-120:]) / 120
    num = sum((tau_hist[i]-tm)*(tau_hist[i-12]-tm) for i in range(12+len(tau_hist)-120, len(tau_hist)))
    den = sum((t-tm)**2 for t in tau_hist[-120:])
    ac12 = num / max(0.001, den)

    # Phase distribution
    pc = Counter(phase_hist)
    total = len(phase_hist)
    locked_pct = pc.get('LOCKED', 0) / total * 100
    rest_pct = pc.get('RESTING', 0) / total * 100
    crit_pct = pc.get('CRITICAL', 0) / total * 100

    # Flicker count: CRITICAL↔LOCKED transitions
    flickers = 0
    for i in range(1, len(phase_hist)):
        if (phase_hist[i-1] == 'CRITICAL' and phase_hist[i] == 'LOCKED') or \
           (phase_hist[i-1] == 'LOCKED' and phase_hist[i] == 'CRITICAL'):
            flickers += 1

    bar = '|' * min(20, flickers)
    print(f'{win:<6} {tau_final:8.4f} {ac12:+8.3f} {locked_pct:7.1f}% {flickers:8} {rest_pct:7.1f}% {crit_pct:7.1f}% {locked_pct:7.1f}% {bar}')

# ── Best window for paradox visibility ──
print()
print('Paradox requires: high ac12 + high flicker + moderate locked%')
print('(Pure chroma would lock; pure novelty would expand; paradox flickers)')
print('\nOK: Shepard window scan completed.')
