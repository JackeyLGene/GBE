"""Generate two demo videos: sine boundary detection + Bach Geruon breathing.

Requires: matplotlib, ffmpeg, numpy, soundfile (for audio)
Output: demo/demo_self_sine.mp4, demo/demo_geruon_bach.mp4
"""
from pathlib import Path
import sys, math, struct, os
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from geruon import Geruon, BiasField
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation

DIM, CAP = 16, 24
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════
# Video 1: Sine Boundary Detection — 3-cavity Self
# ═══════════════════════════════════════════════════════════════════

def make_sine_stream(n=400, dim=DIM):
    for i in range(n):
        if i < 100:       freq, phase = 1.0, 0.0
        elif i < 200:     freq, phase = 2.0, 0.0
        elif i < 300:     freq, phase = 1.0, math.pi
        else:             freq, phase = 1.0, 0.0
        vec = [math.sin(freq * i * 0.1 + j * 0.3 + phase) * 0.5 + 0.5 for j in range(dim)]
        yield vec

def make_sine_video():
    print("Generating sine boundary detection video...")
    bias = BiasField(vec_dim=DIM)
    cavities = [
        Geruon(vec_dim=DIM, memory_cap=CAP, kappa_tau=0.5,  bias_field=bias),
        Geruon(vec_dim=DIM, memory_cap=CAP, kappa_tau=10.0, bias_field=bias),
        Geruon(vec_dim=DIM, memory_cap=CAP, kappa_tau=100.0,bias_field=bias),
    ]

    stream = list(make_sine_stream())
    harms, taus_fast, taus_mid, taus_slow = [], [], [], []
    # Track raw signal for 2 sample dimensions
    raw_dim0, raw_dim4 = [], []

    for vec in stream:
        raw_dim0.append(vec[0])
        raw_dim4.append(vec[4])
        for g in cavities:
            g.process_vec(vec, "s")
        cs = [g.memory.centroid() for g in cavities]
        cs = [c for c in cs if c is not None]
        if len(cs) >= 2:
            h = sum(math.sqrt(sum((cs[a][k]-cs[b][k])**2 for k in range(DIM)))
                    for a in range(len(cs)) for b in range(a+1, len(cs)))
            h /= len(cs) * (len(cs)-1) / 2
            harms.append(h)
        else:
            harms.append(0.0)
        taus_fast.append(cavities[0].tau)
        taus_mid.append(cavities[1].tau)
        taus_slow.append(cavities[2].tau)

    N = len(stream)
    fig = plt.figure(figsize=(12, 8))
    gs = fig.add_gridspec(3, 1, height_ratios=[2.5, 1.2, 1.2], hspace=0.35)
    ax1 = fig.add_subplot(gs[0])  # cross-harm with phase regions
    ax2 = fig.add_subplot(gs[1])  # raw signal
    ax3 = fig.add_subplot(gs[2])  # tau

    fig.suptitle('3-Cavity Self  —  Blind Boundary Detection on Synthetic Stream',
                 fontsize=14, fontweight='bold')

    # ── Phase regions: colored backgrounds + labels ──
    phases = [
        (0, 100, '#e8f4fd', 'BASELINE\nfreq = 1.0, phase = 0\nStable — low cross-harm'),
        (100, 200, '#fff3cd', 'FREQ ×2\nfreq = 2.0\nFrequency doubles →\nfast lens adapts,\nslow lens lags →\nharm spikes at boundary'),
        (200, 300, '#fde8e8', 'PHASE FLIP\nfreq = 1.0, phase = π\nPhase inverts →\nnew statistical structure →\nharm spikes, then settles'),
        (300, 400, '#e8f4fd', 'RETURN\nfreq = 1.0, phase = 0\nReturns to original →\nfamiliar structure →\nharm spikes, cavities\nre-converge'),
    ]

    # Top: cross-harm with phase backgrounds
    ax1.set_ylabel('Cross-Harm', fontsize=11)
    ax1.set_xlim(0, N)
    max_h = max(harms) if harms else 1.0
    ax1.set_ylim(0, max_h * 1.25)
    ax1.grid(True, alpha=0.3)

    for x0, x1, color, label in phases:
        ax1.axvspan(x0, x1, alpha=0.15, color=color)
        ax1.axvline(x=x0, color='#666', linestyle='--', alpha=0.5, linewidth=1)
        mid_x = (x0 + x1) / 2
        ax1.text(mid_x, max_h * 1.08, label, ha='center', va='bottom',
                fontsize=7.5, fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.4', facecolor=color, alpha=0.7))

    line_harm, = ax1.plot([], [], '#1a5276', linewidth=1.4, label='cross-harm')
    ax1.legend(loc='upper right', fontsize=8)

    # Middle: raw signal (2 sample dimensions)
    ax2.set_ylabel('Raw signal\n(dims 0, 4)', fontsize=9)
    ax2.set_xlim(0, N)
    ax2.set_ylim(-0.1, 1.1)
    ax2.grid(True, alpha=0.3)
    line_raw0, = ax2.plot([], [], '#e74c3c', linewidth=0.6, alpha=0.8, label='dim 0')
    line_raw4, = ax2.plot([], [], '#2980b9', linewidth=0.6, alpha=0.8, label='dim 4')
    ax2.legend(loc='upper right', fontsize=7)
    # Mark phase boundaries on raw signal too
    for x0, _, _, _ in phases:
        ax2.axvline(x=x0, color='#666', linestyle='--', alpha=0.3, linewidth=0.8)
    ax2.text(5, 1.05, 'What the instrument sees:', fontsize=8, fontstyle='italic', color='#555')

    # Bottom: τ of three cavities — with explanatory region annotations
    ax3.set_xlabel('Step', fontsize=11)
    ax3.set_ylabel('τ', fontsize=11)
    ax3.set_xlim(0, N)
    ax3.set_ylim(0.55, 0.80)
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0.75, color='#999', linestyle=':', alpha=0.5, linewidth=0.8)
    ax3.text(N-5, 0.753, 'LOCKED', fontsize=7, color='#999', ha='right')
    line_tau_f, = ax3.plot([], [], '#e74c3c', linewidth=0.8, alpha=0.7, label='κ=0.5 (fast)')
    line_tau_m, = ax3.plot([], [], '#27ae60', linewidth=0.8, alpha=0.7, label='κ=10 (mid)')
    line_tau_s, = ax3.plot([], [], '#2980b9', linewidth=0.8, alpha=0.7, label='κ=100 (slow)')
    ax3.legend(loc='upper right', fontsize=8)

    # ── τ region annotations — explaining why τ moves or stays flat ──
    tau_regions = [
        (0, 100, '#e8f4fd',
         'τ flat — centroid stable,\nframe economy merging cleanly'),
        (100, 200, '#fff3cd',
         'τ STILL flat —\nfreq change did NOT shift centroid.\nCross-harm spiked (lenses disagree)\nbut τ unmoved (no frame stress).\nThese are two orthogonal readings.'),
        (200, 300, '#fde8e8',
         'τ STILL flat —\nphase flip also does not shift centroid.\nFrame economy finds new merge targets,\nprediction stays accurate.'),
        (300, 400, '#f0e6f6',
         'τ MOVES (320-350) —\nresidual frames from 3 regimes\nmake re-merging turbulent.\nCentroid finally displaced\n→ frame economy stress\n→ τ responds.'),
    ]
    for x0, x1, color, label in tau_regions:
        ax3.axvspan(x0, x1, alpha=0.10, color=color)
        mid_x = (x0 + x1) / 2
        y_pos = 0.565
        ax3.text(mid_x, y_pos, label, ha='center', va='bottom',
                fontsize=6.5, fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.35', facecolor=color, alpha=0.75))

    def animate(i):
        x = list(range(i+1))
        line_harm.set_data(x, harms[:i+1])
        line_raw0.set_data(x, raw_dim0[:i+1])
        line_raw4.set_data(x, raw_dim4[:i+1])
        line_tau_f.set_data(x, taus_fast[:i+1])
        line_tau_m.set_data(x, taus_mid[:i+1])
        line_tau_s.set_data(x, taus_slow[:i+1])
        return [line_harm, line_raw0, line_raw4, line_tau_f, line_tau_m, line_tau_s]

    ani = animation.FuncAnimation(fig, animate, frames=N, interval=25, blit=True)
    out = os.path.join(OUT_DIR, 'demo_self_sine.mp4')
    ani.save(out, writer='ffmpeg', fps=30, dpi=140)
    plt.close()
    print(f"  -> {out}")

# ═══════════════════════════════════════════════════════════════════
# Video 2: Bach Geruon Breathing — Solo Geruon
# ═══════════════════════════════════════════════════════════════════

def read_midi_notes(path):
    with open(path, 'rb') as f:
        data = f.read()
    assert data[0:4] == b'MThd'
    header_len = struct.unpack('>I', data[4:8])[0]
    fmt, ntrks, ticks_per_beat = struct.unpack('>HHH', data[8:14])
    pos = 8 + header_len
    notes = []
    tempo_us_per_beat = 500000  # default 120 BPM
    for _ in range(ntrks):
        assert data[pos:pos+4] == b'MTrk'
        track_len = struct.unpack('>I', data[pos+4:pos+8])[0]
        pos += 8; end = pos + track_len
        abs_time = 0; active = {}
        while pos < end:
            delta = 0
            while True:
                b = data[pos]; pos += 1
                delta = (delta << 7) | (b & 0x7F)
                if not (b & 0x80): break
            abs_time += delta
            status = data[pos]; pos += 1
            if status < 0x80: pos -= 1; status = 0x90
            if (status & 0xF0) == 0x90:
                pitch = data[pos]; vel = data[pos+1]; pos += 2
                if vel > 0: active[pitch] = (abs_time, vel)
                elif pitch in active:
                    start, _ = active.pop(pitch)
                    notes.append((start, pitch, abs_time - start))
            elif (status & 0xF0) == 0x80:
                pitch = data[pos]; pos += 2
                if pitch in active:
                    start, _ = active.pop(pitch)
                    notes.append((start, pitch, abs_time - start))
            elif status == 0xFF:
                meta_type = data[pos]; pos += 1
                meta_len = 0
                while True:
                    b = data[pos]; pos += 1
                    meta_len = (meta_len << 7) | (b & 0x7F)
                    if not (b & 0x80): break
                if meta_type == 0x51 and meta_len == 3:  # Set Tempo
                    tempo_us_per_beat = (data[pos] << 16) | (data[pos+1] << 8) | data[pos+2]
                pos += meta_len
            else:
                skip = {0xC0:1, 0xD0:1, 0xB0:2, 0xE0:2}.get(status & 0xF0, 2)
                pos += skip
        pos = end
    notes.sort()
    tempo_bpm = 60_000_000 / tempo_us_per_beat
    return notes, ticks_per_beat, tempo_bpm

def synthesize_audio(notes, ticks_per_beat, start_offset, end_tick, n_windows,
                     sample_rate=22050, tempo_bpm=120):
    """Synthesize piano-like audio from MIDI notes. start_offset trims leading silence."""
    import numpy as np
    us_per_beat = 60_000_000 / tempo_bpm
    seconds_per_tick = us_per_beat / (ticks_per_beat * 1_000_000)
    duration = (end_tick - start_offset) * seconds_per_tick

    n_samples = int(duration * sample_rate)
    audio = np.zeros(n_samples, dtype=np.float32)

    def pitch_to_hz(p):
        return 440.0 * (2.0 ** ((p - 69) / 12.0))

    harmonics = [1.0, 0.6, 0.3, 0.15, 0.07]

    for st, pitch, dur_ticks in notes:
        t_start = (st - start_offset) * seconds_per_tick
        t_end = (st + dur_ticks - start_offset) * seconds_per_tick
        i0 = int(t_start * sample_rate)
        i1 = min(int(t_end * sample_rate), n_samples)
        if i1 <= i0 or i0 >= n_samples: continue

        freq = pitch_to_hz(pitch)
        n = i1 - i0
        t = np.arange(n, dtype=np.float32) / sample_rate

        # Piano envelope: fast attack (~5ms), exponential decay
        attack = np.minimum(1.0, t / 0.005)
        decay = np.exp(-t * 3.0)  # ~0.05 after 1 second
        env = attack * decay * 0.25

        # Sum harmonics
        wave = np.zeros(n, dtype=np.float32)
        for h, amp in enumerate(harmonics):
            wave += np.sin(2.0 * np.pi * freq * (h + 1) * t) * amp
        audio[i0:i1] += wave * env

    # Normalize
    mx = np.max(np.abs(audio))
    if mx > 0: audio /= mx * 1.1

    import soundfile as sf
    wav_path = os.path.join(OUT_DIR, '_bach_audio.wav')
    sf.write(wav_path, audio, sample_rate)
    return wav_path, duration


def make_bach_video():
    print("Generating Bach Geruon breathing video...")
    midi_path = os.path.join(OUT_DIR, 'bwv846.mid')
    notes, ticks_per_beat, tempo_bpm = read_midi_notes(midi_path)
    print(f"  {len(notes)} notes, {ticks_per_beat} TPQN, {tempo_bpm:.0f} BPM")
    # Trim trailing near-silence: use 98th percentile of note-end ticks
    note_ends = sorted([s + d for s, _, d in notes], reverse=True)
    total = note_ends[len(note_ends) // 50] if len(note_ends) > 50 else note_ends[0]

    # Build chroma vectors — start from first active window, skip MIDI silence
    step = 20
    first_tick = notes[0][0] if notes else 0
    start_tick = (first_tick // step) * step  # align to step boundary
    chroma, window_ticks = [], []
    for t in range(start_tick, total, step):
        active = set()
        for start, pitch, dur in notes:
            if start <= t < start + dur:
                active.add(pitch % 12)
        chroma.append([1.0 if i in active else 0.0 for i in range(12)])
        window_ticks.append(t)

    # Compute bar numbers from ticks (assuming 4/4, but use actual tempo)
    # BWV 846: 35 bars, ~480 ticks/beat, ~1920 ticks/bar
    ticks_per_bar = ticks_per_beat * 4  # assume 4/4
    # Map musical sections to window indices
    def tick_to_window(tick):
        for i, wt in enumerate(window_ticks):
            if wt >= tick: return i
        return len(window_ticks) - 1

    # Musical sections of BWV 846 (bar numbers → tick → window index)
    bar_to_tick = lambda bar: int((bar - 1) * ticks_per_bar)
    sections = [
        (0, tick_to_window(bar_to_tick(5)), '#e8f4fd',
         'TONIC (bars 1-4)\nC major arpeggios\nsingle harmony —\nframe economy settles'),
        (tick_to_window(bar_to_tick(5)), tick_to_window(bar_to_tick(12)), '#fff3cd',
         'DOMINANT PEDAL (bars 5-11)\nG in bass, harmonic tension\nchord changes accelerate\n→ F rises, model revises'),
        (tick_to_window(bar_to_tick(12)), tick_to_window(bar_to_tick(25)), '#fde8e8',
         'SEQUENCES (bars 12-24)\nchromatic passing tones\nmodulatory passages\n→ frequent wit pulses'),
        (tick_to_window(bar_to_tick(25)), len(chroma), '#e8f4fd',
         'RESOLUTION (bars 25-35)\nreturn to C major\nfinal cadence —\nmodel stabilizes'),
    ]

    g = Geruon(vec_dim=12, memory_cap=16, kappa_tau=3, structon=0.005)
    Fs, wits, centroid_disp = [], [], []
    for vec in chroma:
        g.process_vec(vec, "b")
        m = g.metrics()
        Fs.append(m['F'])
        centroid_disp.append(m['centroid_displacement'])
        wits.append(1 if m['centroid_displacement'] > 0.005 else 0)

    N = len(chroma)
    fig = plt.figure(figsize=(12, 6.5))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.8, 1], hspace=0.3)
    ax1 = fig.add_subplot(gs[0])  # F + musical backgrounds
    ax2 = fig.add_subplot(gs[1])  # wit density

    fig.suptitle('Solo Geruon on Bach  —  BWV 846 (C Major Prelude)',
                 fontsize=14, fontweight='bold')

    # Top: F with musical section backgrounds
    ax1.set_ylabel('F (field curvature)', fontsize=10)
    ax1.set_xlim(0, N)
    ax1.set_ylim(0, max(Fs) * 1.35 + 0.01)
    ax1.grid(True, alpha=0.3)

    for idx, (x0, x1, color, label) in enumerate(sections):
        ax1.axvspan(x0, x1, alpha=0.12, color=color)
        ax1.axvline(x=x0, color='#666', linestyle='--', alpha=0.4, linewidth=0.8)
        mid_x = (x0 + x1) / 2
        y_pos = max(Fs) * (1.25 if idx % 2 == 0 else 1.10)
        ax1.text(mid_x, y_pos, label, ha='center', va='bottom' if idx % 2 == 0 else 'top',
                fontsize=6.5, fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.75))

    line_F, = ax1.plot([], [], '#1a5276', linewidth=1.2, label='F (field curvature)')
    ax1.legend(loc='upper right', fontsize=8)

    # Bottom: wit density — running count of pulses per 100-window block
    ax2.set_xlabel('Window', fontsize=11)
    ax2.set_ylabel('wit density\n(pulses / 100 windows)', fontsize=9)
    ax2.set_xlim(0, N)
    # Compute density: count wit hits in sliding 100-window blocks
    block = 100
    wit_density = []
    for i in range(N):
        lo = max(0, i - block)
        hi = min(N, i + block)
        cnt = sum(wits[lo:hi])
        wit_density.append(cnt / ((hi - lo) / 100))
    max_dens = max(wit_density) if wit_density else 1
    ax2.set_ylim(0, max_dens * 1.25)
    ax2.grid(True, alpha=0.3)
    line_wd, = ax2.plot([], [], '#c0392b', linewidth=1.2, alpha=0.85)
    ax2.fill_between([], 0, [], color='#c0392b', alpha=0.10)

    for x0, _, _, _ in sections:
        ax2.axvline(x=x0, color='#666', linestyle='--', alpha=0.3, linewidth=0.8)
    # One annotation for the key insight: wit/F divergence in resolution
    res_x0 = sections[3][0]
    ax2.text(res_x0 + (N - res_x0) * 0.35, max_dens * 1.05,
             'F flat (still C major) but wit reads local event density.\nF and wit are orthogonal — they measure different layers.',
             ha='center', fontsize=7, fontstyle='italic', color='#555')

    def animate(i):
        x = list(range(i+1))
        line_F.set_data(x, Fs[:i+1])
        line_wd.set_data(x, wit_density[:i+1])
        return [line_F, line_wd]

    # ── Synthesize audio (offset by start_tick to match trimmed chroma) ──
    audio_path, audio_dur = synthesize_audio(notes, ticks_per_beat, start_tick, total, len(chroma), tempo_bpm=tempo_bpm)
    video_fps = len(chroma) / audio_dur

    ani = animation.FuncAnimation(fig, animate, frames=N, interval=1000/video_fps, blit=True)
    video_temp = os.path.join(OUT_DIR, '_bach_video.mp4')
    ani.save(video_temp, writer='ffmpeg', fps=video_fps, dpi=140)
    plt.close()

    out = os.path.join(OUT_DIR, 'demo_geruon_bach.mp4')
    import subprocess
    subprocess.run([
        'ffmpeg', '-y', '-i', video_temp, '-i', audio_path,
        '-c:v', 'copy', '-c:a', 'aac', '-shortest', out
    ], capture_output=True)
    os.remove(video_temp)
    os.remove(audio_path)
    print(f"  -> {out} (with piano audio, {video_fps:.1f} fps)")

# ═══════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    make_sine_video()
    make_bach_video()
    print("Done. Two MP4 files in demo/")
