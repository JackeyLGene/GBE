"""Generic MIDI encoder for any (notes, beats) score.
Produces a MIDI event stream with note sustain/decay.
Labels preserved for structural-analysis pieces (fugue, etc.)."""
NOTES_Hz = {
    'C2':65.41,'C#2':69.30,'D2':73.42,'D#2':77.78,'E2':82.41,'F2':87.31,
    'F#2':92.50,'G2':98.00,'G#2':103.83,'A2':110.00,'A#2':116.54,'B2':123.47,
    'C3':130.81,'C#3':138.59,'D3':146.83,'D#3':155.56,'E3':164.81,'F3':174.61,
    'F#3':185.00,'G3':196.00,'G#3':207.65,'A3':220.00,'A#3':233.08,'B3':246.94,
    'C4':261.63,'C#4':277.18,'D4':293.66,'D#4':311.13,'E4':329.63,'F4':349.23,
    'F#4':369.99,'G4':392.00,'G#4':415.30,'A4':440.00,'A#4':466.16,'B4':493.88,
    'C5':523.25,'C#5':554.37,'D5':587.33,'D#5':622.25,'E5':659.25,'F5':698.46,
    'F#5':739.99,'G5':783.99,'G#5':830.61,'A5':880.00,'A#5':932.33,'B5':987.77,
    'C6':1046.50,
}
FREQ_MIN, FREQ_MAX, BINS = 65, 1050, 27
DECAY = 0.85

def vec_for_active(active):
    v = [0.0]*BINS
    for n in active:
        f = NOTES_Hz.get(n, 440)
        idx = int((f-FREQ_MIN)/(FREQ_MAX-FREQ_MIN)*(BINS-1))
        v[max(0,min(BINS-1,idx))] += 1.0
    s = sum(v)
    return [x/s for x in v] if s > 0 else v

def midi_encode(score, passes=1):
    """Convert score to MIDI event stream.
    score: list of (notes, beats) or (notes, beats, label)
    Returns: list of (vec, label_or_None) pairs."""
    sequence = []
    for _ in range(passes):
        active_notes = set()
        carry_over = {}

        for entry in score:
            if len(entry) == 2:
                notes, beats = entry
                label = None
            else:
                notes, beats = entry[0], entry[1]
                label = entry[2] if len(entry) > 2 else None

            # Note-on for each note in the chord
            for n in notes:
                active_notes.add(n)
                carry_over[n] = beats

            # Step through duration with decay
            for step in range(beats):
                to_remove = []
                for n in list(carry_over.keys()):
                    carry_over[n] -= 1
                    if carry_over[n] <= 0:
                        active_notes.discard(n)
                        to_remove.append(n)
                for n in to_remove:
                    del carry_over[n]

                vec = vec_for_active(active_notes)
                sequence.append((vec, label))

        # Ring-out
        for _ in range(4):
            active_notes = set()
            carry_over = {}
            sequence.append((vec_for_active(set()), 'silence'))

    return sequence
