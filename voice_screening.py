import wave
import audioop
import io

def analyze_audio(audio_bytes):
    """
    Lightweight acoustic analysis using Python's stdlib wave/audioop modules —
    no speech-to-text, no external APIs, no extra dependencies.
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

        if sample_width == 2 and raw_data:
            rms = audioop.rms(raw_data, sample_width)
        else:
            rms = 0

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