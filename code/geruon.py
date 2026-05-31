"""
Geruon — GEME with endogenous time perception.

Core addition: τ is no longer a fixed constant. It evolves with the system's
predictive history, giving each Geruon an internal sense of its own temporal
phase. Phase is encoded in the output vector, enabling phase-aware communication
between units without requiring a central G0 observer.

Unlike GEME's fixed 27-dim alphabet (swap, pair, comm… — formula-language
scaffolding), Geruon's vector dimension is a configurable parameter. Default
is 16, a clean power-of-two with no semantic attachment.

Phase cycle:
  EXPANDING  — τ decreasing, bridge opening, novelty absorption
  RESTING    — τ low and stable, maintenance mode
  TENSING    — τ increasing, approaching boundary
  CRITICAL   — τ near ceiling, boundary imminent
  LOCKED     — τ at ceiling, bridge closed

When LOCKED breaks back into EXPANDING → phase transition (相变).

Key instance parameters (P0 — M4 audit):
  Geruon(kappa_tau=0.5)    — content↔time coupling (instance identity, not global)
  Geruon(gamma_tau=0.025)  — temporal pruning rate (derived: γ_τ = κ_τ × γ)

M10: τ brake — _sig_matches skips verification at Phase.LOCKED (Landauer brake).
M11: Erasure buffer (_sig_cache, _fid_to_frame) — sig→fid O(1) lookup
     avoids O(N) _sig_matches scan for known patterns. _find_frames_by_sig()
     replaces direct _sig_matches calls in L2 creation, _sig_layer, and all
     sig-matching hot paths. Metrics: codex_hits, codex_misses, codex_hit_rate.

Usage:
  from geruon import Geruon
  g = Geruon(vec_dim=16, memory_cap=16, kappa_tau=0.5)
  g.process_vec(vec, sig)
  print(g.phase, g.tau)
  print(g.arrow_output())  # fused content-time vector
"""
from __future__ import annotations
import math, statistics, random
from enum import Enum
from copy import deepcopy

# ── GEME core — only what Geruon needs (no _ALPHABET, no _VEC_DIM) ──
from geme import (
    Term, Formula, const, fn, eq, structural_signature,
    symbol_vector, vec_dist, Frame, reset_frame_id_counter,
    ASSOC_SEP, CHAIN_SEP, SIG_LEN, SRC_LEN,
    DELTA, GAMMA,
)

# ── Geruon-specific constants ──
# ALL multipliers follow GEME discipline: small integers or simple fractions
# (×0.4, ×0.2, ×3, ×4, ×1/4). No arbitrary decimals.

VEC_DIM_DEFAULT = 16
TAU_0 = 0.60                     # τ anchor — from GEME
GI = 4                            # time-decoupling constant — BGM Pareto optimum, M12 Landauer-limited self-reference depth
TAU_ADAPT_RATE = GAMMA * 0.4     # τ inertia: slower than frame decay (cf. DW_THRESHOLD = γ×0.4)
TAU_HISTORY_LEN = int(1 / TAU_ADAPT_RATE)  # 1/(γ×0.4) = 50 — one complete τ breathing cycle
DTAU_STABLE = GAMMA * 0.2        # |dτ/dt| stable threshold: γ×0.2 = γ×(1-τ₀)/2 (cf. META_STABLE = γ×0.2)

# Phase thresholds — integer multiples of γ around τ₀
# Hysteresis band: ±1γ for resting/tensing, +3γ for locked
PHASE_RESTING_CEIL = TAU_0 - GAMMA * 1         # 0.55 — τ below = safe zone
PHASE_TENSING_CEIL = TAU_0 + GAMMA * 1         # 0.65 — τ below = normal
PHASE_LOCKED_FLOOR  = TAU_0 + GAMMA * 3         # 0.75 — τ above = boundary

# ── Operational τ — now instance-level via Geruon(kappa_tau=…, gamma_tau=…) ──
# Module-level defaults retained for legacy experiment scripts only.
# New code: Geruon(kappa_tau=0.5) — κ_τ is structural identity, not global config.
_KAPPA_TAU_DEFAULT = 1.0
_GAMMA_TAU_DEFAULT = GAMMA * 1

# Backward-compat aliases (deprecated — use Geruon(kappa_tau=…) instead)
KAPPA_TAU = _KAPPA_TAU_DEFAULT
GAMMA_TAU = _GAMMA_TAU_DEFAULT

# Precipitation — integer counts
PRECIPITATE_MIN_SURVIVAL = 1
PRECIPITATE_MIN_ACTIVATIONS = 3

# Phase band cache (vec_dim → bands dict)
_phase_bands_cache = {}

# Deterministic string hash (DJB2 variant — same algorithm as StructuralSig._hash_vec)
def _hash_str(s: str) -> int:
    h = 5381
    for ch in s:
        h = ((h << 5) + h) ^ ord(ch)
    return h & 0x7FFFFFFF


class Phase(Enum):
    EXPANDING  = "expanding"   # τ↓ bridge opening, learning
    RESTING    = "resting"     # τ low stable, maintenance
    TENSING    = "tensing"     # τ↑ approaching boundary
    CRITICAL   = "critical"    # τ near ceiling, boundary close
    LOCKED     = "locked"      # τ at ceiling, bridge closed


def _compute_phase_bands(vec_dim: int) -> dict:
    """Allocate non-overlapping bands for 5 phases across vec_dim bins.
    Result cached — bands are pure function of vec_dim.
    """
    if vec_dim in _phase_bands_cache:
        return _phase_bands_cache[vec_dim]
    n = vec_dim
    base = n // 5
    extra = n % 5
    sizes = [base + (1 if i < extra else 0) for i in range(5)]
    starts = []
    acc = 0
    for s in sizes:
        starts.append(acc)
        acc += s
    result = {
        Phase.EXPANDING:  (starts[0], starts[0] + sizes[0] - 1),
        Phase.RESTING:    (starts[1], starts[1] + sizes[1] - 1),
        Phase.TENSING:    (starts[2], starts[2] + sizes[2] - 1),
        Phase.CRITICAL:   (starts[3], starts[3] + sizes[3] - 1),
        Phase.LOCKED:     (starts[4], starts[4] + sizes[4] - 1),
    }
    _phase_bands_cache[vec_dim] = result
    return result


def phase_encode(anomaly: float, phase: Phase, vec_dim: int = VEC_DIM_DEFAULT) -> tuple:
    """Encode (anomaly, phase) into a vec_dim vector.

    Anomaly ∈ [0, 1] maps to position within the phase's band.
    Different phases activate non-overlapping vector regions.
    """
    bands = _compute_phase_bands(vec_dim)
    lo, hi = bands[phase]
    n_bins = hi - lo + 1
    idx = lo + int(anomaly * (n_bins - 1))
    idx = max(lo, min(hi, idx))
    v = [0.0] * vec_dim
    v[idx] = 1.0
    return tuple(v)


def phase_decode(vec) -> tuple:
    """Inverse of phase_encode: (anomaly, phase) from vector."""
    vec_dim = len(vec)
    bands = _compute_phase_bands(vec_dim)
    best_i = max(range(vec_dim), key=lambda i: vec[i])
    if vec[best_i] == 0.0:
        return 0.0, None
    for ph, (lo, hi) in bands.items():
        if lo <= best_i <= hi:
            n_bins = hi - lo + 1
            anomaly = (best_i - lo) / max(n_bins - 1, 1)
            return anomaly, ph
    return 0.5, None


# ──────────────────────────────────────────────────────────────────
# StructuralSig — Gödel encoding of frame identity
# ──────────────────────────────────────────────────────────────────

# Primes for Gödel encoding (enough for 4 refs beyond the 3 base fields)
_GODEL_PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47)
_MAX_REFS = 2 * int(GI)  # 2×GI=8 — max recursive refs in a structural signature


class StructuralSig:
    """Collision-resistant structural signature of a frame.

    A signature IS the frame's structural fingerprint — not a human-given
    name. Two frames with identical structure produce identical signatures.

    Identity is determined by struct_key — a collision-resistant tuple of
    (vec_hash, weight_bin, layer, tau_bin, ref_keys). The gid is a compact
    display id derived from struct_key; it is NOT injective and must not
    be used for equality.

    Self-reference closure: a StructuralSig can contain references to other
    StructuralSig objects (including itself, directly or transitively).
    Circular reference chains are detectable and tracked.
    """

    __slots__ = ('struct_key', 'gid', 'vec_hash', 'weight_bin', 'layer', 'tau_bin', 'refs')

    def __init__(self, vec, weight, layer, refs=(), tau=TAU_0):
        self.vec_hash = self._hash_vec(vec)
        self.weight_bin = _log2_bin(weight)
        self.layer = layer
        if tau < PHASE_RESTING_CEIL:       self.tau_bin = 0
        elif tau < PHASE_TENSING_CEIL:     self.tau_bin = 1
        elif tau < PHASE_LOCKED_FLOOR:     self.tau_bin = 2
        else:                              self.tau_bin = 3
        self.refs = tuple(refs) if refs else ()
        # ref_keys: use struct_key for stable identity, fallback to gid for legacy
        self.struct_key = self._compute_key()
        self.gid = self._compute_display_id()

    @staticmethod
    def _hash_vec(vec) -> int:
        """Deterministic 32-bit hash of quantized vector content."""
        h = 5381
        for v in vec:
            h = ((h << 5) + h) ^ int(round(v, 4) * 10000)
        return h & 0x7FFFFFFF

    def _ref_keys(self):
        """Stable identity keys of referenced signatures."""
        return tuple(r.struct_key if hasattr(r, 'struct_key') else r.gid for r in self.refs)

    def _compute_key(self):
        """Collision-resistant structural identity tuple.

        Includes full vec_hash, weight_bin, layer, tau_bin, and ref identity keys.
        This is the authoritative identity — two frames are structurally equal
        iff their struct_key tuples are equal.
        """
        return (self.vec_hash, self.weight_bin, self.layer, self.tau_bin, self._ref_keys())

    def _compute_display_id(self) -> int:
        """Compact display id derived from struct_key. NOT injective — display only."""
        return hash(self.struct_key) & 0x7FFFFFFF

    def __eq__(self, other):
        if not isinstance(other, StructuralSig):
            return False
        return self.struct_key == other.struct_key

    def __hash__(self):
        return hash(self.struct_key)

    def add_ref(self, other):
        """Append a reference to another StructuralSig. Recomputes identity.

        This is the operational form of diagonalization: a frame's
        signature can be extended to reference another frame after
        creation, enabling true self-referential cycles.
        """
        self.refs = self.refs + (other,)
        self.struct_key = self._compute_key()
        self.gid = self._compute_display_id()

    def __repr__(self):
        ref_keys = self._ref_keys()
        r = ','.join(str(rk)[:8] for rk in ref_keys[:3])
        if len(ref_keys) > 3:
            r += '…'
        return f"Σ({self.gid % 1000000:06d}|L{_layer_int(self.layer)}|→{r or '-'})"


def _log2_bin(w: float) -> int:
    """Log-scale weight bin for structural encoding."""
    if w <= 0:
        return 0
    return int(math.log2(w))


def _layer_int(layer: str) -> int:
    return {'L1': 1, 'L2': 2, 'L3': 3, 'L4': 4, 'L5': 5, 'L6': 6}.get(layer, 0)


def detect_circularity(sig: StructuralSig, visited=None, depth=0) -> tuple:
    """Trace reference chains to detect self-referential cycles.

    Returns (is_circular, chain) where chain is the list of gids
    from entry point to the repeated node, empty if acyclic.
    Depth limited to prevent infinite recursion on malformed refs.
    Uses struct_key for stable identity tracking.
    """
    if visited is None:
        visited = set()
    if depth > 20:
        return False, ()
    if sig.struct_key in visited:
        return True, (sig.gid,)
    visited.add(sig.struct_key)
    for ref in sig.refs:
        is_circ, chain = detect_circularity(ref, visited, depth + 1)
        if is_circ:
            return True, (sig.gid,) + chain
    return False, ()


# ──────────────────────────────────────────────────────────────────
# Codex — externalized symbol table for cross-generational transmission
# ──────────────────────────────────────────────────────────────────

