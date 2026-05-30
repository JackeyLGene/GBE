"""
We: encapsulation of the We architecture — 3-Self 3-cavity field.
"""
import math, random as _rnd
from geruon import Geruon, Codex, BiasField, GAMMA, TAU_0, _hash_str, PHASE_RESTING_CEIL

class We:
    """N Selfs, each a 3-cavity Geruon. Shared BiasField, per-Self Codex.
    Cross-Self harm arrows → Self Codex + collective Codex (direct accumulation).
    Collective Geruon: pattern detector — L3 bridges from boundary events.
    """

    def __init__(self, n_selves=3, k_lenses=None, vec_dim=16,  # aligned with Geruon default
                 cap=24, win=None, gi=4, seed=42, kappa_tau_harm=10.0,  # circ-optimal κ_τ — detects self-referential structure
                 cavity_quantum=False, collective_quantum=False,
                 stress_sensitivity=1.0,
                 enable_active_codex_query=False,  # Phase 2: off by default
                 inherited_alpha=0.0):  # Codex→BiasField deposit weight at gen birth
        if win is None:
            win = cap * gi  # M16: window = cap × GI, not hardcoded 100
        self.n_selves = n_selves
        self.k_lenses = k_lenses or [0.5, 10.0, 100.0]
        self.vec_dim = vec_dim
        self.cap = cap
        self.win = win
        self.gi = gi
        self.seed = seed
        self.kappa_tau_harm = kappa_tau_harm
        self.cavity_quantum = cavity_quantum
        self.collective_quantum = collective_quantum
        self.stress_sensitivity = stress_sensitivity       # per-Self crisis threshold
        self.enable_active_codex_query = enable_active_codex_query  # Phase 2 gate
        self.inherited_alpha = inherited_alpha             # Codex→BiasField deposit weight

        self.shared_bias = BiasField(vec_dim=vec_dim)
        self.selves = []
        self.harm_codexes = []  # per-Self Codex — what this Self's frames were marked as harm
        self.collective = None
        self.collective_codex = None

    def _make_self(self, seed_offset):
        """Create one 3-cavity Self. Born empty — no codex. Codex is queried at boundary events only."""
        lenses = []
        for i, k in enumerate(self.k_lenses):
            g = Geruon(vec_dim=self.vec_dim, memory_cap=self.cap,
                       cooccur_window=self.win, codex=None,
                       bias_field=None, bias_weight=0.0, kappa_tau=k)
            g.memory.quantum_mode = self.cavity_quantum
            g.memory._qrand = _rnd.Random(self.seed + seed_offset*10 + i)
            g.memory.cooccur_thresh = 0.20  # 1/GI−γ=0.20 — one γ-unit more sensitive than solo Geruon (0.25)
            lenses.append(g)
        return lenses

    def init_generation(self):
        """Initialize all Selfs and collective for a new generation.
        Self Codex ← previous generation's collective_codex (discrete lookup)."""
        self.shared_bias = BiasField(vec_dim=self.vec_dim)
        # Per-Self Codex persists across gens — accumulates this Self's harm-marked frames
        if not hasattr(self, '_prev_harm_codexes') or self._prev_harm_codexes is None:
            self.harm_codexes = [Codex.empty(name=f"harm_s{si}", vec_dim=self.vec_dim)
                                 for si in range(self.n_selves)]
        else:
            self.harm_codexes = self._prev_harm_codexes
        # ── Self Codex transmission: inherited collective_codex → cavity codex ──
        # Cavities receive the inherited vocabulary at birth.
        # Query mechanism is the same as geruon: nearest + blend_in.
        inherited_codex = None
        if hasattr(self, '_prev_codex') and self._prev_codex and self._prev_codex._table:
            inherited_codex = self._prev_codex
        self.selves = [self._make_self(si) for si in range(self.n_selves)]
        if inherited_codex is not None and self.enable_active_codex_query:
            for lenses in self.selves:
                for g in lenses:
                    g.codex = inherited_codex  # Self carries inherited vocabulary
        # collective_codex: We-level inter-gen persistence. Carried forward from previous gen.
        inherited = self._prev_codex if hasattr(self, '_prev_codex') and self._prev_codex else None
        self.collective_codex = Codex.empty(name="we", vec_dim=self.vec_dim)
        if inherited is not None and inherited._table:
            for sym, vec in inherited._table.items():
                self.collective_codex._table[sym] = vec
            # carry forward weights too
            if hasattr(inherited, '_entry_weight'):
                self.collective_codex._entry_weight = dict(inherited._entry_weight)
        # ── Phase 2: inherited Codex → BiasField deposit (generation birth) ──
        # Externalization does not act. It biases becoming.
        if self.inherited_alpha > 0 and self.collective_codex._table:
            for sym, vec in self.collective_codex._table.items():
                w = self.collective_codex._entry_weight.get(sym, 1.0)
                self.shared_bias.deposit(vec, weight=self.inherited_alpha * w)
        # Collective Geruon — pattern detector. Receives boundary events as heartbeat.
        self.collective = Geruon(vec_dim=self.vec_dim, memory_cap=self.cap*3,
                                 cooccur_window=self.win, codex=None,
                                 bias_field=None, bias_weight=0.0,
                                 kappa_tau=self.kappa_tau_harm)
        self.collective.memory.quantum_mode = self.collective_quantum
        self.collective.memory._qrand = _rnd.Random(self.seed + 999)
        self.collective.memory.cooccur_thresh = 0.15  # 1/GI−2γ=0.15 — most sensitive; collective detects weak cross-Self patterns

        self.harm_gids = [set() for _ in range(self.n_selves)]
        self._harm_step_log = {}  # gid → [step, ...] — when each gid was harm-marked
        self._harm_tracks = []  # [{gid, src_self, tau, phase, vec}, ...] — for collective heartbeat
        self._boundary_events = []  # [{step, self, lens, tau, phase, dtaudt}, ...]
        self.harm_routed = 0
        self.harm_zero = 0

    def _exchange_internal(self, lenses):
        """Cavity-internal arrow exchange at GI."""
        arrows = [g.arrow_output() for g in lenses]
        for i, g in enumerate(lenses):
            for j, a in enumerate(arrows):
                if i != j:
                    g.process_vec(list(a), f'L{i}_from_L{j}')

    def process_step(self, vec, sig, step, g_vec=None, g_gap=0):
        """Process one input event through all Selfs + exchange."""
        base = list(vec)
        if not self.shared_bias.is_empty():
            base = self.shared_bias.blend_into(base, weight=GAMMA)
        for lenses in self.selves:
            for g in lenses:
                g.process_vec(list(base), sig)

        if g_vec is not None and g_gap > 0 and step > 0 and step % g_gap == 0:
            for lenses in self.selves:
                for g in lenses:
                    g.process_vec(list(g_vec), 'G_sentence')

        if step % self.gi == 0:
            for lenses in self.selves:
                self._exchange_internal(lenses)

        # Cross-Self harm arrows — frame-delta capture
        if step % (self.gi * self.gi) == 0:  # GI² — cross-Self communication interval
            for si, lenses_src in enumerate(self.selves):
                for sj, lenses_dst in enumerate(self.selves):
                    if si == sj:
                        continue
                    n_before = {id(g): len(g.memory.frames) for g in lenses_dst}
                    for li, g_src in enumerate(lenses_src):
                        arrow = g_src.arrow_output()
                        self.shared_bias.deposit(arrow, weight=0.5)
                        for g in lenses_dst:
                            g.process_vec(list(arrow), f'H_S{si}_L{li}')
                    for g in lenses_dst:
                        nb = n_before.get(id(g), 0)
                        for f in g.memory.frames[nb:]:
                            ss = getattr(f, 'struct_sig', None)
                            if ss:
                                self.harm_gids[sj].add(ss.gid)
                                s_log = self._harm_step_log.setdefault(ss.gid, [])
                                if len(s_log) < 2 * self.gi + 2:  # 2×GI+2=10 — max harm step records per gid
                                    s_log.append(step)

        # ── Self-level Codex query (dynamic threshold) ──
        # Geruon cliff_gate uses fixed DTAU_STABLE (derived from τ₀).
        # Self uses its OWN RECENT HISTORY to decide when to query Codex.
        # This is adaptive: "am I more stressed than I've been recently?"
        if step % (self.gi * self.gi) == 0:  # GI² — cross-Self communication interval
            for si, lenses in enumerate(self.selves):
                for li, g in enumerate(lenses):
                    # ── Self-level dynamic stress detection ──
                    # Each Self tracks its own dτ/dt history continuously.
                    # Threshold = p90 of full history ÷ sensitivity.
                    # Crisp detection: dτ/dt > threshold AND τ > RESTING.
                    MIN_WINDOW = 50
                    # stress_sensitivity: 1.0=normal, >1=more sensitive
                    DIVISOR = self.stress_sensitivity

                    if not hasattr(g, '_dtau_history'):
                        g._dtau_history = []

                    g._dtau_history.append(g.dtaudt)
                    if len(g._dtau_history) > 500:
                        g._dtau_history.pop(0)

                    geruon_cliff = g.memory.cliff_gate
                    current_dt = g.dtaudt

                    # Self stress: current dτ/dt exceeds own historical p90 / sensitivity
                    self_stressed = False
                    if len(g._dtau_history) >= MIN_WINDOW:
                        sd = sorted(g._dtau_history)
                        p90 = sd[int(len(sd) * 0.9)]
                        threshold = max(p90 / max(DIVISOR, 0.1), 0.0001)
                        self_stressed = (current_dt > threshold and
                                        g.tau > PHASE_RESTING_CEIL)

                    if geruon_cliff < 0.5 or self_stressed:
                        etype = 'self_stress' if (self_stressed and geruon_cliff >= 0.5) else 'cliff_shut'
                        self._boundary_events.append({
                            'step': step, 'self': si, 'lens': li,
                            'tau': round(g.tau, 4), 'phase': g.phase.value,
                            'dtaudt': round(current_dt, 6), 'type': etype,
                        })
                        # ── Query + Abstract: joint-signature Codex formation ──
                        if self.collective_codex is not None:
                            arrow = list(g.arrow_output())

                            # ── Abstract formation: joint signature with other Selfs ──
                            # When stressed, this Self marks what the OTHER Selfs see.
                            # The joint [my_arrow | their_arrow] is a concept neither can form alone.
                            if len(self.selves) >= 2:
                                for sj in range(len(self.selves)):
                                    if sj == si: continue
                                    # Get the OTHER Self's arrow (use slowest cavity = most stable view)
                                    other_g = self.selves[sj][-1]  # κ=100 cavity
                                    other_arrow = list(other_g.arrow_output())

                                    # Build joint signature: outer product → top entries
                                    # Abstraction = coupling between streams, not their contents.
                                    # Joint[i,j] = arrow[i] * other_arrow[j] = co-activation.
                                    # Top outer-product entries → joint vector (interleaved index pairs).
                                    outer_flat = []  # (value, i, j)
                                    for a in range(self.vec_dim):
                                        for b in range(self.vec_dim):
                                            outer_flat.append((abs(arrow[a] * other_arrow[b]), a, b))
                                    outer_flat.sort(key=lambda x: -x[0])
                                    k = max(2, self.vec_dim // 2)  # pairs to encode
                                    joint = [0.0] * self.vec_dim
                                    for idx, (val, a, b) in enumerate(outer_flat[:k]):
                                        # Encode (i, j) pair into position idx*2 and idx*2+1
                                        pos_a = min(idx * 2, self.vec_dim - 2)
                                        pos_b = min(idx * 2 + 1, self.vec_dim - 1)
                                        joint[pos_a] = arrow[a]
                                        joint[pos_b] = other_arrow[b]
                                    ns = math.sqrt(sum(x*x for x in joint))
                                    if ns > 0: joint = [x/ns for x in joint]

                                    # Write abstract concept to Codex
                                    gid_str = _hash_str('ABS_s%d_s%d' % (si, sj))[-6:]
                                    sym = 'ABS_s%d_%s' % (si, gid_str)
                                    if len(self.collective_codex) < 200:  # prevent unbounded growth
                                        self.collective_codex.add(sym, tuple(joint),
                                                                  source='abstraction_s%d_s%d' % (si, sj))

                            # ── Active Codex query (Phase 1 scaffold, gated for Phase 2) ──
                            if self.enable_active_codex_query and len(self.collective_codex) > 0:
                                best_sym, best_vec, best_dist = self.collective_codex.nearest(arrow)
                                if best_vec is not None and best_dist < 1.0:
                                    g.process_vec(list(best_vec), 'CODEX_%s' % str(best_sym)[:20])

    def finalize(self):
        """Collect harm-marked frames → Self Codex + collective tracks.
        Weighted blending by occurrence count. L2-L6 routed to collective for translation layer."""
        for si, lenses in enumerate(self.selves):
            for g in lenses:
                for f in g.memory.frames:
                    ss = getattr(f, 'struct_sig', None)
                    if not ss or ss.gid not in self.harm_gids[si]:
                        continue
                    n = math.sqrt(sum(v*v for v in f.vec))
                    if n <= 0.01:
                        self.harm_zero += 1
                        continue
                    self.harm_routed += 1
                    vec_norm = tuple(v/n for v in f.vec)
                    sym = f"W_{ss.gid % 1000000}"
                    # Accumulate in collective_codex — slow cavities weight higher
                    existing = self.collective_codex.lookup(sym)
                    if existing is not None:
                        old_w = self.collective_codex._entry_weight.get(sym, 1.0)
                        new_w = old_w + 1.0
                        blended = tuple(existing[j] * (old_w/new_w) + vec_norm[j] * (1.0/new_w)
                                       for j in range(min(len(existing), len(vec_norm))))
                        self.collective_codex._table[sym] = blended
                        self.collective_codex._entry_weight[sym] = new_w
                    else:
                        self.collective_codex._table[sym] = vec_norm
                        if not hasattr(self.collective_codex, '_entry_weight'):
                            self.collective_codex._entry_weight = {}
                        self.collective_codex._entry_weight[sym] = 1.0
                    # Write to Self Codex
                    self.harm_codexes[si].add(sym, vec_norm)
                    # Track for collective heartbeat and L3
                    steps = self._harm_step_log.get(ss.gid, [])
                    self._harm_tracks.append({
                        'gid': ss.gid,
                        'src_self': si,
                        'tau': getattr(f, 'tau', TAU_0),
                        'phase': getattr(g, 'phase', None),
                        'vec': vec_norm,
                        'steps': steps,
                    })

        # ── Route Self cavities' L2-L6 frames to collective (translation layer raw material) ──
        # Weighted blending — same as harm entries. Preserves occurrence count and gradual drift.
        for si, lenses in enumerate(self.selves):
            for g in lenses:
                for f in g.memory.frames:
                    if f.layer not in ('L2', 'L3', 'L4', 'L6'):
                        continue
                    n = math.sqrt(sum(v*v for v in f.vec))
                    if n <= 0.01:
                        continue
                    vec_norm = tuple(v/n for v in f.vec)
                    ss = getattr(f, 'struct_sig', None)
                    gid_tag = ss.gid % 1000000 if ss else 0
                    sym = f"{f.layer}_{gid_tag}"
                    existing = self.collective_codex.lookup(sym)
                    if existing is not None:
                        old_w = self.collective_codex._entry_weight.get(sym, 1.0)
                        new_w = old_w + 1.0
                        blended = tuple(existing[j] * (old_w/new_w) + vec_norm[j] * (1.0/new_w)
                                       for j in range(min(len(existing), len(vec_norm))))
                        self.collective_codex._table[sym] = blended
                        self.collective_codex._entry_weight[sym] = new_w
                    else:
                        self.collective_codex._table[sym] = vec_norm
                        if not hasattr(self.collective_codex, '_entry_weight'):
                            self.collective_codex._entry_weight = {}
                        self.collective_codex._entry_weight[sym] = 1.0
                    self._harm_tracks.append({
                        'gid': ss.gid if ss else 0,
                        'src_self': si,
                        'tau': getattr(f, 'tau', TAU_0),
                        'phase': getattr(g, 'phase', None),
                        'vec': vec_norm,
                        'steps': [],
                    })

        # ── Self cavity enrich: deposit precipitated frames into persistent Self Codex ──
        for si, lenses in enumerate(self.selves):
            for g in lenses:
                g.enrich()

        # ── Collective heartbeat: feed harm tracks → collective processes them as events ──
        for t in self._harm_tracks:
            self.collective.process_vec(list(t['vec']), f"H_{t['gid'] % 1000000}")

        # L3 chains from collective's accumulated co-occurrence
        mem = self.collective.memory
        s = mem.tau_scale
        active = [f for f in mem.frames if f.weight > 1 * s]
        if len(active) >= 2:
            feed_time = mem._step_counter
            for f in active:
                fid_sig = f"fid_{f.fid}"
                if fid_sig not in mem._sig_to_gid:
                    mem._sig_to_gid[fid_sig] = _hash_str(fid_sig)
                mem._window.append((fid_sig, feed_time, tuple(f.vec), mem.tau))
                if len(mem._window) > mem._win_max:
                    mem._window.pop(0)
            for i in range(len(active)):
                for j in range(i + 1, len(active)):
                    ckey = tuple(sorted([f"fid_{active[i].fid}", f"fid_{active[j].fid}"]))
                    mem._cooccur[ckey] = mem._cooccur.get(ckey, 0) + int(3 * s)
            mem._form_chains()
            # L3 bridges → collective_codex too
            for f in mem.frames:
                if f.layer == 'L3':
                    n2 = math.sqrt(sum(v*v for v in f.vec))
                    if n2 > 0.01:
                        sym2 = f"L3_{f.struct_sig.gid % 1000000}"
                        vec_n2 = tuple(v/n2 for v in f.vec)
                        self.collective_codex._table[sym2] = vec_n2

        return [f for f in self.collective.memory.frames
                if math.sqrt(sum(v*v for v in f.vec)) > 0.01]

    def run_stream(self, stream, g_vec=None, g_gap=0):
        """Run one pass. Uses current generation state (no re-init)."""
        for step, (vec, label) in enumerate(stream):
            self.process_step(vec, label or f's{step}', step, g_vec, g_gap)
        result = self.finalize()
        self._prev_codex = self.collective_codex
        self._prev_harm_codexes = self.harm_codexes
        return result

    def run_gen(self, stream, n_loops=1):
        """Run a full generation: init once → n_loops passes → one finalize."""
        self.init_generation()
        for _ in range(n_loops):
            for step, (vec, label) in enumerate(stream):
                self.process_step(vec, label or f's{step}', step)
        result = self.finalize()
        self._prev_codex = self.collective_codex
        self._prev_harm_codexes = self.harm_codexes
        return result

    def metrics(self):
        total_circ = sum(
            sum(g.metrics()['circular_refs'] for g in lenses)
            for lenses in self.selves)
        avg_tau = sum(
            sum(g.tau for g in lenses) / len(lenses)
            for lenses in self.selves) / max(len(self.selves), 1)
        return {
            'total_circ': total_circ,
            'avg_tau': round(avg_tau, 4),
            'harm_routed': self.harm_routed,
            'harm_zero': self.harm_zero,
            'we_frames': len(self.collective.memory.frames),
            'collective_tau': round(self.collective.tau, 4),
        }
