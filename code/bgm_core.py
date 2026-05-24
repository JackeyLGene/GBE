"""
BGM Core: GEMENet — Multi-GEME network container.

No GEME kernel modifications. GEME unchanged: "always receives from environment".
L6 = only output per GEME. G0 = standard GEME. Feedback = environment vector.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from geme import GEME
import random as _qr2
import statistics

_VEC_DIM = 27

def l6_to_vec(l6_val):
    """Encode L6 scalar [0,1] to 27-dim bin vector."""
    v = [0.0] * _VEC_DIM
    idx = int(l6_val * (_VEC_DIM - 1))
    v[max(0, min(_VEC_DIM - 1, idx))] = 1.0
    return v

def g0_feedback_vec(g0_geme, dim=_VEC_DIM):
    """Extract G0's self-observation as feedback vector.

    Uses G0's weighted frame centroid — G0's own 'view' encoded
    in the same vector space as all GEME inputs.
    """
    frames = g0_geme.memory.frames
    if not frames:
        return [0.0] * dim
    total_w = sum(f.weight for f in frames)
    if total_w <= 0:
        return [0.0] * dim
    return [sum(f.vec[i] * f.weight for f in frames) / total_w for i in range(dim)]


class GEMENet:
    """Manage N GEME units + 1 G0 unit with optional feedback loop.

    G0 operates at a slower timescale (g0_interval) than individual units.
    This decoupling is the core discovery: cross-scale emergence requires
    temporal asymmetry between layers.
    """

    def __init__(self, n_units=3, mem_cap=16, g0_enabled=True, g0_weight=0.3,
                 g0_interval=1, closed_loop=True, seed_base=0):
        """
        Args:
            n_units: Number of parallel GEME units (A, B, C...)
            mem_cap: Frame capacity per GEME
            g0_enabled: If False, G0 feedback is disabled (ablation mode)
            g0_weight: Blend ratio for G0 feedback in [0,1]. 0 = no feedback
            g0_interval: G0 processes aggregated input every N steps.
                         Default=1 (same frequency as units).
                         Higher = slower temporal resolution on G0.
            seed_base: Base random seed for reproducibility
        """
        self.g0_enabled = g0_enabled
        self.closed_loop = closed_loop
        self.g0_weight = g0_weight if g0_enabled else 0.0
        self._base_weight = g0_weight  # for closed-loop reset
        self.g0_interval = g0_interval
        self._g0_buffer = []  # accumulates L6 values between G0 steps

        # Create parallel GEME units
        self.units = []
        for i in range(n_units):
            g = GEME(memory_cap=mem_cap)
            g.memory.preserve_sig = True
            g.memory.quantum_mode = True
            g.memory._merge_dists = [0.3] * 30
            g._induction_threshold = 3.0
            g.memory.cooccur_thresh = 0.08
            g.memory._qrand = _qr2.Random(seed_base + i * 777)
            self.units.append(g)

        # G0: standard GEME (always exists for metrics, but feedback can be disabled)
        self.g0 = GEME(memory_cap=mem_cap)
        self.g0.memory.preserve_sig = True
        self.g0.memory.quantum_mode = True
        self.g0.memory._merge_dists = [0.3] * 30
        self.g0._induction_threshold = 3.0
        self.g0.memory.cooccur_thresh = 0.08
        self.g0.memory._qrand = _qr2.Random(seed_base + 9999)

        self._t = 0
        self._track = None

    def enable_tracking(self):
        """Enable per-step novelty tracking. Returns list ref for external recording."""
        self._track = {
            'g0_pred_err': [],  # G0 pred_err frame count per step (novelty spike)
            'g0_meta': [],      # G0 L4_meta_active per step (weight derivatives)
            'g0_doubt': [],     # G0 doubt mode per step
            'g0_acc': [],       # G0 rolling accuracy (for reference)
            'unit_acc': [],     # [step_0: [u0_acc, u1_acc, u2_acc], ...]
            'step_labels': [],  # Musical chord / harmonic label
        }
        return self._track

    def step(self, ext_vec, step_label=''):
        """One time step. ext_vec: external input vector.

        Order:
            1. Each unit receives ext_vec + G0 feedback
            2. Each unit self-observes
            3. G0 receives aggregated L6 from all units
            4. G0 self-observes → feedback ready for next step
        """
        # Phase 1: Units process external input
        for unit in self.units:
            if self.g0_weight > 0:
                # Blend: external + G0 feedback
                g0_vec = g0_feedback_vec(self.g0)
                blended = [(1.0 - self.g0_weight) * ext_vec[i] + self.g0_weight * g0_vec[i]
                           for i in range(len(ext_vec))]
                unit.process_vec(blended, 'input')
            else:
                unit.process_vec(ext_vec, 'input')
            unit.memory.self_observe()

        # Phase 2: Accumulate L6 for G0
        l6_vals = [u.anomaly_score() for u in self.units]
        self._g0_buffer.append(sum(l6_vals) / len(l6_vals))

        # Phase 3: G0 processes at its own timescale
        if self._t % self.g0_interval == 0 and self._g0_buffer:
            g0_in = l6_to_vec(sum(self._g0_buffer) / len(self._g0_buffer))
            self._g0_buffer = []
            self.g0.process_vec(g0_in, 'g0')
            self.g0.memory.self_observe()
            
            # L5-L6 closed loop: G0's doubt_mode → modulates g0_weight
            if self.closed_loop:
                g0_metrics = self.g0.metrics()
                if g0_metrics.get('doubt_mode', False):
                    self.g0_weight = min(0.8, self.g0_weight + 0.05)
                else:
                    self.g0_weight = max(0.1, self.g0_weight - 0.02)

        # Record tracking data (G0 metrics: last known value if not updated this step)
        if self._track is not None:
            g0_m = self.g0.metrics()
            self._track['g0_pred_err'].append(g0_m.get('L4_frame_count', 0))
            self._track['g0_meta'].append(g0_m.get('L4_meta_active', 0))
            self._track['g0_doubt'].append(g0_m.get('doubt_mode', False))
            self._track['g0_acc'].append(g0_m.get('pred_accuracy', 0))
            self._track['unit_acc'].append([u.metrics().get('pred_accuracy', 0) for u in self.units])
            self._track['step_labels'].append(step_label)

        self._t += 1

    def metrics(self):
        """Return metrics for all units + G0."""
        result = {
            'units': [],
            'g0': {},
            'config': {
                'n_units': len(self.units),
                'g0_enabled': self.g0_enabled,
                'g0_weight': self.g0_weight,
            }
        }
        for i, unit in enumerate(self.units):
            m = unit.metrics()
            result['units'].append({
                'acc': m.get('pred_accuracy', 0),
                'L4': m.get('L4_frame_count', 0),
                'MI': m.get('I(phi;X)', 0),
                'doubt': m.get('doubt_mode', False),
                'l6': unit.anomaly_score(),
            })
        m = self.g0.metrics()
        result['g0'] = {
            'frames': m.get('frame_count', 0),
            'L4': m.get('L4_frame_count', 0),
            'MI': m.get('I(phi;X)', 0),
        }
        return result