class Codex:
    """Externalized symbol→vector mapping — the "language" passed between generations.

    A Codex is NOT the system's internal encoding. It is an external artifact —
    a writing system — that one generation produces and the next receives as
    part of its environment. This is the operational form of EE's core claim:
    signatures that survive individual death and become inputs for new bridges.

    The codex serves two functions:
      1. Initialization: new Geruon instances look up symbols to get seed vectors
      2. Boundary detection: symbols NOT in the codex are "novel" — potential 碰数
    """

    def __init__(self, name="unnamed"):
        self.name = name
        self._table = {}       # symbol → vector tuple
        self._generation = 0   # how many generations this codex has passed through
        self._history = []     # [(gen, event, detail), ...]
        self._entry_weight = {}  # symbol → accumulated weight (for merge tracking)

    # ── Builders ──

    @classmethod
    def from_alphabet(cls, alphabet: list, vec_dim: int = 16, seed=42):
        """Create a codex from a symbol alphabet.

        Each symbol gets a deterministic sparse vector — the same symbol
        always maps to the same vector for a given seed, making the codex
        reproducible across instances.
        """
        r = random.Random(seed)
        c = cls(name=f"alphabet_{len(alphabet)}")
        for sym in alphabet:
            # Sparse vector: 2-3 active dimensions per symbol
            v = [0.0] * vec_dim
            indices = set()
            while len(indices) < min(int(GI) - 1, vec_dim):  # GI-1=3 — sparse activation per symbol
                indices.add(r.randint(0, vec_dim - 1))
            for i in indices:
                v[i] = round(r.uniform(0.3, 1.0), 4)
            # Normalize
            s = math.sqrt(sum(x * x for x in v))
            v = tuple(x / max(s, 0.001) for x in v)
            c._table[sym] = v
        c._history.append((0, "created", f"{len(alphabet)} symbols, dim={vec_dim}"))
        return c

    @classmethod
    def empty(cls, name="empty", vec_dim=16):
        """Create an empty codex — a blank writing system."""
        c = cls(name=name)
        c._history.append((0, "created", f"empty, dim={vec_dim}"))
        return c

    # ── Query ──

    def lookup(self, symbol: str) -> tuple:
        """Look up a symbol. Returns None if not found — potential 碰数."""
        return self._table.get(symbol)

    def is_novel(self, symbol: str) -> bool:
        """True if symbol is not in the codex — a boundary encounter."""
        return symbol not in self._table

    def __contains__(self, symbol: str) -> bool:
        return symbol in self._table

    def __len__(self) -> int:
        return len(self._table)

    def symbols(self) -> list:
        return list(self._table.keys())

    def nearest(self, vec):
        """Find closest Codex entry to query vector. Returns (symbol, vector, distance)."""
        if not self._table:
            return None, None, float('inf')
        best_sym = None; best_vec = None; best_dist = float('inf')
        for sym, cv in self._table.items():
            d = math.sqrt(sum((a-b)**2 for a,b in zip(vec, cv)))
            if d < best_dist:
                best_dist = d; best_sym = sym; best_vec = cv
        return best_sym, best_vec, best_dist

    def blend_in(self, vec, dist, weight=GAMMA):
        """Blend a Codex entry into an input vector. Weight decays with distance."""
        if dist >= 2.0:
            return list(vec)
        w = weight * (1.0 - dist/2.0)  # far = less influence
        best_sym, best_vec, _ = self.nearest(vec)
        if best_vec is None:
            return list(vec)
        return [(1.0 - w) * vec[i] + w * best_vec[i]
                for i in range(min(len(vec), len(best_vec)))]

    # ── Enrichment (generation writes back) ──

    def add(self, symbol: str, vec: tuple, source="manual"):
        """Add or update a symbol mapping. Called when a generation
        enriches the codex with its own stable frames.

        Two merge strategies:
        1. Cosine > 0.95: near-identical entries merged (all types)
        2. Coverage merge (ABS_* only): new abstraction covers all active dims
           of existing abstraction → merge as more complete evidence.
        """
        MERGE_SIMILARITY = 0.95
        ACTIVE_THRESH = 0.1  # dimension is "active" if |value| > this

        nv = math.sqrt(sum(x*x for x in vec))
        if nv > 0:
            vec_norm = tuple(x/nv for x in vec)

            # Strategy 1 (reordered): coverage merge first (ABS_* only)
            # More complete evidence should extend incomplete abstractions
            # before being merged as near-identical to complete ones.
            if 'ABS' in symbol or 'ABS' in str(source):
                vec_active = {j for j in range(len(vec)) if abs(vec_norm[j]) > ACTIVE_THRESH}
                best_target = None; best_active_count = 999
                for existing_sym, existing_vec in self._table.items():
                    if 'ABS' not in str(existing_sym) and 'ABS' not in str(existing_sym):
                        continue
                    ev = math.sqrt(sum(x*x for x in existing_vec))
                    if ev <= 0: continue
                    ev_norm = [x/ev for x in existing_vec]
                    old_active = {j for j in range(len(existing_vec)) if abs(ev_norm[j]) > ACTIVE_THRESH}
                    if old_active and old_active.issubset(vec_active):
                        if len(old_active) < best_active_count:
                            best_active_count = len(old_active)
                            best_target = (existing_sym, existing_vec, old_active)

                if best_target is not None:
                    existing_sym, existing_vec, old_active = best_target
                    old_w = self._entry_weight.get(existing_sym, 1.0)
                    blended = list(existing_vec)
                    for j in vec_active:
                        blended[j] = (existing_vec[j]*old_w + vec[j])/(old_w+1.0)
                    self._table[existing_sym] = tuple(blended)
                    self._entry_weight[existing_sym] = old_w + 1.0
                    self._history.append(
                        (self._generation, "coverage",
                         f"{symbol} ⊃ {existing_sym} (w={old_w+1:.0f} n_active={len(old_active)}→{len(vec_active)})"))
                    return

            # Strategy 2: near-identical merge (all entry types)
            for existing_sym, existing_vec in self._table.items():
                ev = math.sqrt(sum(x*x for x in existing_vec))
                if ev <= 0: continue
                dot = sum(a*b for a,b in zip(vec_norm, [x/ev for x in existing_vec]))
                if dot > MERGE_SIMILARITY:
                    old_w = self._entry_weight.get(existing_sym, 1.0)
                    blended = tuple((existing_vec[j]*old_w + vec[j])/(old_w+1.0)
                                   for j in range(min(len(existing_vec), len(vec))))
                    self._table[existing_sym] = blended
                    self._entry_weight[existing_sym] = old_w + 1.0
                    self._history.append(
                        (self._generation, "merge",
                         f"{symbol} → {existing_sym} (w={old_w+1:.0f})"))
                    return

        is_new = symbol not in self._table
        self._table[symbol] = tuple(vec)
        self._history.append(
            (self._generation, "add" if is_new else "update",
             f"{symbol} ({source})"))

    def new_generation(self):
        """Mark passage to next generation."""
        self._generation += 1
        self._history.append((self._generation, "generation", "passed"))

    # ── Persistence ──

    def save(self, path):
        import json
        state = {
            'name': self.name,
            'generation': self._generation,
            'table': {s: list(v) for s, v in self._table.items()},
            'history': self._history,
            'entry_weight': self._entry_weight,
        }
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)

    @classmethod
    def load(cls, path):
        import json
        with open(path) as f:
            state = json.load(f)
        c = cls(name=state.get('name', 'loaded'))
        c._generation = state.get('generation', 0)
        c._table = {s: tuple(v) for s, v in state.get('table', {}).items()}
        c._history = state.get('history', [])
        c._entry_weight = {s: float(w) for s, w in state.get('entry_weight', {}).items()}
        return c

    def __repr__(self):
        return f"Codex('{self.name}' gen={self._generation} |{len(self._table)}|)"


# ──────────────────────────────────────────────────────────────────
# BiasField — gradient-based externalized memory (non-symbolic)
# ──────────────────────────────────────────────────────────────────

class BiasField:
    """Gradient-field accumulator for cross-generational transmission.

    Unlike Codex (symbol→vector lookup table), BiasField is a non-symbolic
    gradient field. Precipitated frames' vectors × weights accumulate into
    a bias vector. The next generation doesn't "read" symbols — it inherits
    the bias as structural tendency in its initial frame economy.

    Inspired by GABAergic inhibition: neurons don't pass symbol labels —
    they pass gradients that bias post-synaptic potentials.
    """

    def __init__(self, vec_dim=16):
        self.vec_dim = vec_dim
        self.bias = [0.0] * vec_dim   # accumulated gradient
        self._total_weight = 0.0      # for normalization
        self._count = 0               # number of frames deposited
        self._generation = 0

    def deposit(self, vec, weight=1.0):
        """Accumulate a frame's vector into the bias field."""
        w = max(0.0, weight)
        for i in range(min(len(vec), self.vec_dim)):
            self.bias[i] += vec[i] * w
        self._total_weight += w
        self._count += 1

    def deposit_frame(self, frame):
        """Deposit a GeruonFrame's vector × weight into the bias field."""
        self.deposit(frame.vec, frame.weight)

    def normalized(self) -> tuple:
        """Return the bias field normalized by total weight."""
        if self._total_weight <= 0:
            return tuple(self.bias)
        return tuple(v / self._total_weight for v in self.bias)

    def is_empty(self) -> bool:
        return self._count == 0

    def blend_into(self, vec, weight=None):
        if weight is None:
            weight = GAMMA  # default = γ
        """Blend the bias field into an input vector.

        Like GABA in the synaptic cleft — always present, continuously
        modulating. The bias is the accumulated precipitate of all units
        sharing this field, weighted by blend ratio.
        """
        if self.is_empty():
            return list(vec)
        normed = self.normalized()
        return [(1.0 - weight) * vec[i] + weight * normed[i]
                for i in range(min(len(vec), self.vec_dim))]

    def seed_frames(self, memory, count=3):
        """Create initial GeruonFrames from the bias field.

        Each seeded frame captures one significant dimension of the bias,
        giving the next generation structural inheritance without symbols."""
        if self._total_weight <= 0 or self._count == 0:
            return 0
        if self.is_empty():
            return 0
        normed = self.normalized()
        ranked = sorted(range(self.vec_dim),
                       key=lambda i: abs(normed[i]), reverse=True)
        n = 0
        for dim in ranked[:count]:
            if abs(normed[dim]) < 0.01:
                continue
            vec = [0.0] * self.vec_dim
            vec[dim] = 1.0 if normed[dim] > 0 else -1.0
            f = GeruonFrame(tuple(vec),
                           weight=self._total_weight / max(count, 1),
                           sig=f'bias_dim{dim}', layer='L1')
            memory.frames.append(f)
            memory.total_weight += f.weight
            memory._track_frame_sig(f)
            n += 1
        return n

    def save(self, path):
        import json
        state = {
            'vec_dim': self.vec_dim,
            'bias': list(self.bias),
            'total_weight': self._total_weight,
            'count': self._count,
            'generation': self._generation,
        }
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)

    @classmethod
    def load(cls, path):
        import json
        with open(path) as f:
            state = json.load(f)
        bf = cls(vec_dim=state.get('vec_dim', 16))
        bf.bias = state.get('bias', [0.0]*bf.vec_dim)
        bf._total_weight = state.get('total_weight', 0.0)
        bf._count = state.get('count', 0)
        bf._generation = state.get('generation', 0)
        return bf

    def __repr__(self):
        return (f"BiasField(dim={self.vec_dim} count={self._count} "
                f"Σw={self._total_weight:.1f} gen={self._generation})")


class GeruonFrame(Frame):
    """Frame with structural signature and precipitation tracking.

    struct_sig is computed from the frame's structural properties
    at creation time and updated on merge. The string sig is set
    to a compact representation of the Gödel number.

    Precipitation (沉积): a frame that survives multiple induction
    cycles, is activated in prediction paths, and is structurally
    stable — it becomes an externalized trace (Codex/Ledger entry).
    """
    __slots__ = ('struct_sig', 'survival_cycles', 'activations', 'precipitated', '_externalized', 'tau')

    def __init__(self, vec, weight=1.0, sig="", src="", layer="L1",
                 struct_sig=None, ref_sigs=(), tau=TAU_0):
        super().__init__(vec, weight, sig, src, layer)
        if struct_sig is not None:
            self.struct_sig = struct_sig
        else:
            self.struct_sig = StructuralSig(vec, weight, layer, ref_sigs, tau=tau)
        self.tau = tau            # birth τ — for operational τ (merge/cooccur/prune)
        tag = sig[:16] if sig and not sig.startswith('Σ') else ''
        suffix = f"_{tag}" if tag else ''
        self.sig = f"Σ{int(self.struct_sig.gid) % 1000000:06d}{suffix}"
        self.sig_full = self.sig
        # ── Precipitation tracking ──
        self.survival_cycles = 0   # induction_clean survivals
        self.activations = 0       # times in prediction path
        self.precipitated = False
        self._externalized = False  # idempotent enrichment guard


def make_frame_sig(vec, weight, layer, ref_sigs=()) -> StructuralSig:
    """Compute structural signature for a frame about to be created."""
    return StructuralSig(vec, weight, layer, ref_sigs)


