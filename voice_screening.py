import wave
import struct
import io

def analyze_audio(audio_bytes):
    """
    Lightweight acoustic analysis using only Python's stdlib wave and struct
    modules — no speech-to-text, no external APIs, no extra dependencies.
    Returns duration, a volume score, and a heuristic preliminary assessment.
    """
    try:
        audio_file = io.BytesIO(audio_bytes)
        with wave.open(audio_file, 'rb') as wf:
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            duration = n_frames / float(framerate) if framerate else 0
            raw_data = wf.readframes(n_frames)

        rms = 0
        if sample_width == 2 and raw_data:
            # Unpack 16-bit signed PCM samples and compute RMS manually
            sample_count = len(raw_data) // 2
            if sample_count > 0:
                samples = struct.unpack(f"<{sample_count}h", raw_data[:sample_count * 2])
                sum_squares = sum(s * s for s in samples)
                rms = (sum_squares / sample_count) ** 0.5

        # Rough 0-100 volume/clarity score — speech rarely hits max amplitude, so scale up
        volume_score = min(round((rms / 32768) * 100 * 4, 1), 100)

        return {
            "duration_seconds": round(duration, 1),
            "volume_score": volume_score,
            "assessment": _generate_assessment(duration, volume_score),
        }
    except Exception as e:
        return {
            "duration_seconds": 0,
            "volume_score": 0,
            "assessment": f"Could not analyze this recording ({str(e)}). Please try recording again.",
        }

def _generate_assessment(duration, volume_score):
    notes = []

    if duration < 3:
        notes.append("Response was very brief — consider asking the candidate to elaborate.")
    elif duration < 15:
        notes.append("Response length was adequate for a preliminary screening.")
    else:
        notes.append("Candidate gave a detailed, extended response.")

    if volume_score < 15:
        notes.append("Audio volume was low — the recording may be hard to review clearly.")
    elif volume_score > 85:
        notes.append("Audio volume was strong throughout.")
    else:
        notes.append("Audio clarity was within a normal range.")

    return " ".join(notes)