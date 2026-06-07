"""Demo: Solo Geruon breathes on Bach's C major prelude (BWV 846).

Reads a MIDI file with zero external dependencies. Encodes note events as
12-dim chroma vectors and feeds them to a solo Geruon. Watch tau breathe
and F (field curvature) respond to harmonic density — without knowing
what a chord is, what a key is, or that Bach existed.
"""
from pathlib import Path
import sys, math, struct
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from geruon import Geruon

# ── Minimal MIDI parser (stdlib only, reads format 0/1 MIDI files) ──
def read_midi_notes(path):
    """Return sorted list of (start_tick, pitch, duration_ticks, velocity)."""
    with open(path, 'rb') as f:
        data = f.read()

    # Read header
    assert data[0:4] == b'MThd', "Not a MIDI file"
    header_len = struct.unpack('>I', data[4:8])[0]
    fmt, ntrks, ticks_per_beat = struct.unpack('>HHH', data[8:14])
    pos = 8 + header_len   # MThd(4) + len(4) + data(header_len)

    notes = []
    for _ in range(ntrks):
        assert data[pos:pos+4] == b'MTrk'
        track_len = struct.unpack('>I', data[pos+4:pos+8])[0]
        pos += 8
        end = pos + track_len
        abs_time = 0
        active = {}  # pitch -> (start_tick, velocity)

        while pos < end:
            # Variable-length delta time
            delta = 0
            while True:
                b = data[pos]; pos += 1
                delta = (delta << 7) | (b & 0x7F)
                if not (b & 0x80): break
            abs_time += delta

            status = data[pos]; pos += 1
            if status < 0x80:  # running status
                pos -= 1; status = 0x90  # assume note-on (simplified)

            if (status & 0xF0) == 0x90:  # Note On
                pitch = data[pos]; vel = data[pos+1]; pos += 2
                if vel > 0:
                    active[pitch] = (abs_time, vel)
                elif pitch in active:
                    start, _ = active.pop(pitch)
                    notes.append((start, pitch, abs_time - start, vel))
            elif (status & 0xF0) == 0x80:  # Note Off
                pitch = data[pos]; pos += 2
                if pitch in active:
                    start, _ = active.pop(pitch)
                    notes.append((start, pitch, abs_time - start, 0))
            elif status == 0xFF:  # Meta event
                meta_type = data[pos]; pos += 1
                meta_len = 0
                while True:
                    b = data[pos]; pos += 1
                    meta_len = (meta_len << 7) | (b & 0x7F)
                    if not (b & 0x80): break
                pos += meta_len
            else:  # Skip other events
                skip = {0xC0:1, 0xD0:1, 0xB0:2, 0xE0:2}.get(status & 0xF0, 2)
                pos += skip

        pos = end

    notes.sort()
    return notes

def notes_to_chroma(notes, ticks_per_beat, window_ticks=120):
    """Convert MIDI notes to 12-dim chroma vectors in time windows."""
    total = max((s + d) for s, _, d, _ in notes) if notes else 0
    vectors = []
    pos = 0
    while pos < total:
        active = set()
        for start, pitch, dur, vel in notes:
            if start <= pos < start + dur and vel > 0:
                active.add(pitch % 12)
        vec = [1.0 if i in active else 0.0 for i in range(12)]
        vectors.append((pos, vec))
        pos += window_ticks
    return vectors

# ── Main ──
import os
midi_path = os.path.join(os.path.dirname(__file__), 'bwv846.mid')
if not os.path.exists(midi_path):
    print("MIDI file not found: demo/bwv846.mid")
    print("Download BWV 846 MIDI (public domain) and place it in demo/")
    sys.exit(1)

print("Reading BWV 846 (C major prelude)...")
notes = read_midi_notes(midi_path)
print(f"  {len(notes)} note events")

# Read tempo from MIDI header — default 120 BPM, 480 ticks/beat
ticks_per_beat = 480
chroma = notes_to_chroma(notes, ticks_per_beat, window_ticks=60)
print(f"  {len(chroma)} chroma windows")

# Solo Geruon — no music theory
g = Geruon(vec_dim=12, memory_cap=12, kappa_tau=5)
print(f"\n{'step':>5}  {'tau':>6}  {'F':>6}  {'phase':<10}  notes")
print(f"{'':->5}  {'':->6}  {'':->6}  {'':->10}  {'':->5}")

for i, (tick, vec) in enumerate(chroma):
    n_active = sum(1 for v in vec if v > 0)
    g.process_vec(vec, f"t{tick}")
    if i % 20 == 0 or i < 5:
        m = g.metrics()
        phase_short = m['phase'][:10] if isinstance(m['phase'], str) else str(m['phase'])[:10]
        print(f"{i:>5}  {m['tau']:>6.3f}  {m['F']:>6.3f}  {phase_short:<10}  "
              f"{'|' * min(n_active, 8)}")

m = g.metrics()
print(f"\nBWV 846 complete.")
print(f"  inputs: {m['input_count']}  frames: {m['frame_count']}/{m['capacity']}")
print(f"  final tau={m['tau']:.3f}  phase={m['phase']}  F={m['F']:.3f}")
print(f"  wit_hits={m['wit_hits']}  wit_rate={m['wit_rate']}")
print(f"  OK: Geruon processed Bach without knowing who Bach was.")