# ──────────────────────────────────────────────────────────────────
# GeruonMemory — Memory with endogenous τ
# ──────────────────────────────────────────────────────────────────
class GeruonMemory:
    """Extended Memory that maintains endogenous τ and time phase.

    τ evolves with prediction accuracy — rising when predictions fail
    (environment is surprising), falling when they succeed. The rate of
    change dτ/dt defines the breathing phase.
    """

    def __init__(self, vec_dim=VEC_DIM_DEFAULT, capacity=10, cooccur_window=None,
                 cooccur_thresh=0.25, max_chains=5,  # 0.25=1/GI — M12 anchor
                 kappa_tau=None, gamma_tau=None):
        if kappa_tau is None:
            kappa_tau = _KAPPA_TAU_DEFAULT
        if gamma_tau is None:
            gamma_tau = _GAMMA_TAU_DEFAULT
        if cooccur_window is None:
            cooccur_window = capacity * int(GI)  # M12: window anchor = cap × GI, τ-modulated at use
        self.kappa_tau = kappa_tau         # content↔time coupling (instance-level)
        self.gamma_tau = gamma_tau         # temporal pruning rate (derived from κ_τ)
        self.vec_dim = vec_dim
        # ── Core Memory fields (same algorithms as geme.Memory) ──
        self.frames = []
        self.capacity = max(capacity, 1)
        self.cooccur_thresh = cooccur_thresh
        self.total_weight = 0.0
        self._window = []
        self._win_max = cooccur_window      # anchor = cap × GI (M12)
        self._step_counter = 0
        self._cooccur = {}
        self._assoc_frames = 0
        self._chain_count = 0
        self.max_chains = max(max_chains, 1)
        self._merge_dists = []
        self._learn_dists = []
        self.preserve_sig = True
        self._last_merge_fid = None
        self._merge_history = []
        self._novelty_bonus = 1.0 / (GAMMA * int(GI))  # 1/(γ×GI)=5 — new frame weight bonus
        self.quantum_mode = False
        self._weight_history = {}
        self._derivative_frames = []
        self._prediction_accuracy = []
        self._pred_errors = 0
        self._pred_total = 0
        self._confidences = []
        self._conf_threshold = TAU_0 * 0.5  # τ₀/2=0.30 — initial confidence seed, adapts from data
        self._doubt_mode = False
        self._last_accuracy = 1.0
        self._multiverse_enabled = True
        self._multiverse = []
        self._step_branched = set()
        self._merge_thresh_val = 0.0
        self._qrand = random.Random(42)  # fixed seed for reproducibility; all cavities share same RNG

        # ── Geruon additions: endogenous τ ──
        self.tau = TAU_0
        self._tau_history = []          # (step, tau) pairs
        self._tau_pred_errors = []      # |pred_tau - actual_tau| — time self-prediction
        self._last_phase = Phase.RESTING
        self._phase_steps = {ph: 0 for ph in Phase}
        self._phase_transitions = []    # (step, from_phase, to_phase)

        # ── StructuralSig: circularity tracking ──
        self._circular_refs = {}        # gid → (step_first_seen, chain)
        self._sig_index = {}            # struct_key → frame (collision-resistant)
        # Reset global fid counter for deterministic runs (short-term fix;
        # long-term: localize fid to GeruonMemory)
        reset_frame_id_counter()
        self._sig_to_gid = {}           # string sig → gid (display)
        self._sig_to_key = {}           # string sig → struct_key (identity)
        self._sys_fids = {}             # 'pred_err'/'sys_doubt' → fid (O(1) lookup)

        # ── 碰数 (pengshu) detection ──
        self._pengshu_events = []       # [(step, gid, phase, tau, dtaudt), ...]
        self._prediction_path_gids = [] # gids in most recent prediction path
        self._pengshu_cooldown = 0      # steps since last 碰数 (debounce)

        # ── τ operational switches (P0-3 ablation) — default all ON ──
        self.tau_in_merge = True     # |τ_a−τ_b| < ε — time-gated merge
        self.tau_in_cooccur = True   # count += 1−|τ_a−τ_b| — time-weighted cooccur
        self.tau_in_prune = True     # |τ_cur−τ_f|×γ_τ — time-biased pruning

        # ── M11: Codex erasure buffer (sig→fid) — Landauer bill cache ──
        self._sig_cache = {}             # sig → fid (O(1) lookup, avoids O(N) _sig_matches)
        self._fid_to_frame = {}          # fid → frame (maintained on frame add/remove)
        self._codex_hits = 0             # count: cache hits (for bill metrics)
        self._codex_misses = 0           # count: cache misses

        # ── Self-boundary (BGM cliff) ──
        self._gate_open = True           # cliff gate latch — snaps shut at dτ/dt cliff

        # ── Faraday readings: centroid tracking ──
        self._prev_centroid = None        # previous step centroid (for wit)
        self._centroid_displacement = 0.0 # last displacement |c_t − c_{t-1}|
        self._wit_hits = 0                # count: |c_t − c_{t-1}| > structon

    def centroid(self):
        """Weighted centroid of all current frames. None if no frames."""
        if not self.frames or self.total_weight <= 0:
            return None
        D = self.vec_dim
        c = [0.0] * D
        for f in self.frames:
            w = f.weight
            for j in range(D):
                c[j] += f.vec[j] * w
        tw = self.total_weight
        return tuple(c[j] / tw for j in range(D))

    def _update_centroid_tracking(self, structon):
        """Call after each step to update centroid displacement and wit count."""
        c = self.centroid()
        if c is not None and self._prev_centroid is not None:
            d2 = sum((c[j] - self._prev_centroid[j]) ** 2 for j in range(self.vec_dim))
            self._centroid_displacement = math.sqrt(d2)
            if structon is not None and self._centroid_displacement > structon:
                self._wit_hits += 1
        else:
            self._centroid_displacement = 0.0
        self._prev_centroid = c

    def _zero_vec(self):
        return (0.0,) * self.vec_dim

    @property
    def dtaudt(self) -> float:
        """Rate of τ change over recent history (linear regression slope)."""
        if len(self._tau_history) < 5:
            return 0.0
        recent = self._tau_history[-TAU_HISTORY_LEN:]
        n = len(recent)
        xs = [h[0] for h in recent]
        ys = [h[1] for h in recent]
        x_mean = sum(xs) / n
        y_mean = sum(ys) / n
        num = sum((xs[i] - x_mean) * (ys[i] - y_mean) for i in range(n))
        den = sum((xs[i] - x_mean) ** 2 for i in range(n))
        return num / max(den, 0.001)

    @property
    def tau_scale(self) -> float:
        """Breathing factor for creation thresholds: 1.0 at τ₀, <1 expanding, >1 locked.
        All L2/L3/L4 creation thresholds scale by this factor — one knob closes the τ→creation loop."""
        return self.tau / TAU_0

    @property
    def phase(self) -> Phase:
        """Current breathing phase — simple forward mapping from τ and dτ/dt.

        Phase is a reading, not a parameter. Under temporal input it serves
        as the operational identity basis (BGM §2.2: τ becomes the signature scheme).
        """
        return self._compute_phase()

    def _compute_phase(self):
        tau = self.tau
        dt = self.dtaudt

        # Hysteresis band: ×2 prevents phase flicker on minor τ fluctuations.
        # Without it, the system oscillates between adjacent phases every few steps.
        # 2 = "twice stable" — not a GI derivative, a phase stability design choice.
        if tau >= PHASE_LOCKED_FLOOR and abs(dt) < DTAU_STABLE * 2:
            return Phase.LOCKED
        if tau >= PHASE_TENSING_CEIL and dt > DTAU_STABLE:
            return Phase.CRITICAL
        if tau >= PHASE_RESTING_CEIL and dt > DTAU_STABLE:
            return Phase.TENSING
        if dt < -DTAU_STABLE:
            return Phase.EXPANDING
        if tau < PHASE_RESTING_CEIL and abs(dt) < DTAU_STABLE * 2:
            return Phase.RESTING
        if tau >= PHASE_RESTING_CEIL:
            return Phase.TENSING
        return Phase.RESTING

    @property
    def cliff_gate(self) -> float:
        """BGM cliff: discontinuous self-boundary gate.

        When dτ/dt crosses upward through DTAU_STABLE, gate snaps SHUT (0.0)
        and LATCHES until phase fully cycles to EXPANDING. This is NOT a
        continuous modulation — it is a phase transition of the self-boundary.

        BGM analogue: conf_threshold jumping from 0.3 to 1.0 at step 23.
        """
        dt = self.dtaudt
        if self._gate_open and dt > DTAU_STABLE and self.tau > PHASE_RESTING_CEIL:
            self._gate_open = False
        elif not self._gate_open and self.phase == Phase.EXPANDING:
            self._gate_open = True
        return 1.0 if self._gate_open else 0.0

    # ── Core Memory methods ──

    def _adaptive_window(self):
        if not self.frames:
            return self._win_max
        avg_life = self.total_weight / max(len(self.frames), 1)
        ceil = self.capacity * 2 * int(GI)  # 2×base_window = cap×8 — prevents explosion in long streams
        adaptive = max(int(GI) + 1, min(ceil, int(avg_life * 2)))
        return adaptive

    def _adaptive_thresh(self):
        if not self._merge_dists:
            if len(self._learn_dists) < 10:
                return None
            t = sorted(self._learn_dists)[len(self._learn_dists) // 4]
            if t <= 0:
                t = statistics.mean(self._learn_dists) * 0.5
            if t <= 0:
                t = 0.001
            self._merge_dists.append(t)
            return t
        med = statistics.median(self._merge_dists[-50:])
        last_ok = self._merge_dists[-1] if self._merge_dists else 0.001
        return max(med, last_ok * 0.5)

    def _merge_frame(self, f, vec, sig):
        self.total_weight -= f.weight
        f.vec = tuple((f.vec[j] * f.weight + vec[j]) / (f.weight + 1)
                      for j in range(len(vec)))
        f.weight += 1.0
        f.merged += 1
        # StructuralSig update: vec/weight changed → gid must change
        # (P0 fix: same structure → same gid; different structure → different gid)
        if hasattr(f, 'struct_sig') and f.struct_sig is not None:
            f.struct_sig = StructuralSig(f.vec, f.weight, f.layer,
                                         f.struct_sig.refs, tau=getattr(f, 'tau', TAU_0))
            tag = ""
            if sig and not sig.startswith('Σ'):
                tag = f"_{sig[:12]}"
            f.sig = f"Σ{f.struct_sig.gid % 1000000:06d}{tag}"
            f.sig_full = f.sig
        elif not self.preserve_sig:
            combined = "_".join(sorted(set(f.sig.split("_") + sig.split("_"))))
            if len(combined.split("_")) <= 8:
                f.sig = combined[:SIG_LEN]
        self.total_weight += f.weight
        self._last_merge_fid = f.fid
        self._merge_history.append(f.fid)
        if f.fid not in self._weight_history:
            self._weight_history[f.fid] = []
        self._weight_history[f.fid].append((self._step_counter, f.weight))
        if len(self._weight_history[f.fid]) > 50:
            self._weight_history[f.fid].pop(0)

    def _quantum_merge(self, candidates, vec, sig):
        psum = 0.0
        probs = []
        for i, d, f in candidates:
            p = math.exp(-d / max(self._merge_thresh_val, 0.001))
            probs.append((i, d, f, p))
            psum += p
        if psum <= 0:
            return False
        r = self._qrand.random() * psum
        acc = 0.0
        bi = candidates[0][0]
        bd = candidates[0][1]
        for i, d, f, p in probs:
            acc += p
            if r <= acc:
                bi, bd = i, d
                break
        if self._multiverse_enabled and len(candidates) > 1:
            for i, d, f in candidates:
                if i == bi:
                    continue
                if len(self._multiverse) >= int(GI) - 1:  # GI-1=3 — max parallel branches
                    self._multiverse.pop(0)
                branch_frames = deepcopy(self.frames)
                for bf in branch_frames:
                    if bf.fid == f.fid:
                        bf.vec = tuple(
                            (bf.vec[j] * bf.weight + vec[j]) / (bf.weight + 1)
                            for j in range(len(vec)))
                        bf.weight += 1.0
                        bf.merged += 1
                        break
                self._multiverse.append(
                    (branch_frames, self._step_counter,
                     f"branch_{self._step_counter}_{f.fid}"))
        self._merge_dists.append(bd)
        if len(self._merge_dists) > 100:
            self._merge_dists.pop(0)
        self._merge_frame(self.frames[bi], vec, sig)
        # Register merged sig → gid for prediction path
        ss = getattr(self.frames[bi], 'struct_sig', None)
        if ss is not None:
            self._sig_to_gid[sig] = ss.gid
        return True

    def _track_cooccurrence(self, sig, vec):
        self._step_counter += 1
        # NOTE: _win_max is fixed at cap×GI. τ modulation on window size was tested
        # and rejected (M15 follow-up): even mild shrinkage destroys cooccurrence
        # accumulation. The window needs stability to form patterns. τ regulates
        # cooccurrence via tau_scale in the L2 threshold, not via window size.
        # Ensure every sig in the window has a gid mapping for prediction path
        if sig not in self._sig_to_gid:
            self._sig_to_gid[sig] = _hash_str(sig)
        self._window.append((sig, self._step_counter, tuple(vec), self.tau))
        if len(self._window) > self._win_max:
            self._window.pop(0)
        for i in range(len(self._window)):
            for j in range(i + 1, min(i + (int(GI) - 1), len(self._window))):  # GI-1=3 neighbour distance
                s1, id1, tau1 = self._window[i][0], self._window[i][1], self._window[i][3]
                s2, id2, tau2 = self._window[j][0], self._window[j][1], self._window[j][3]
                if id1 == id2:
                    continue
                key = tuple(sorted([s1, s2]))
                tw = 1.0 - self.kappa_tau * abs(tau1 - tau2) if self.tau_in_cooccur else 1.0
                tw = max(0.0, min(1.0, tw))
                self._cooccur[key] = self._cooccur.get(key, 0) + tw
        total_steps = len(self._window)
        s = self.tau_scale
        if total_steps >= int(2 * int(GI) * s):  # 2×GI=8 — L2 trigger window
            for (sa, sb), count in list(self._cooccur.items()):
                ratio = count / total_steps
                if ratio >= self.cooccur_thresh * s and count >= max(int((int(GI) - 1) * s), int(total_steps * GAMMA * TAU_0 * s)):  # GI-1=3, γ×τ₀=0.03
                    # Build L2 sig from STRUCTURAL identities (gids), not external labels
                    gid_a = self._sig_to_gid.get(sa)
                    gid_b = self._sig_to_gid.get(sb)
                    tag_a = f"Σ{gid_a % 1000000:06d}" if gid_a else sa[:20]
                    tag_b = f"Σ{gid_b % 1000000:06d}" if gid_b else sb[:20]
                    assoc_sig = tag_a + ASSOC_SEP + tag_b
                    existing = self._find_frames_by_sig(assoc_sig)
                    if existing:
                        for exf in existing:
                            self.total_weight -= exf.weight
                            exf.weight += 0.5
                            exf.merged += 1
                            self.total_weight += exf.weight
                    else:
                        frames_a = self._find_frames_by_sig(sa)
                        frames_b = self._find_frames_by_sig(sb)
                        base_frames = frames_a + frames_b
                        # Skip L2 if no base frames exist — zero-vec L2 poisons harm routing
                        if not base_frames:
                            continue
                        total_w = sum(f.weight for f in base_frames)
                        assoc_vec = tuple(
                            sum(f.vec[j] * f.weight for f in base_frames)
                            / max(total_w, 1)
                            for j in range(self.vec_dim))
                        if len(self.frames) >= self.capacity:
                            self.frames.sort(key=lambda x: x.weight - x.age * GAMMA * 2 - (abs(self.tau - getattr(x, 'tau', TAU_0)) * self.gamma_tau if self.tau_in_prune else 0))
                            r = self.frames.pop(0)
                            self.total_weight -= r.weight
                            self._fid_to_frame.pop(r.fid, None)
                        # Build refs to the frames being associated
                        ref_sigs = []
                        for bf in base_frames[:4]:  # max 4 refs
                            ss = getattr(bf, 'struct_sig', None)
                            if ss is not None:
                                ref_sigs.append(ss)
                        nf = GeruonFrame(assoc_vec, weight=float(count),
                                   sig=assoc_sig, layer="L2", ref_sigs=ref_sigs,
                                   tau=self.tau)
                        self.frames.append(nf)
                        self.total_weight += float(count)
                        self._assoc_frames += 1
                        self._track_frame_sig(nf)
                        # Register assoc_sig → gid so duplicates can be found
                        self._sig_to_gid[assoc_sig] = nf.struct_sig.gid
                        self._sig_to_gid[nf.sig] = nf.struct_sig.gid

    def observe(self, vec, sig, src="", layer="L1"):
        if not vec:
            return
        if sig:
            self.process_prediction(sig)
        thresh = self._adaptive_thresh()
        self._merge_thresh_val = thresh or 0.0
        # _win_max is set at init to configured window; adaptive behavior
        # must be explicitly enabled via _adaptive_window_enabled flag.
        bi, bd = -1, float('inf')
        candidates = []
        for i, f in enumerate(self.frames):
            d_content = vec_dist(vec, f.vec)
            d_time = self.kappa_tau * abs(self.tau - getattr(f, 'tau', TAU_0)) if self.tau_in_merge else 0.0
            d = d_content + d_time
            if d < bd:
                bd, bi = d, i
            if self.quantum_mode and thresh and d <= thresh:
                candidates.append((i, d, f))
        if thresh is None and bi >= 0 and bd != float('inf'):
            self._learn_dists.append(bd)
            if len(self._learn_dists) > 200:
                self._learn_dists.pop(0)
        if self.quantum_mode and len(candidates) > 0:
            if self._quantum_merge(candidates, vec, sig):
                return
        # Merge condition: vector within threshold AND signature compatible
        sig_match = False
        if not sig:
            sig_match = True
        elif bi >= 0 and bi < len(self.frames):
            f_bi = self.frames[bi]
            sig_match = (
                self._sig_to_gid.get(sig) == getattr(
                    getattr(f_bi, 'struct_sig', None), 'gid', None))
        if thresh is not None and bi >= 0 and bd <= thresh and sig_match:
            self._merge_dists.append(bd)
            if len(self._merge_dists) > 100:
                self._merge_dists.pop(0)
            self._merge_frame(self.frames[bi], vec, sig)
            # ── M11: cache sig→fid for future O(1) lookup ──
            if sig and sig not in self._sig_cache:
                self._sig_cache[sig] = self.frames[bi].fid
        else:
            if thresh is None or thresh == 0.0:
                nw = 1.0
            elif bd != float('inf'):
                nw = 1.0 + self._novelty_bonus * max(0, 1.0 - bd / max(thresh, 0.001))
            else:
                nw = 1.0
            if len(self.frames) >= self.capacity:
                self.frames.sort(key=lambda x: x.weight - x.age * GAMMA * 2 - (abs(self.tau - getattr(x, 'tau', TAU_0)) * self.gamma_tau if self.tau_in_prune else 0))
                r = self.frames.pop(0)
                self.total_weight -= r.weight
                self._fid_to_frame.pop(r.fid, None)
            nf = GeruonFrame(vec, nw, sig, src, layer=layer,
                       ref_sigs=getattr(self, '_current_ref_sigs', ()),
                       tau=self.tau)
            self.frames.append(nf)
            self.total_weight += nw
            self._last_merge_fid = nf.fid
            self._merge_history.append(nf.fid)
            self._track_frame_sig(nf)
            # Map original sig (used in window/cooccur) to gid
            self._sig_to_gid[sig] = nf.struct_sig.gid
            # ── M11: cache raw input sig → fid (decorated sig cached in _track_frame_sig) ──
            self._sig_cache[sig] = nf.fid
            self._weight_history[nf.fid] = [(self._step_counter, nw)]
        self._track_cooccurrence(sig, vec)

    def _form_chains(self):
        s = self.tau_scale
        cur = {f.fid: f for f in self.frames if f.weight > 1 * s}
        if len(cur) < 2:
            return
        fids = list(cur.keys())
        for i in range(len(fids)):
            for j in range(i + 1, len(fids)):
                fa, fb = cur[fids[i]], cur[fids[j]]
                ckey = tuple(sorted([f"fid_{fa.fid}", f"fid_{fb.fid}"]))
                if self._cooccur.get(ckey, 0) >= int((int(GI) - 1) * s):  # GI-1=3 — L3 chain threshold
                    ms = f"f{fa.fid}{CHAIN_SEP}f{fb.fid}"
                    # M11: cached L3 bridge lookup — O(1) hit, O(N) fallback
                    if self._find_frames_by_sig(ms):
                        continue
                    chain_w = (fa.weight + fb.weight) / 2
                    # L3 bridge = weighted average of both ends — visible content
                    tw = fa.weight + fb.weight
                    chain_vec = tuple((fa.vec[k] * fa.weight + fb.vec[k] * fb.weight) / max(tw, 0.001)
                                      for k in range(self.vec_dim))
                    if len(self.frames) >= self.capacity:
                        self.frames.sort(key=lambda x: x.weight - x.age * GAMMA * 2 - (abs(self.tau - getattr(x, 'tau', TAU_0)) * self.gamma_tau if self.tau_in_prune else 0))
                        r = self.frames.pop(0)
                        self.total_weight -= r.weight
                        self._fid_to_frame.pop(r.fid, None)
                    ref_sigs = []
                    for bf in (fa, fb):
                        ss = getattr(bf, 'struct_sig', None)
                        if ss is not None:
                            ref_sigs.append(ss)
                    self.frames.append(GeruonFrame(
                        chain_vec, weight=chain_w, sig=ms, layer="L3",
                        ref_sigs=ref_sigs, tau=self.tau))
                    self.total_weight += chain_w
                    self._chain_count += 1
                    self._track_frame_sig(self.frames[-1])
                    # ── M11: cache raw L3 bridge sig → fid (decorated sig cached in _track_frame_sig) ──
                    self._sig_cache[ms] = self.frames[-1].fid

    def _track_frame_sig(self, f):
        """Register frame signature and detect circular references."""
        ss = getattr(f, 'struct_sig', None)
        # ── M11: fid→frame index (always maintained, even without struct_sig) ──
        self._fid_to_frame[f.fid] = f
        if ss is None:
            return
        self._sig_index[ss.struct_key] = f
        # Populate sig→gid mapping for prediction path tracking
        for s in (f.sig, getattr(f, 'sig_full', None) or ''):
            if s:
                self._sig_to_gid[s] = ss.gid
                self._sig_to_key[s] = ss.struct_key
                # ── M11: sig_cache — erasure buffer for O(1) sig lookup ──
                if s not in self._sig_cache:
                    self._sig_cache[s] = f.fid
        is_circ, chain = detect_circularity(ss)
        if is_circ:
            if ss.struct_key not in self._circular_refs:
                self._circular_refs[ss.struct_key] = (self._step_counter, chain)

    # ── M11: Erasure buffer lookup ──
    def _find_frames_by_sig(self, sig):
        """Cached sig lookup — O(1) best case, O(N) fallback.

        The erasure buffer (_sig_cache) maps sig→fid, avoiding the per-call
        overhead of string comparison and struct_sig attribute access that
        makes _sig_matches expensive at scale (49M calls).
        """
        if not sig:
            return []
        fid = self._sig_cache.get(sig)
        if fid is not None:
            f = self._fid_to_frame.get(fid)
            if f is not None and f in self.frames:
                self._codex_hits += 1
                return [f]
            # Stale cache entry — frame was pruned
            del self._sig_cache[sig]
        self._codex_misses += 1
        # ── M11: Continuous Landauer modulation ──
        # f(τ) = max(0, 1 - (τ - τ₀) / (τ_locked - τ₀))
        # Anchored to existing constants: τ₀=0.60, τ_locked=0.75
        # Deterministic per-sig: hash(sig) decides which sigs get scanned at each τ
        tau_locked = TAU_0 + GAMMA * 3   # 0.75, same as PHASE_LOCKED_FLOOR
        fallback_prob = 1.0 - (self.tau - TAU_0) / max(tau_locked - TAU_0, 0.001)
        fallback_prob = max(0.0, min(1.0, fallback_prob))
        if fallback_prob < 1.0:
            h = (_hash_str(sig) % 100000) / 100000.0  # deterministic, per-sig
            if h >= fallback_prob:
                self._landauer_skips = getattr(self, '_landauer_skips', 0) + 1
                return []
        # Fallback: O(N) scan (probability-gated by τ)
        result = [f for f in self.frames if self._sig_matches(f, sig)]
        if result:
            self._sig_cache[sig] = result[0].fid
        return result

    def _codex_bill(self):
        """Landauer bill metrics: cache efficiency = hits / (hits + misses)."""
        total = self._codex_hits + self._codex_misses
        if total == 0:
            return {'hits': 0, 'misses': 0, 'rate': 0.0}
        return {'hits': self._codex_hits, 'misses': self._codex_misses,
                'rate': round(self._codex_hits / total, 4)}

    def self_observe(self):
        """DEPRECATED: M13 dissolved L4 into the frame economy.
        τ is the real-time self-observation. fid-based window feeding
        and chain formation now happen inline in induction_clean().
        Method retained for backward compatibility with bgm_*.py callers."""
        pass

    def induction_clean(self):
        # ── M13: L4 dissolved — τ IS the real-time self-observation ──
        # Active frames feed the window for structural cooccurrence → L3 chains.
        # No centroid, no dw/dt, no explicit meta-frames. The frame economy
        # observes itself through every merge (sig rewrite, gid chain update, τ breath).
        active = [f for f in self.frames if f.weight > 1 * self.tau_scale]
        if active:
            fids = [f.fid for f in active]
            feed_time = self._step_counter
            for fid in fids:
                fid_sig = f'fid_{fid}'
                if fid_sig not in self._sig_to_gid:
                    self._sig_to_gid[fid_sig] = _hash_str(fid_sig)
                self._window.append((fid_sig, feed_time, self._zero_vec(), self.tau))
                if len(self._window) > self._win_max:
                    self._window.pop(0)
            for i in range(len(fids)):
                for j in range(i + 1, len(fids)):
                    ckey = tuple(sorted([f'fid_{fids[i]}', f'fid_{fids[j]}']))
                    self._cooccur[ckey] = self._cooccur.get(ckey, 0) + 1

        self._chain_count = 0
        induction_decay_unmerged = math.exp(-GAMMA * int(GI))  # 1/(γ×GI)⁻¹ → GI×γ decay for unmerged frames
        induction_decay_low = math.exp(-GAMMA)  # γ decay for low-merge frames
        for f in self.frames:
            self.total_weight -= f.weight
            if f.merged == 0:
                f.weight *= induction_decay_unmerged
            elif f.merged < 3:
                f.weight *= induction_decay_low
            f.weight = max(1.0, f.weight)
            self.total_weight += f.weight
            f.age += 1
        self.frames.sort(key=lambda x: (
            x.weight - x.age * GAMMA
            - (abs(self.tau - getattr(x, 'tau', TAU_0)) * self.gamma_tau if self.tau_in_prune else 0)
        ), reverse=True)
        half = max(1, len(self.frames) // 2)
        for f in self.frames[half:]:
            self.total_weight -= f.weight
            self._fid_to_frame.pop(f.fid, None)  # M11: cleanup pruned frames
        self.frames = self.frames[:half]
        alive_fids = {f.fid for f in self.frames}
        for fid in list(self._weight_history.keys()):
            if fid not in alive_fids:
                del self._weight_history[fid]
        # ── M11: cleanup stale sig_cache entries for pruned frames ──
        stale_sigs = [s for s, fid in self._sig_cache.items() if fid not in alive_fids]
        for s in stale_sigs:
            del self._sig_cache[s]
        # ── Precipitation: survivors age one more cycle ──
        for f in self.frames:
            f.survival_cycles += 1

        self._form_chains()

        # ── Housekeeping ──
        self._multiverse = self._multiverse[-1:]  # keep at most 1 branch world
        self._pengshu_events = self._pengshu_events[-200:]  # trim unbounded growth
        # Recalibrate total_weight from actual frame weights (drift guard)
        computed = sum(f.weight for f in self.frames)
        if abs(computed - self.total_weight) > 0.01:
            self.total_weight = computed

    # ── Endogenous τ evolution ──

    def _update_tau(self):
        """Evolve τ based on prediction accuracy + frame-economy stress.

        τ rises when the frame economy is under stress (crowded, inefficient)
        AND predictions are failing. τ falls when the economy is healthy.

        Harm frames from other Selves enter through observe() → κ_τ modulates
        merge/cooccur/prune → stress emerges endogenously → τ differentiates
        across κ_τ without external pressure injection.

        Inertia (TAU_ADAPT_RATE < GAMMA) means τ changes slower than
        frame weights — the system's self-assessment has momentum.
        """
        acc = self._last_accuracy
        endogenous_pressure = max(0, self.stress - TAU_0) * self.gamma_tau * (1.0 - TAU_0)  # γ_τ×(1-τ₀)=γ_τ×0.4
        target_tau = 1.0 - acc + endogenous_pressure
        target_tau = max(GAMMA, min(1.0, target_tau))  # floor = γ, ceiling = 1

        self.tau += (target_tau - self.tau) * TAU_ADAPT_RATE
        self._tau_history.append((self._step_counter, self.tau))
        if len(self._tau_history) > 200:
            self._tau_history.pop(0)
        new_phase = self.phase
        self._phase_steps[new_phase] = self._phase_steps.get(new_phase, 0) + 1
        if new_phase != self._last_phase:
            self._phase_transitions.append(
                (self._step_counter, self._last_phase, new_phase))
            self._last_phase = new_phase

    # ── Prediction processing with τ update ──

    def process_prediction(self, actual_sig):
        if not actual_sig or actual_sig == 'self_obs':
            return None

        # ── When LOCKED, the bridge is closed — no predictions ──
        # GEME legacy: closed bridge → no errors → accuracy treated as 1.0 → τ falls.
        # This is NOT a "falsified perfect accuracy" — it is the self-correcting
        # mechanism: closed perception naturally relaxes vigilance.
        if self.phase == Phase.LOCKED:
            self._last_accuracy = 1.0  # bridge closed = no errors
            self._update_tau()
            return {'predicted': None, 'actual': actual_sig,
                    'confidence': 0.0,
                    'accuracy': 1.0, 'locked': True}
        predicted, conf = self.predict_next()
        if predicted is None:
            return None
        if conf > 0:
            self._confidences.append(conf)
            if len(self._confidences) > 100:
                self._confidences.pop(0)
            if len(self._confidences) >= 20:
                sorted_conf = sorted(self._confidences)
                self._conf_threshold = sorted_conf[max(0, len(sorted_conf) // 4)]
        if conf < self._conf_threshold:
            return None
        self._pred_total += 1
        if predicted == actual_sig:
            self._prediction_accuracy.append(1.0)
        else:
            self._prediction_accuracy.append(0.0)
            self._pred_errors += 1
            err_str = f"pred_err_{conf:.2f}_{predicted[:8]}_{actual_sig[:8]}"
            # P1: O(1) cached lookup — avoid O(N) scan
            match = []
            fid = self._sys_fids.get('pred_err')
            if fid is not None and fid in self._fid_to_frame:
                match = [self._fid_to_frame[fid]]
            else:
                match = [f for f in self.frames
                        if 'pred_err' in (getattr(f, 'sig_full', None) or f.sig)]
            if not match:
                dummy_vec = self._zero_vec()  # system frame — no borrowed content
                if len(self.frames) >= self.capacity:
                    self.frames.sort(key=lambda x: x.weight - x.age * GAMMA * 2 - (abs(self.tau - getattr(x, 'tau', TAU_0)) * self.gamma_tau if self.tau_in_prune else 0))
                    r = self.frames.pop(0)
                    self.total_weight -= r.weight
                    self._fid_to_frame.pop(r.fid, None)
                nf = GeruonFrame(dummy_vec, weight=1.0/(GAMMA*int(GI)), sig=err_str, layer="L4", tau=self.tau)  # 1/(γ×GI)=5
                self.frames.append(nf)
                self.total_weight += 5.0
                self._track_frame_sig(nf)
                self._sys_fids['pred_err'] = nf.fid
        if len(self._prediction_accuracy) > 50:
            self._prediction_accuracy.pop(0)

        # ── Doubt mode detection ──
        doubt_on_threshold = TAU_0
        doubt_off_threshold = 1.0 - GAMMA * 3.0
        healthy_acc_threshold = 1.0 - GAMMA * 4.0
        recent_acc = (sum(self._prediction_accuracy[-10:])
                      / len(self._prediction_accuracy[-10:])
                      if self._prediction_accuracy else 1.0)
        # Track peak accuracy for "was healthy" check
        if not hasattr(self, '_peak_accuracy'):
            self._peak_accuracy = 0.0
        if recent_acc > self._peak_accuracy:
            self._peak_accuracy = recent_acc

        if (not self._doubt_mode and len(self._prediction_accuracy) >= 10
                and recent_acc < doubt_on_threshold
                and self._peak_accuracy > healthy_acc_threshold):
            self._doubt_mode = True
            doubt_str = f"sys_doubt_acc_{recent_acc:.2f}"
            # P1: O(1) cached lookup
            match = []
            fid = self._sys_fids.get('sys_doubt')
            if fid is not None and fid in self._fid_to_frame:
                match = [self._fid_to_frame[fid]]
            else:
                match = [f for f in self.frames
                        if 'sys_doubt' in (getattr(f, 'sig_full', None) or f.sig)]
            if not match:
                dummy_vec = self._zero_vec()  # system frame — no borrowed content
                if len(self.frames) >= self.capacity:
                    self.frames.sort(key=lambda x: x.weight - x.age * GAMMA * 2 - (abs(self.tau - getattr(x, 'tau', TAU_0)) * self.gamma_tau if self.tau_in_prune else 0))
                    r = self.frames.pop(0)
                    self.total_weight -= r.weight
                    self._fid_to_frame.pop(r.fid, None)
                nf = GeruonFrame(dummy_vec, weight=2.0/(GAMMA*int(GI)), sig=doubt_str, layer="L6", tau=self.tau)  # 2/(γ×GI)=10
                self.frames.append(nf)
                self.total_weight += 10.0
                self._track_frame_sig(nf)
                self._sys_fids['sys_doubt'] = nf.fid
        elif self._doubt_mode and recent_acc > doubt_off_threshold:
            self._doubt_mode = False
            self._peak_accuracy = recent_acc  # reset peak for next cycle

        self._last_accuracy = recent_acc
        self._update_tau()

        # ── Precipitation: activation tracking ──
        # L1: activated if its sig appears in recent window
        # L2/L3: activated if merged (weight increased) — their sigs never enter window
        recent = set(entry[0] for entry in self._window[-10:])
        for f in self.frames:
            ly = getattr(f, 'layer', 'L1')
            if ly == 'L1':
                if f.sig in recent or getattr(f, 'sig_full', '') in recent:
                    f.activations += 1
            else:
                # L2+: use merge count as activation proxy
                f.activations = f.merged

        # ── 碰数 detection ──
        self._pengshu_detect()

        return {'predicted': predicted, 'actual': actual_sig,
                'confidence': conf, 'accuracy': recent_acc}

    def _pengshu_detect(self):
        """Four-condition 碰数 (boundary encounter) detector.

        Conditions (all must hold):
        (1) circularity — at least one gid in prediction path has circular refs
        (2) activation — self-referential frame participates in prediction path
        (3) phase boundary — phase is CRITICAL or LOCKED
        (4) escalation — dτ/dt > 0 (τ rising) or at ceiling (τ≥1.0 LOCKED/CRITICAL)

        Note: doubt (prediction accuracy decline) is L5→L6 conscious-layer,
        not a prerequisite for 碰数. 碰数 is a structural event at L3↔L4 —
        the system touches its Gödel boundary whether or not it "feels" it.

        Debounce: cooldown of 2×GI steps between successive 碰数 events.
        """
        if self._pengshu_cooldown > 0:
            self._pengshu_cooldown -= 1
            return

        # (1) circularity in prediction path
        if not self._circular_refs or not self._prediction_path_gids:
            return
        circular_in_path = [gid for gid in self._prediction_path_gids
                           if gid in self._circular_refs]
        if not circular_in_path:
            return

        # (2) self-referential frame in path (satisfied by circular_in_path non-empty)

        # (3) phase boundary
        phase = self.phase
        if phase not in (Phase.CRITICAL, Phase.LOCKED):
            return

        # (4) escalation — τ is rising, OR already at boundary ceiling
        if self.dtaudt <= 0 and not (self.tau >= 1.0 and phase in (Phase.CRITICAL, Phase.LOCKED)):
            return

        # All four conditions met → 碰数
        # Use HEAVIEST circular frame in prediction path (not first found).
        # P1: O(1) via _sig_index (gid→frame) — avoids O(|circ|×N) scan.
        best_gid = circular_in_path[0]
        best_w = 0
        for gid in circular_in_path:
            f = self._sig_index.get(gid)
            if f is not None and f.weight > best_w:
                best_w = f.weight
                best_gid = gid
        self._pengshu_events.append({
            'step': self._step_counter,
            'gid': best_gid % 1000000,
            'phase': phase.value,
            'tau': round(self.tau, 4),
            'dtaudt': round(self.dtaudt, 6),
            'chain': [g % 1000000 for g in
                      self._circular_refs.get(best_gid, (0, ()))[1]],
        })
        self._pengshu_cooldown = 2 * int(GI)  # 2×GI = 8 — M12 structural constant

    def precipitate_candidates(self) -> list:
        """Find frames that meet all precipitation conditions.

        A frame precipitates when:
        1. It has survived enough induction cycles (cross-phase survival)
        2. It has been activated in prediction paths (actually used)
        3. It is structurally stable (d(w)/dt near zero)

        These frames are the "sediment" — externalizable knowledge traces.
        """
        candidates = []
        for f in self.frames:
            if f.precipitated:
                continue
            if f.survival_cycles < PRECIPITATE_MIN_SURVIVAL:
                continue
            if f.activations < PRECIPITATE_MIN_ACTIVATIONS:
                continue
            if not self.is_meta_stable(f.fid):
                continue
            candidates.append(f)
        return candidates

    def precipitate(self) -> int:
        """Mark qualifying frames as precipitated. Returns count."""
        count = 0
        for f in self.precipitate_candidates():
            f.precipitated = True
            count += 1
        return count

    # ── Metrics and properties ──

    @property
    def efficiency(self):
        if not self.frames or self.total_weight == 0:
            return 1.0
        avg = self.total_weight / len(self.frames)
        dev = sum(abs(f.weight - avg) for f in self.frames) / (len(self.frames) * max(avg, 0.001))
        return max(0.01, 1.0 - min(1.0, dev))

    @property
    def utilization(self):
        return len(self.frames) / self.capacity

    @property
    def stress(self):
        return self.utilization * (1.0 - self.efficiency)

    def structural_entropy(self):
        if not self.frames or self.total_weight <= 0:
            return 0.0
        return -sum((f.weight / self.total_weight) * math.log2(f.weight / self.total_weight)
                    for f in self.frames if f.weight > 0)

    def count_L4_frames(self, min_weight_ratio=1.5):
        l4 = [f for f in self.frames
              if getattr(f, 'layer', 'L1') in ('L2', 'L3', 'L4', 'L6')]
        if not l4:
            return 0
        w = sorted([f.weight for f in l4], reverse=True)
        avg = sum(w) / len(w) if w else 1
        return sum(1 for x in w if x >= avg * 1.5)

    def count_by_layer(self):
        counts = {}
        for f in self.frames:
            l = getattr(f, 'layer', "L1")
            counts[l] = counts.get(l, 0) + 1
        return counts

    def _sig_matches(self, f, sig):
        """Check if a frame matches a signature string.
        M11: LOCKED brake REMOVED — cache (_find_frames_by_sig) handles energy conservation."""
        if f.sig == sig or getattr(f, 'sig_full', '') == sig:
            return True
        key = self._sig_to_key.get(sig)
        ss = getattr(f, 'struct_sig', None)
        if key is not None and ss is not None and key == ss.struct_key:
            return True
        return False

    def _sig_layer(self, sig):
        key = self._sig_to_key.get(sig)
        if key and key in self._sig_index:
            return getattr(self._sig_index[key], 'layer', 'L1')
        frames = self._find_frames_by_sig(sig)
        if frames:
            return getattr(frames[0], 'layer', 'L1')
        return 'L1'

    def mutual_information_phi_X(self):
        phi_keys, x_keys = set(), set()
        for (sa, sb) in self._cooccur:
            la = self._sig_layer(sa); lb = self._sig_layer(sb)
            (phi_keys if la in ('L2','L3','L4','L6') else x_keys).add(sa)
            (phi_keys if lb in ('L2','L3','L4','L6') else x_keys).add(sb)
        if not phi_keys or not x_keys:
            return 0.0
        total_all = sum(c for c in self._cooccur.values())
        if total_all == 0:
            return 0.0
        p_phi_cache = {}
        p_x_cache = {}
        for sig in phi_keys:
            p_phi_cache[sig] = sum(c for (sa, sb), c in self._cooccur.items()
                                   if sa == sig or sb == sig) / total_all
        for sig in x_keys:
            p_x_cache[sig] = sum(c for (sa, sb), c in self._cooccur.items()
                                 if sa == sig or sb == sig) / total_all
        mi = 0.0
        for (sa, sb), c in self._cooccur.items():
            in_phi_a = sa in phi_keys
            in_phi_b = sb in phi_keys
            in_x_a = sa in x_keys
            in_x_b = sb in x_keys
            if in_phi_a and in_x_b:
                p_joint = c / total_all
                p_phi = p_phi_cache[sa]
                p_x = p_x_cache[sb]
                if p_joint > 0 and p_phi > 0 and p_x > 0:
                    mi += p_joint * math.log2(p_joint / (p_phi * p_x))
            elif in_x_a and in_phi_b:
                p_joint = c / total_all
                p_phi = p_phi_cache[sb]
                p_x = p_x_cache[sa]
                if p_joint > 0 and p_phi > 0 and p_x > 0:
                    mi += p_joint * math.log2(p_joint / (p_phi * p_x))
        return max(0.0, mi)

    def compute_derivatives(self):
        derivs = {}
        for fid, history in self._weight_history.items():
            if len(history) < 5:
                continue
            recent = history[-10:] if len(history) > 10 else history
            n = len(recent)
            xs = [h[0] for h in recent]
            ys = [h[1] for h in recent]
            x_mean = sum(xs) / n
            y_mean = sum(ys) / n
            num = sum((xs[i] - x_mean) * (ys[i] - y_mean) for i in range(n))
            den = sum((xs[i] - x_mean) ** 2 for i in range(n))
            derivs[fid] = num / max(den, 0.001)
        return derivs

    def is_meta_stable(self, fid):
        derivs = self.compute_derivatives()
        if fid in derivs:
            return abs(derivs[fid]) < GAMMA * 0.2
        # No derivative data: frame never merged.
        # Stable if it has survived at least one induction cycle
        # (it persisted without needing to merge — structural fit).
        for f in self.frames:
            if f.fid == fid:
                return f.survival_cycles >= 1
        return False

    def predict_next(self):
        if len(self._window) < int(GI) - 1:  # GI-1=3 — minimum window for prediction
            self._prediction_path_gids = []
            return None, 0.0
        recent = [e for e in self._window if e[0] != 'self_obs']
        if len(recent) < 2:
            self._prediction_path_gids = []
            return None, 0.0
        # τ-context: sig → most recent τ in window
        tau_of = {}
        for e in self._window:
            tau_of[e[0]] = e[3]  # last wins
        tau_now = self.tau
        ctx_sigs = [e[0] for e in recent[-2:]]
        scores = {}
        path_gids = set()
        for sig in ctx_sigs:
            gid = self._sig_to_gid.get(sig)
            if gid is not None:
                path_gids.add(gid)
            tau_sig = tau_of.get(sig, tau_now)
            for (sa, sb), c in self._cooccur.items():
                if sa == sig and sb not in ctx_sigs:
                    tau_sb = tau_of.get(sb, tau_now)
                    tw = 1.0 - self.kappa_tau * abs(tau_sig - tau_sb)
                    tw = max(0.1, min(1.0, tw))
                    scores[sb] = scores.get(sb, 0) + c * tw
                    gid_b = self._sig_to_gid.get(sb)
                    if gid_b is not None:
                        path_gids.add(gid_b)
                elif sb == sig and sa not in ctx_sigs:
                    tau_sa = tau_of.get(sa, tau_now)
                    tw = 1.0 - self.kappa_tau * abs(tau_sig - tau_sa)
                    tw = max(0.1, min(1.0, tw))
                    scores[sa] = scores.get(sa, 0) + c * tw
                    gid_a = self._sig_to_gid.get(sa)
                    if gid_a is not None:
                        path_gids.add(gid_a)
        if not scores:
            self._prediction_path_gids = []
            return None, 0.0
        best = max(scores, key=scores.get)
        total = sum(scores.values())
        conf = scores[best] / max(total, 1)
        gid_best = self._sig_to_gid.get(best)
        if gid_best is not None:
            path_gids.add(gid_best)
        self._prediction_path_gids = list(path_gids)
        return best, conf

    def predict_next_vec(self):
        """Predict the NEXT VECTOR (not sig) from cooccurrence patterns.

        Unlike predict_next() which tries to match exact sig strings,
        this returns a weighted centroid of what vectors usually follow
        the recent context. Confidence = inverse variance of predictions.
        Returns (vector_tuple, confidence) or (None, 0.0).
        """
        if len(self._window) < int(GI) - 1:  # GI-1=3 — minimum window for prediction
            return None, 0.0
        recent = [e for e in self._window if e[0] != 'self_obs']
        if len(recent) < 2:
            return None, 0.0
        tau_of = {}
        for e in self._window:
            tau_of[e[0]] = e[3]
        tau_now = self.tau
        ctx_sigs = [e[0] for e in recent[-2:]]

        # Collect candidate vectors from frames that co-occur with context
        cand_vecs = []
        cand_weights = []
        for sig in ctx_sigs:
            tau_sig = tau_of.get(sig, tau_now)
            for (sa, sb), c in self._cooccur.items():
                tw = 1.0
                if sa == sig and sb not in ctx_sigs:
                    tau_sb = tau_of.get(sb, tau_now)
                    tw = 1.0 - self.kappa_tau * abs(tau_sig - tau_sb)
                    tw = max(0.1, min(1.0, tw))
                    # Find frame for sb
                    fid = self._sig_cache.get(sb) or (self._sig_to_gid.get(sb) and self._sig_index.get(self._sig_to_gid[sb]))
                    if fid and fid in self._fid_to_frame:
                        f = self._fid_to_frame[fid]
                        cand_vecs.append(f.vec)
                        cand_weights.append(c * tw)
                elif sb == sig and sa not in ctx_sigs:
                    tau_sa = tau_of.get(sa, tau_now)
                    tw = 1.0 - self.kappa_tau * abs(tau_sig - tau_sa)
                    tw = max(0.1, min(1.0, tw))
                    fid = self._sig_cache.get(sa) or (self._sig_to_gid.get(sa) and self._sig_index.get(self._sig_to_gid[sa]))
                    if fid and fid in self._fid_to_frame:
                        f = self._fid_to_frame[fid]
                        cand_vecs.append(f.vec)
                        cand_weights.append(c * tw)

        if not cand_vecs:
            return None, 0.0

        dim = len(cand_vecs[0])
        total_w = sum(cand_weights)
        centroid = tuple(
            sum(v[j] * cand_weights[i] for i, v in enumerate(cand_vecs)) / total_w
            for j in range(dim))

        # Confidence: inverse of weighted variance
        variance = sum(
            cand_weights[i] * sum((v[j] - centroid[j])**2 for j in range(dim))
            for i, v in enumerate(cand_vecs)) / total_w
        conf = 1.0 / (1.0 + math.sqrt(variance))

        return centroid, conf

    def metrics(self):
        w = sorted([f.weight for f in self.frames], reverse=True)
        return {
            "frame_count": len(self.frames),
            "capacity": self.capacity,
            "total_weight": round(self.total_weight, 2),
            "efficiency": round(self.efficiency, 4),
            "utilization": round(self.utilization, 4),
            "stress": round(self.stress, 4),
            "structural_entropy": round(self.structural_entropy(), 4),
            "L4_frame_count": self.count_L4_frames(),
            "top_weights": [round(x, 1) for x in w[:5]],
            "I(phi;X)": round(self.mutual_information_phi_X(), 6),
            "SR-eff": round(self.mutual_information_phi_X() / max(self.tau, 0.001), 6),
            "assoc_frames": self._assoc_frames,
            "pred_total": self._pred_total,
            "pred_accuracy": round(
                sum(self._prediction_accuracy[-20:])
                / max(len(self._prediction_accuracy[-20:]), 1), 3)
                if self._prediction_accuracy else 0.0,
            "conf_threshold": round(self._conf_threshold, 4),
            "doubt_mode": self._doubt_mode,
            "derivative_frames": len(self._derivative_frames),
            "L4_meta_active": len([f for f in self.frames
                                   if getattr(f, 'layer', 'L1') == 'L4']),
            "layers": self.count_by_layer(),
            # ── Geruon-specific ──
            "vec_dim": self.vec_dim,
            "tau": round(self.tau, 4),
            "dtaudt": round(self.dtaudt, 6),
            "phase": self.phase.value,
            "phase_steps": {k.value: v for k, v in self._phase_steps.items()},
            "phase_transitions": len(self._phase_transitions),
            # ── StructuralSig: circularity ──
            "circular_refs": len(self._circular_refs),
            "circular_gids": [hash(key) % 1000000 for key in self._circular_refs],
            # ── M11: Landauer bill ──
            "codex_hits": self._codex_hits,
            "codex_misses": self._codex_misses,
            "codex_hit_rate": self._codex_bill()['rate'],
            "sig_cache_size": len(self._sig_cache),
            "landauer_skips": getattr(self, '_landauer_skips', 0),
            # ── 碰数 ──
            "pengshu_count": len(self._pengshu_events),
            "pengshu_last": self._pengshu_events[-1] if self._pengshu_events else None,
            # ── Precipitation ──
            "precipitated": sum(1 for f in self.frames if f.precipitated),
            "precipitate_candidates": len(self.precipitate_candidates()),
            # ── Faraday readings ──
            "F": self._compute_F(),
            "centroid_displacement": round(self._centroid_displacement, 6),
            "wit_hits": self._wit_hits,
        }

    def _compute_F(self):
        """Field curvature: 1 − H(w)/Hmax. 0 = flat, 1 = fully concentrated."""
        H = self.structural_entropy()
        n = max(len(self.frames), 1)
        H_max = math.log2(n)
        return round(1.0 - H / H_max, 6) if H_max > 0 else 0.0


# ──────────────────────────────────────────────────────────────────
# Geruon — top-level API
# ──────────────────────────────────────────────────────────────────
class Geruon:
    """Self-referential primitive with endogenous time perception.

    Key additions over GEME:
      - vec_dim: configurable vector dimension (default 16, not 27)
      - .tau: current endogenous τ (evolves with prediction history)
      - .phase: current breathing phase
      - .phase_output(): (anomaly, phase) encoded as vec_dim vector
    """

    def __init__(self, vec_dim=VEC_DIM_DEFAULT, memory_cap=10, cooccur_window=None,
                 cooccur_thresh=0.25, max_chains=5, time_window_size=0,
                 codex=None, bias_field=None, bias_weight=None,
                 kappa_tau=None, gamma_tau=None, structon=None):
        if bias_weight is None:
            bias_weight = GAMMA          # default blend = γ
        if kappa_tau is None:
            kappa_tau = _KAPPA_TAU_DEFAULT
        if gamma_tau is None:
            gamma_tau = kappa_tau * GAMMA   # derived from κ_τ: time pruning = coupling × decay
        self.vec_dim = vec_dim
        self.structon = structon          # minimum detectable centroid displacement (Faraday)
        self.codex = codex
        self.bias_field = bias_field        # content-layer gradient field
        self.time_field = None               # time-layer gradient field (set separately)
        self.bias_weight = bias_weight
        self.kappa_tau = kappa_tau
        self.gamma_tau = gamma_tau
        self._codex_novelties = []
        self._last_input_vec = None
        self.memory = GeruonMemory(
            vec_dim=vec_dim, capacity=memory_cap,
            cooccur_window=cooccur_window, cooccur_thresh=cooccur_thresh,
            max_chains=max_chains,
            kappa_tau=kappa_tau, gamma_tau=gamma_tau)
        if self.bias_field is not None and not self.bias_field.is_empty():
            self.bias_field.seed_frames(self.memory, count=min(int(GI) + 1, memory_cap//3))  # GI+1=5
        if self.time_field is not None and not self.time_field.is_empty():
            self.time_field.seed_frames(self.memory, count=min(3, memory_cap//4))
        self._stress_accum = 0.0
        self._induction_threshold = TAU_0
        self.frame_count = 0
        self._last_induction = 0
        self._input_count = 0
        self.time_window_size = time_window_size
        self._inputs_in_window = 0
        self.vocab_mode = False
        self.vocab = {}
        self._decoded_signatures = {}

    # ── Delegated properties ──
    @property
    def tau(self) -> float:
        return self.memory.tau

    @property
    def phase(self) -> Phase:
        return self.memory.phase

    @property
    def dtaudt(self) -> float:
        return self.memory.dtaudt

    # ── Phase-aware output ──

    def anomaly_score(self) -> float:
        m = self.metrics()
        # Anomaly levels anchored to GEME thresholds:
        # 1−4γ=0.80 healthy, τ₀=0.60 doubt_on, 4γ=0.20 critical floor
        if m.get('doubt_mode', False):
            return TAU_0 + GAMMA * 4        # 0.80 — systemic doubt (= DOUBT_OFF baseline)
        acc = m.get('pred_accuracy', 0.0)
        if acc > 1.0 - GAMMA * 4:           # > 0.80 — healthy
            return GAMMA * 2                 # 0.10
        elif acc > TAU_0 - GAMMA * 2:        # > 0.50 — mild anomaly
            return TAU_0 * 0.5               # 0.30
        elif acc > GAMMA * 4:                # > 0.20 — elevated
            return TAU_0                     # 0.60
        else:
            return TAU_0 + GAMMA * 4         # 0.80 — critical (matches doubt threshold)

    def arrow_output(self) -> tuple:
        """Refraction output — how THIS Self absorbed the last input.

        Returns the residual (input − existing_match) blended with phase.
        This captures what this Self uniquely ADDED — its refractive index
        for this specific event — rather than the accumulated consensus.
        If no merge happened (new frame created), returns the input itself.
        """
        frames = self.memory.frames
        if not frames or not self._last_input_vec:
            return tuple([0.0] * self.vec_dim)
        input_vec = self._last_input_vec
        # Find the frame that was merged (if any)
        last_fid = self.memory._last_merge_fid
        merged_frame = None
        for f in frames:
            if f.fid == last_fid:
                merged_frame = f
                break
        if merged_frame is not None and merged_frame.merged > 0:
            # Residual: what was unique about this input vs what I already had
            residual = [input_vec[j] - merged_frame.vec[j] for j in range(self.vec_dim)]
        else:
            # New frame — the input itself IS the refraction
            residual = list(input_vec)
        norm = math.sqrt(sum(v*v for v in residual))
        if norm > 0.001:
            residual = [v / norm for v in residual]
        return tuple(residual)

    def centroid_output(self) -> tuple:
        """Legacy: full centroid output — what the system knows (summary)."""
        frames = self.memory.frames
        if not frames:
            return tuple([0.0] * self.vec_dim)
        tw = sum(f.weight for f in frames)
        return tuple(
            sum(f.vec[j] * f.weight for f in frames) / max(tw, 0.001)
            for j in range(self.vec_dim))

    def phase_output(self) -> tuple:
        """Legacy: sparse phase vector. Use arrow_output() for fused content-time."""
        return phase_encode(self.anomaly_score(), self.phase, self.vec_dim)

    def phase_state(self) -> dict:
        """Compact phase summary for external tracking."""
        return {
            'tau': round(self.tau, 4),
            'dtaudt': round(self.dtaudt, 6),
            'phase': self.phase.value,
            'anomaly': round(self.anomaly_score(), 3),
            'phase_transitions': self.memory._phase_transitions[-3:]
                if self.memory._phase_transitions else [],
        }

    # ── Core processing ──

    def process_sig(self, formula, sig=None):
        """DEPRECATED: GEME formula-language wrapper. Use process_vec() instead."""
        if sig is None:
            sig = structural_signature(formula)
        return self.process_vec(symbol_vector(formula), sig)

    def process_vec(self, vec, sig, src=""):
        vec = list(vec)  # defensive copy — prevents mutation of caller's data
        # ── Dimension guard: reject or pad mismatched vectors ──
        if len(vec) != self.vec_dim:
            if len(vec) < self.vec_dim:
                vec.extend([0.0] * (self.vec_dim - len(vec)))
            else:
                vec = vec[:self.vec_dim]
        # ── Dual-field continuous modulation ──
        # Self-boundary (BGM cliff): phase-gated bias_weight
        # When cliff snaps shut, the Self stops listening to the shared field.
        gate = self.memory.cliff_gate
        effective_bw = self.bias_weight * gate
        if self.bias_field is not None and not self.bias_field.is_empty():
            vec = self.bias_field.blend_into(vec, weight=effective_bw)
        if self.time_field is not None and not self.time_field.is_empty():
            vec = self.time_field.blend_into(vec, weight=effective_bw * TAU_0 * 0.5)  # τ₀/2=0.30 — time-field blend decay

        # ── Self-level Codex query: inherited vocabulary ──
        # Cavity carries Codex from previous generation. Query when novel.
        if self.codex is not None and len(self.codex) > 0:
            best_sym, best_vec, best_dist = self.codex.nearest(vec)
            if best_vec is not None and best_dist < 1.0:
                vec = self.codex.blend_in(vec, best_dist, weight=GAMMA)

        self.frame_count += 1
        self._input_count += 1
        self._last_input_vec = list(vec)  # save for refraction output

        self.memory.observe(vec, sig, src)

        # Multiverse branching
        if self.memory._multiverse_enabled and self.memory._multiverse:
            # P1: 1.0 + γ×GI×(1+τ₀) = 1.0 + 0.05×4×1.6 = 1.32
            # Dimension penalty for multiverse branching — anchored to δ/γ/τ₀/GI
            multiverse_dim_penalty = DELTA * (1.0 + GAMMA * GI * (1.0 + TAU_0))
            new_mv = []
            for branch_frames, step_branched, branch_id in self.memory._multiverse:
                if len(new_mv) >= 20:
                    break
                bi = -1
                bd = float('inf')
                for i, f in enumerate(branch_frames):
                    dl = min(len(vec), len(f.vec))
                    d = sum((vec[j] - f.vec[j]) ** 2 for j in range(dl))
                    d += abs(len(vec) - len(f.vec)) * multiverse_dim_penalty
                    if d < bd:
                        bd = d
                        bi = i
                th = self.memory._adaptive_thresh() or DELTA
                if bi >= 0 and bd <= th * th:
                    f = branch_frames[bi]
                    f.vec = tuple((f.vec[j] * f.weight + vec[j]) / (f.weight + 1)
                                  for j in range(len(vec)))
                    f.weight += 1.0
                    f.merged += 1
                else:
                    nf = GeruonFrame(vec, 1.0, sig, src)
                    branch_frames.append(nf)
                new_mv.append((branch_frames, step_branched, branch_id))
            self.memory._multiverse = new_mv

        stress = self.memory.stress
        ind = self._induction_step(stress)
        # ── Faraday: centroid displacement tracking ──
        self.memory._update_centroid_tracking(self.structon)
        return {"frame": self.frame_count, "mem": len(self.memory.frames),
                "eff": round(self.memory.efficiency, 4),
                "stress": round(stress, 4),
                "induction": ind,
                "thresh": self.memory._merge_thresh_val}

    def _induction_step(self, stress):
        self._stress_accum += stress * 0.1
        fired = False
        if self.time_window_size > 0:
            self._inputs_in_window += 1
            if self._inputs_in_window >= self.time_window_size:
                self.consolidate()
                self._inputs_in_window = 0
                fired = True
        elif self._stress_accum > TAU_0:
            cd = self.frame_count - self._last_induction
            guard = max(int(GI) + 1, int(self.memory.capacity / max(self.memory.utilization, 0.01)))  # GI+1=5 — induction floor
            if cd >= guard:
                self.consolidate()
                fired = True
        return fired

    def consolidate(self):
        self.memory.induction_clean()
        if self.vocab_mode:
            self.promote_to_vocab()
        self.memory._chain_count = 0
        self._stress_accum = 0.0
        self._last_induction = self.frame_count

    # ── Input / output ──

    def input(self, data, sig_hint=""):
        """DEPRECATED: convenience wrapper with legacy string support.
        Use process_vec() directly for gradient-pure input."""
        if isinstance(data, str):
            if self.codex is not None:
                vec = [0.0] * self.vec_dim
                for ch in data:
                    cv = self.codex.lookup(ch)
                    if cv is not None:
                        for j in range(min(len(cv), self.vec_dim)):
                            vec[j] += cv[j]
                    else:
                        self._codex_novelties.append(
                            (self.frame_count, ch))
                norm = math.sqrt(sum(x * x for x in vec))
                if norm > 0:
                    vec = [x / norm for x in vec]
                sig = sig_hint or data[:8]
                return self.process_vec(vec, sig)
            else:
                # No codex — simple hash fallback (legacy)
                char_counts = [0.0] * self.vec_dim
                for ch in data:
                    idx = ord(ch) % self.vec_dim
                    char_counts[idx] += 1.0
                norm = math.sqrt(sum(x * x for x in char_counts))
                if norm > 0:
                    char_counts = [x / norm for x in char_counts]
                sig = sig_hint or data[:8]
                return self.process_vec(char_counts, sig)
        elif isinstance(data, (list, tuple)):
            sig = sig_hint or 'vec'
            return self.process_vec(list(data), sig)
        elif isinstance(data, (int, float)):
            v = [0.0] * self.vec_dim
            v[int(data) % self.vec_dim] = 1.0
            sig = sig_hint or str(data)
            return self.process_vec(v, sig)
        else:
            raise TypeError(f"Unsupported input type: {type(data)}")

    def predict_next(self):
        pred, conf = self.memory.predict_next()
        return (pred, round(conf, 3)) if pred else (None, 0.0)

    def predict_next_vec(self):
        return self.memory.predict_next_vec()

    def metrics(self):
        m = self.memory.metrics()
        m["frame_count_total"] = self.frame_count
        m["input_count"] = self._input_count
        m["induction_threshold"] = self._induction_threshold
        if self._input_count > 0:
            m["compression_ratio"] = round(
                self._input_count / max(len(self.memory.frames), 1), 1)
        # Codex info
        m["has_codex"] = self.codex is not None
        m["codex_size"] = len(self.codex) if self.codex else 0
        m["codex_generation"] = self.codex._generation if self.codex else 0
        m["codex_novelties"] = len(self._codex_novelties)
        m["has_bias_field"] = self.bias_field is not None
        m["bias_count"] = self.bias_field._count if self.bias_field else 0
        # M11: Landauer bill
        m["codex_hits"] = self.memory._codex_hits
        m["codex_misses"] = self.memory._codex_misses
        m["codex_hit_rate"] = self.memory._codex_bill()['rate']
        # Faraday: wit rate
        if self._input_count > 0:
            m["wit_rate"] = round(self.memory._wit_hits / self._input_count, 4)
        else:
            m["wit_rate"] = 0.0
        return m

    def enrich(self):
        """Deposit precipitated frames into externalized memory.

        Two modes coexist:
        - Codex (symbolic): named entries for lookup
        - BiasField (gradient): unnamed vector accumulation — "GABA mode"

        The gradient mode is the EE-native form of externalization:
        no names, no lookup, just structural bias inherited by the next
        generation as initial frame economy conditions.

        Returns number of frames deposited.
        """
        newly = self.memory.precipitate()
        count = 0
        for f in self.memory.frames:
            if not f.precipitated or f._externalized:
                continue
            f._externalized = True
            # Route: time_obs frames → time_field, others → bias_field
            is_time = 'time_' in (getattr(f, 'sig_full', '') or f.sig)
            if is_time and self.time_field is not None:
                self.time_field.deposit_frame(f)
            elif self.bias_field is not None:
                self.bias_field.deposit_frame(f)
            # Symbol mode: also add to codex if available
            if self.codex is not None:
                sym = f"deposit_{f.struct_sig.gid % 1000000}"
                if self.codex.is_novel(sym):
                    self.codex.add(sym, f.vec,
                                   source=f"precip_f{f.fid}_sc{f.survival_cycles}_act{f.activations}")
            count += 1
        if newly > 0 and self.codex is not None:
            self.codex.new_generation()
        return count

    def state(self):
        m = self.metrics()
        layers = m.get('layers', {})
        lines = [
            f"Geruon State Summary",
            f"  vec_dim: {self.vec_dim}",
            f"  Total inputs: {m.get('input_count', 0)}",
            f"  Frames: {m.get('frame_count', 0)} total",
            f"  By layer: {dict(sorted(layers.items()))}",
            f"  L4 active: {m.get('L4_frame_count', 0)}",
            f"  Prediction acc: {m.get('pred_accuracy', 0):.1%}",
            f"  Anomaly score: {self.anomaly_score():.2f}",
            f"  MI(phi;X): {m.get('I(phi;X)', 0):.4f}",
            f"  τ: {self.tau:.4f}  dτ/dt: {self.dtaudt:.6f}",
            f"  Phase: {self.phase.value}",
        ]
        return '\n'.join(lines)

    def save(self, path):
        import json
        m = self.metrics()
        frames_data = [{
            'vec': f.vec, 'weight': f.weight,
            'sig': f.sig, 'layer': getattr(f, 'layer', 'L1')
        } for f in self.memory.frames]
        state = {
            'type': 'Geruon',
            'vec_dim': self.vec_dim,
            'metrics': m,
            'frame_count': self.frame_count,
            'memory_cap': self.memory.capacity,
            'frames': frames_data,
            'tau': self.tau,
            'phase': self.phase.value,
        }
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)

    @classmethod
    def load(cls, path):
        import json
        with open(path) as f:
            state = json.load(f)
        vec_dim = state.get('vec_dim', VEC_DIM_DEFAULT)
        g = cls(vec_dim=vec_dim, memory_cap=state.get('memory_cap', 16))
        g.frame_count = state.get('frame_count', 0)
        g._input_count = state.get('input_count', state.get('frame_count', 0))
        g.memory.tau = state.get('tau', TAU_0)
        for fd in state.get('frames', []):
            vec = fd['vec'] if isinstance(fd['vec'], (list, tuple)) else [0.0] * vec_dim
            nf = GeruonFrame(tuple(vec), weight=fd.get('weight', 1.0),
                       sig=fd.get('sig', ''), layer=fd.get('layer', 'L1'))
            g.memory.frames.append(nf)
            g.memory.total_weight += nf.weight
        return g

    def input_file(self, path, encoding='utf-8'):
        with open(path, encoding=encoding) as f:
            for line in f:
                line = line.strip()
                if line:
                    self.input(line)

    # ── Vocab (unchanged from GEME) ──

    def enable_vocab(self):
        """DEPRECATED: GEME-era human-readable string decoder. Kept as debugging lens only."""
        self.vocab_mode = True

    def promote_to_vocab(self):
        """DEPRECATED: GEME-legacy debug tool. Disabled in non-debug mode.
        Iterates ASCII range to decode cooccurrence symbols into human-readable
        words — external observer perspective, not an architectural operation."""
        # Body disabled (audit P2 3.4). Uncomment for debugging only.
        pass

    def get_vocab(self, min_weight=10):
        return {w: wgt for w, (_, wgt) in self.vocab.items() if wgt >= min_weight}

    def has_vocab(self, word):
        return word in self.vocab

    def evaluate_sig(self, sig):
        """DEPRECATED: string-based signature matching. Retained as debugging lens only."""
        sp = set(sig.split("_"))
        sorted_w = sorted(f.weight for f in self.memory.frames)
        med = sorted_w[len(sorted_w) // 2] if sorted_w else 1
        for f in self.memory.frames:
            if f.weight < med:
                continue
            fp = set(f.sig.split("_"))
            denom = min(len(sp), len(fp))
            if denom == 0:
                continue
            ratio = len(sp & fp) / denom
            if ratio >= 1.0 - DELTA * 1.3:  # ≈ 0.75 — Jaccard-like threshold
                return 2
        return 3


# ──────────────────────────────────────────────────────────────────
# Self-test: phase differentiation across vec_dim
# ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import random as _rnd

    print("=" * 65)
    print("Geruon Self-Test: StructuralSig, τ, Phase, Circularity")
    print("=" * 65)

    # ── Test S1: StructuralSig determinism ──
    print("\n[S1] StructuralSig — same structure → same gid")
    v1 = (0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    v2 = (0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    v3 = (0.9, 0.8, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    s1 = StructuralSig(v1, 3.0, "L1")
    s2 = StructuralSig(v2, 3.0, "L1")
    s3 = StructuralSig(v3, 3.0, "L1")
    s4 = StructuralSig(v1, 1.0, "L1")  # different weight
    print(f"  Same structure:  s1==s2: {s1 == s2} (expect True)  key_eq:{s1.struct_key == s2.struct_key}")
    print(f"  Different vec:   s1==s3: {s1 == s3} (expect False) key_eq:{s1.struct_key == s3.struct_key}")
    print(f"  Different weight: s1==s4: {s1 == s4} (expect False) key_eq:{s1.struct_key == s4.struct_key}")
    print(f"  s1={s1}  s3={s3}")

    # ── Test S2: Self-referential signature → circularity ──
    print("\n[S2] Circularity detection — self-referential signature")
    # Create a signature that references itself
    base = StructuralSig((0.5,) * 16, 1.0, "L4")
    # Recreate with self-reference
    self_ref = StructuralSig((0.5,) * 16, 1.0, "L4", refs=(base,))
    # Create a true self-ref by referencing itself (via proxy)
    proxy = StructuralSig((0.5,) * 16, 1.0, "L4")
    circular = StructuralSig((0.5,) * 16, 1.0, "L4", refs=(proxy,))
    # Acyclic chain
    a = StructuralSig((0.1,) * 16, 1.0, "L1")
    b = StructuralSig((0.2,) * 16, 1.0, "L2", refs=(a,))
    c = StructuralSig((0.3,) * 16, 1.0, "L3", refs=(b,))

    is_circ_base, chain_base = detect_circularity(base)
    is_circ_chain, chain_chain = detect_circularity(c)
    print(f"  No refs:          circular={is_circ_base} (expect False)")
    print(f"  Acyclic L1→L2→L3: circular={is_circ_chain} (expect False)")

    # True self-reference: A → A
    self_ref_to_self = StructuralSig((0.5,) * 16, 1.0, "L4")
    # We can't directly create A→A (need A to exist first), so use a 2-cycle:
    x = StructuralSig((0.1,) * 16, 1.0, "L4")  # x exists
    y = StructuralSig((0.2,) * 16, 1.0, "L4", refs=(x,))  # y → x
    x_with_ref = StructuralSig((0.1,) * 16, 1.0, "L4", refs=(y,))  # x → y, creating x↔y cycle
    is_circ_2cycle, chain_2cycle = detect_circularity(x_with_ref)
    print(f"  2-cycle (x↔y):    circular={is_circ_2cycle} (expect True)")
    if is_circ_2cycle:
        print(f"    chain: {[g % 1000000 for g in chain_2cycle]}")

    # ── Test S3: GeruonFrame creates structural sigs ──
    print("\n[S3] GeruonFrame — auto-generated structural signatures")
    gf1 = GeruonFrame(v1, 3.0, "input_A", layer="L1")
    gf2 = GeruonFrame(v1, 3.0, "input_A", layer="L1")  # same → same gid
    gf3 = GeruonFrame(v3, 3.0, "input_B", layer="L1")
    print(f"  gf1 sig: {gf1.sig}  gid={gf1.struct_sig.gid % 1000000}")
    print(f"  gf2 sig: {gf2.sig}  gid={gf2.struct_sig.gid % 1000000}")
    print(f"  gf3 sig: {gf3.sig}  gid={gf3.struct_sig.gid % 1000000}")
    print(f"  gf1==gf2 (same struct): {gf1.struct_sig == gf2.struct_sig} (expect True)")
    print(f"  gf1==gf3 (diff struct): {gf1.struct_sig == gf3.struct_sig} (expect False)")
    # Check sig tag preservation
    gf4 = GeruonFrame(v1, 5.0, "pred_err_0.45_cat_mat", layer="L4")
    print(f"  L4 pred_err sig: {gf4.sig} (should contain 'pred_err' tag)")

    # ── Test 0: vec_dim flexibility ──
    print("\n[0] Vector dimension flexibility")
    for dim in [8, 16, 32]:
        bands = _compute_phase_bands(dim)
        spans = [hi - lo + 1 for lo, hi in bands.values()]
        print(f"  vec_dim={dim:2d}: bands={spans} total={sum(spans)}")
    # Verify all phases get at least 1 bin
    for dim in [8, 16, 32]:
        bands = _compute_phase_bands(dim)
        for ph in Phase:
            lo, hi = bands[ph]
            assert hi >= lo, f"Phase {ph} has zero bins at dim={dim}"

    # ── Test 1: Single Geruon τ evolution ──
    print("\n[1] Single Geruon — τ evolution under noisy input")
    r = _rnd.Random(42)
    g = Geruon(vec_dim=16, memory_cap=16, cooccur_window=60)
    tau_traj = []
    phase_traj = []

    for step in range(200):
        if step < 60:
            a, b = str(r.randint(0, 3)), str(r.randint(0, 3))
        elif step < 100:
            a, b = str(r.randint(0, 99)), str(r.randint(0, 99))
        elif step < 150:
            a, b = str(r.randint(0, 3)), str(r.randint(0, 3))
        else:
            a, b = str(r.randint(0, 999)), str(r.randint(0, 999))
        f = eq(fn("swap", const(a), const(b)),
               fn("swap", const(b), const(a)))
        g.process_sig(f, structural_signature(f))
        if step % 5 == 0:
            tau_traj.append((step, g.tau))
            phase_traj.append((step, g.phase.value))

    print(f"  Final: τ={g.tau:.4f}  dτ/dt={g.dtaudt:.6f}  phase={g.phase.value}")
    print(f"  Phase transitions: {len(g.memory._phase_transitions)}")
    phases_seen = []
    for _, ph in phase_traj:
        if not phases_seen or phases_seen[-1] != ph:
            phases_seen.append(ph)
    print(f"  Phase sequence: {' → '.join(phases_seen)}")

    # ── Test 2: Three Geruons, same input, τ differentiation ──
    print("\n[2] Three Geruons — same input, should develop τ differentiation")
    seeds = [42, 123, 999]
    units = []
    for s in seeds:
        r2 = _rnd.Random(s)
        u = Geruon(vec_dim=16, memory_cap=16, cooccur_window=60)
        u.memory.quantum_mode = True
        u.memory._qrand = _rnd.Random(s + 777)
        for _ in range(150):
            a, b = str(r2.randint(0, 9)), str(r2.randint(0, 9))
            f = eq(fn("swap", const(a), const(b)),
                   fn("swap", const(b), const(a)))
            u.process_sig(f, structural_signature(f))
        units.append(u)

    for i, u in enumerate(units):
        print(f"  Unit {i}: τ={u.tau:.4f}  phase={u.phase.value}  "
              f"dτ/dt={u.dtaudt:.6f}  transitions={len(u.memory._phase_transitions)}")
    tau_vals = [u.tau for u in units]
    phase_vals = [u.phase.value for u in units]
    print(f"  τ spread: {max(tau_vals) - min(tau_vals):.4f}")
    print(f"  Unique phases: {len(set(phase_vals))}")

    # ── Test 3: Phase-aware output encoding ──
    print("\n[3] Phase-aware output — different phases → distinguishable vectors")
    for dim in [8, 16, 32]:
        print(f"  vec_dim={dim}:")
        ref_vecs = {ph: phase_encode(0.5, ph, dim) for ph in Phase}
        min_dist = float('inf')
        for ph1 in Phase:
            for ph2 in Phase:
                if ph1.value < ph2.value:
                    d = vec_dist(ref_vecs[ph1], ref_vecs[ph2])
                    min_dist = min(min_dist, d)
        print(f"    min inter-phase distance: {min_dist:.4f}")

    # Round-trip test
    for dim in [8, 16, 32]:
        for ph in Phase:
            for anomaly in [0.1, 0.5, 0.9]:
                vec = phase_encode(anomaly, ph, dim)
                dec_anomaly, dec_phase = phase_decode(vec)
                ok = (dec_phase == ph and abs(dec_anomaly - anomaly) < 0.3)
                if not ok:
                    print(f"  Round-trip FAIL dim={dim}: ({anomaly}, {ph.value}) → ({dec_anomaly:.2f}, {dec_phase})")

    # ── Test 4: Lock detection ──
    print("\n[4] Lock detection — repetitive input should drive toward LOCKED")
    r4 = _rnd.Random(77)
    g4 = Geruon(vec_dim=16, memory_cap=16, cooccur_window=60)
    lock_traj = []
    for step in range(500):
        a, b = str(r4.randint(0, 1)), str(r4.randint(0, 1))
        f = eq(fn("swap", const(a), const(b)),
               fn("swap", const(b), const(a)))
        g4.process_sig(f, structural_signature(f))
        if step % 10 == 0:
            lock_traj.append((step, g4.tau, g4.phase.value))
    initial_tau = lock_traj[0][1]
    final_tau = lock_traj[-1][1]
    print(f"  τ: {initial_tau:.4f} → {final_tau:.4f} (Δ={final_tau - initial_tau:+.4f})")
    print(f"  Final phase: {g4.phase.value}")
    phases_touched = set(ph for _, _, ph in lock_traj)
    print(f"  Phases touched: {sorted(phases_touched)}")

    # ── Test 5: Identical outputs distinguishable by phase ──
    print("\n[5] Phase distinguishability — same anomaly, different phases")
    for dim in [8, 16]:
        vecs = {ph: phase_encode(0.5, ph, dim) for ph in Phase}
        all_distinct = True
        for ph1 in Phase:
            for ph2 in Phase:
                if ph1 != ph2 and vecs[ph1] == vecs[ph2]:
                    all_distinct = False
                    print(f"  COLLISION: {ph1.value} == {ph2.value} at dim={dim}")
        print(f"  dim={dim}: all phases distinct = {all_distinct}")

    # ── Test 6: Geruon circularity tracking ──
    print("\n[6] Geruon circularity — struct sig in live system")
    r6 = _rnd.Random(99)
    g6 = Geruon(vec_dim=8, memory_cap=12, cooccur_window=40)
    g6.memory.quantum_mode = True
    g6.memory._qrand = _rnd.Random(9999)
    for _ in range(120):
        a, b = str(r6.randint(0, 5)), str(r6.randint(0, 5))
        f = eq(fn("swap", const(a), const(b)),
               fn("swap", const(b), const(a)))
        g6.process_sig(f, structural_signature(f))

    m6 = g6.metrics()
    print(f"  Frames: {m6['frame_count']}")
    print(f"  Layers: {m6['layers']}")
    print(f"  Circular refs detected: {m6['circular_refs']}")
    # Verify all frames have struct_sig
    no_ss = [f for f in g6.memory.frames if not hasattr(f, 'struct_sig')]
    print(f"  Frames without struct_sig: {len(no_ss)} (expect 0)")

    # Show some signatures
    for f in g6.memory.frames[:5]:
        print(f"    {f.sig[:40]} layer={f.layer}")

    # ── Test 7: Codex cross-generational transmission ──
    print("\n[7] Codex — cross-generational symbol table (EE core operation)")
    # Test symbols — explicit, no dependency on GEME's internal _ALPHABET
    _TEST_SYMS = ['swap', 'pair', 'comm', 'self', 'true', 'false', 'x', 'y', 'z',
                  '+', '=', '0', '1', 'succ', 'pred', 'not', 'and', 'or',
                  'all', 'ex', 'in', 'sub', 'pow', 'null', 'nil', 't', 'f']
    codex_gen0 = Codex.from_alphabet(_TEST_SYMS, vec_dim=16, seed=42)
    print(f"  Gen-0 codex: {codex_gen0}")
    print(f"  Sample: '{_TEST_SYMS[0]}' → vec[:4]={codex_gen0.lookup(_TEST_SYMS[0])[:4]}")

    # Gen 1: run with the codex
    r7 = _rnd.Random(77)
    gen1 = Geruon(vec_dim=16, memory_cap=16, cooccur_window=60, codex=codex_gen0)
    gen1.memory.quantum_mode = True
    gen1.memory._qrand = _rnd.Random(7777)

    known_syms = _TEST_SYMS[:12]   # first 12 symbols as "known language"
    novel_syms = ['α', 'β', 'γ', 'Ω']    # not in codex → should trigger novelty

    for step in range(120):
        if step < 60:
            # Phase 1: known symbols only
            a, b = r7.choice(known_syms), r7.choice(known_syms)
        elif step < 90:
            # Phase 2: mix known and novel
            a = r7.choice(known_syms + novel_syms)
            b = r7.choice(known_syms + novel_syms)
        else:
            # Phase 3: novel symbols dominate
            a, b = r7.choice(novel_syms), r7.choice(novel_syms)
        gen1.input(f"{a}{b}", sig_hint=f"{a}{b}")

    m7 = gen1.metrics()
    print(f"  Gen 1: {m7['frame_count']} frames, τ={gen1.tau:.4f}, phase={gen1.phase.value}")
    print(f"  Codex novelties (potential 碰数): {m7['codex_novelties']}")
    if gen1._codex_novelties:
        samples = gen1._codex_novelties[:5]
        print(f"    First 5: {[(s, sym) for s, sym in samples]}")

    # Enrich codex with Gen 1's stable frames
    n_added = gen1.enrich()
    print(f"  Enriched codex with {n_added} stable frames")
    print(f"  Codex now: {codex_gen0}")

    # Save codex
    import tempfile, os
    tmp = os.path.join(tempfile.gettempdir(), 'geruon_codex_test.json')
    codex_gen0.save(tmp)

    # Gen 2: load the enriched codex
    codex_gen1 = Codex.load(tmp)
    gen2 = Geruon(vec_dim=16, memory_cap=16, cooccur_window=60, codex=codex_gen1)
    gen2.memory.quantum_mode = True
    gen2.memory._qrand = _rnd.Random(8888)

    for step in range(80):
        a, b = r7.choice(known_syms + novel_syms), r7.choice(known_syms + novel_syms)
        gen2.input(f"{a}{b}", sig_hint=f"{a}{b}")

    m2 = gen2.metrics()
    print(f"  Gen 2: {m2['frame_count']} frames, τ={gen2.tau:.4f}, phase={gen2.phase.value}")
    print(f"  Codex novelties: {m2['codex_novelties']}")
    print(f"  Codex generation: {m2['codex_generation']}")
    os.remove(tmp)

    # ── Test 8: Codex as anchor (α-substitute, EE P3 prelude) ──
    print("\n[8] Codex as anchor — Geruon with only codex, no external input")
    codex_anchor = Codex.from_alphabet(_TEST_SYMS[:8], vec_dim=8, seed=99)
    g8 = Geruon(vec_dim=8, memory_cap=10, cooccur_window=40, codex=codex_anchor)
    g8.memory.quantum_mode = True
    g8.memory._qrand = _rnd.Random(1111)

    # Feed ONLY codex symbols — codex IS the environment
    syms = _TEST_SYMS[:8]
    r8 = _rnd.Random(42)
    for step in range(100):
        a, b = r8.choice(syms), r8.choice(syms)
        g8.input(f"{a}{b}", sig_hint=f"{a}{b}")

    m8 = g8.metrics()
    print(f"  Codex-only Geruon: τ={g8.tau:.4f}  phase={g8.phase.value}")
    print(f"  Frames: {m8['frame_count']}  I(Φ;X)={m8['I(phi;X)']}")
    print(f"  Codex novelties: {m8['codex_novelties']} (expect 0 — all symbols known)")
    print(f"  Phases: {m8['phase_steps']}")

    # ── Test 9: 碰数 detection ──
    print("\n[9] 碰数 (Pengshu) — five-condition boundary encounter detector")
    r9 = _rnd.Random(13)
    g9 = Geruon(vec_dim=8, memory_cap=12, cooccur_window=30)
    g9.memory.quantum_mode = True
    g9.memory._qrand = _rnd.Random(1313)

    # Feed high-variance input to drive doubt and phase transitions
    for step in range(300):
        if step < 80:
            a, b = str(r9.randint(0, 3)), str(r9.randint(0, 3))
        elif step < 160:
            a, b = str(r9.randint(0, 49)), str(r9.randint(0, 49))
        elif step < 220:
            a, b = str(r9.randint(0, 3)), str(r9.randint(0, 3))
        else:
            a, b = str(r9.randint(0, 199)), str(r9.randint(0, 199))
        f = eq(fn("swap", const(a), const(b)),
               fn("swap", const(b), const(a)))
        g9.process_sig(f, structural_signature(f))

    m9 = g9.metrics()
    print(f"  Frames: {m9['frame_count']}  τ={g9.tau:.4f}  phase={g9.phase.value}")
    print(f"  Circular refs: {m9['circular_refs']}")
    print(f"  碰数 events: {m9['pengshu_count']}")
    if m9['pengshu_last']:
        ps = m9['pengshu_last']
        print(f"    Last: step={ps['step']} gid={ps['gid']} phase={ps['phase']} "
              f"τ={ps['tau']} dτ/dt={ps['dtaudt']}")
    print(f"  Doubt mode: {m9['doubt_mode']}")
    print(f"  Phase steps: {m9['phase_steps']}")

    # Manual circularity injection: create two frames, make them reference each other
    print("  Manual 2-cycle injection:")
    f1 = GeruonFrame((0.5,) * 8, 3.0, "test_A", layer="L1")
    f2 = GeruonFrame((0.6,) * 8, 3.0, "test_B", layer="L1")
    g9.memory._track_frame_sig(f1)
    g9.memory._track_frame_sig(f2)
    # Create a 2-cycle via new signatures referencing each other
    sig_ab = StructuralSig((0.5,) * 8, 3.0, "L2", refs=(f1.struct_sig, f2.struct_sig))
    sig_ba = StructuralSig((0.6,) * 8, 3.0, "L2", refs=(sig_ab,))  # sig_ba → sig_ab → (f1,f2)
    # sig_ab references f1 and f2 (no cycle), sig_ba references sig_ab
    is_circ, chain = detect_circularity(sig_ba)
    print(f"    sig_ba circular: {is_circ} (expect False — acyclic L2 chain)")

    # Now create a true 2-cycle: A → B → A
    c1 = StructuralSig((0.3,) * 8, 2.0, "L3")
    c2 = StructuralSig((0.4,) * 8, 2.0, "L3", refs=(c1,))
    # Recreate c1 with ref to c2 — but c1 already exists, so make a new one
    c1_cycle = StructuralSig((0.3,) * 8, 2.0, "L3", refs=(c2,))  # c1 → c2 → c1
    is_circ2, chain2 = detect_circularity(c1_cycle)
    print(f"    c1→c2→c1 cycle circular: {is_circ2} (expect True)")
    if is_circ2:
        print(f"    chain: {[g % 1000000 for g in chain2]}")

    # ── Test 10: Instance-level κ_τ (P0 fix — M4 audit) ──
    print("\n[10] Instance-level κ_τ — kappa_tau as constructor parameter")
    for kt in [0.5, 1.0, 10.0]:
        g10 = Geruon(vec_dim=8, memory_cap=12, kappa_tau=kt)
        print(f"  κ_τ={kt:>4.1f}:  memory.kappa_tau={g10.memory.kappa_tau}  "
              f"gamma_tau={g10.memory.gamma_tau:.4f} (expect γ×κ={GAMMA * kt:.4f})")
        assert g10.memory.kappa_tau == kt, f"kappa_tau mismatch: {g10.memory.kappa_tau} != {kt}"
        assert abs(g10.memory.gamma_tau - GAMMA * kt) < 0.001, \
            f"gamma_tau mismatch: {g10.memory.gamma_tau} != {GAMMA * kt}"

    # ── Test 11: struct_sig update on merge (P0 fix — M4 audit) ──
    print("\n[11] struct_sig update — merge changes gid")
    r11 = _rnd.Random(55)
    g11 = Geruon(vec_dim=8, memory_cap=8, cooccur_window=30)
    # Feed identical vectors → should merge
    test_vec = [0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0]
    for i in range(20):
        g11.process_vec(list(test_vec), f"test_{i % 3}")
    # Find the merged frame
    merged = sorted(g11.memory.frames, key=lambda f: -f.merged)[0]
    print(f"  Top merged frame: weight={merged.weight:.1f} merged={merged.merged} "
          f"sig={merged.sig[:40]}")
    # Verify struct_sig exists and weight_bin reflects actual weight
    if hasattr(merged, 'struct_sig') and merged.struct_sig is not None:
        print(f"  weight_bin={merged.struct_sig.weight_bin} "
              f"(actual log2(w)={_log2_bin(merged.weight)})")
        # After multiple merges, struct_sig.weight_bin should reflect merged weight,
        # not creation-time weight. If weight > 2, weight_bin should be >= 1.
        if merged.weight > 2.0:
            assert merged.struct_sig.weight_bin >= 1, \
                f"struct_sig not updated: weight={merged.weight:.1f} but weight_bin={merged.struct_sig.weight_bin}"

    # ── Test 12: LOCKED accuracy integrity (P0 fix — M4 audit) ──
    print("\n[12] LOCKED accuracy integrity — no fake 1.0 accuracy during bridge closure")
    r12 = _rnd.Random(33)
    g12 = Geruon(vec_dim=8, memory_cap=10, cooccur_window=40)
    # Drive system with high variance to push τ up
    for step in range(400):
        a, b = str(r12.randint(0, step % 50 + 5)), str(r12.randint(0, step % 50 + 5))
        f = eq(fn("swap", const(a), const(b)), fn("swap", const(b), const(a)))
        g12.process_sig(f, structural_signature(f))
    acc_vals = g12.memory._prediction_accuracy
    # Check: no 1.0 entries from LOCKED suppression (any 1.0 should be actual correct predictions)
    locked_ones = sum(1 for v in acc_vals if v == 1.0)
    print(f"  Prediction entries: {len(acc_vals)}")
    print(f"  Values of 1.0: {locked_ones} (may include genuine correct predictions)")
    print(f"  τ={g12.tau:.4f}  phase={g12.phase.value}  last_acc={g12.memory._last_accuracy:.3f}")

    # ── Test 13: _hash_str determinism (P0 fix — engineering audit) ──
    print("\n[13] _hash_str determinism — same input → same hash, different → different")
    h1 = _hash_str("pred_err_0.45_cat_mat")
    h2 = _hash_str("pred_err_0.45_cat_mat")
    h3 = _hash_str("sys_doubt_acc_0.32")
    print(f"  hash('pred_err...') = {h1 % 1000000:06d}  (twice) = {h2 % 1000000:06d}")
    print(f"  hash('sys_doubt...') = {h3 % 1000000:06d}")
    assert h1 == h2, f"hash not deterministic: {h1} != {h2}"
    assert h1 != h3, f"hash collision: {h1} == {h3}"

    # ── Test 14: vec copy safety (P0 fix — engineering audit) ──
    print("\n[14] vec copy — process_vec does not mutate caller's data")
    g14 = Geruon(vec_dim=8, memory_cap=8)
    original = [0.5, 0.3, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0]
    caller_vec = list(original)
    g14.process_vec(caller_vec, "test")
    assert caller_vec == original, f"process_vec mutated caller's vec: {caller_vec} != {original}"
    print(f"  vec preserved: {caller_vec == original}")

    print("\n" + "=" * 65)
    print("Geruon self-test complete.")
