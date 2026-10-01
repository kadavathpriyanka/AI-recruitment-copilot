"""
Voice screening utilities for the Recruitment Copilot Streamlit app.

Browser microphone recording is handled by Streamlit's st.audio_input().
This module intentionally does NOT use sr.Microphone(), so PyAudio is not
required for the Streamlit recording workflow.
"""

import io
import struct
import wave

import pyttsx3
import speech_recognition as sr


# ============================================================
# AUDIO ANALYSIS
# ============================================================

def analyze_audio(audio_bytes):
    """Analyze a WAV recording for duration and approximate volume."""
    try:
        audio_file = io.BytesIO(audio_bytes)

        with wave.open(audio_file, "rb") as wav:
            frames = wav.getnframes()
            sample_rate = wav.getframerate()
            sample_width = wav.getsampwidth()
            raw_data = wav.readframes(frames)

        duration = frames / float(sample_rate) if sample_rate else 0.0
        volume_score = 0

        if sample_width == 2 and len(raw_data) >= 2:
            try:
                samples = struct.unpack(
                    "<{}h".format(len(raw_data) // 2),
                    raw_data
                )

                if samples:
                    squared_sum = sum(sample * sample for sample in samples)
                    rms = (squared_sum / len(samples)) ** 0.5
                    volume_score = min(100, max(0, int((rms / 32768) * 100)))
            except Exception:
                volume_score = 0

        return {
            "duration_seconds": round(duration, 2),
            "volume_score": volume_score,
            "assessment": _generate_assessment(duration, volume_score),
        }

    except Exception as exc:
        return {
            "duration_seconds": 0,
            "volume_score": 0,
            "assessment": f"Audio analysis error: {exc}",
        }


def _generate_assessment(duration, volume_score):
    """Create simple delivery feedback from duration and volume."""
    feedback = []

    if duration < 5:
        feedback.append(
            "Your answer was quite short. Try to explain your answer in more detail."
        )
    elif duration < 20:
        feedback.append("Your answer had a reasonable duration.")
    else:
        feedback.append("Your answer had good detail and duration.")

    if volume_score < 15:
        feedback.append("Your voice volume seems low. Try speaking a little louder.")
    elif volume_score < 40:
        feedback.append("Your voice volume is moderate. Try to maintain a clear volume.")
    else:
        feedback.append("Your voice volume was clear.")

    return " ".join(feedback)


# ============================================================
# TEXT TO SPEECH
# ============================================================

def speak_text(text):
    """Speak text through the machine running Streamlit using pyttsx3."""
    try:
        if not text or not str(text).strip():
            return False

        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.setProperty("volume", 1.0)
        engine.say(str(text))
        engine.runAndWait()
        engine.stop()
        return True

    except Exception as exc:
        print(f"Text-to-speech error: {exc}")
        return False


# ============================================================
# SPEECH TO TEXT - STREAMLIT AUDIO
# ============================================================

def listen_to_candidate(audio_bytes):
    """Convert audio recorded by Streamlit st.audio_input() into text.

    Parameters
    ----------
    audio_bytes : bytes
        WAV audio bytes returned by Streamlit's st.audio_input().

    Returns
    -------
    dict
        {'success': bool, 'text': str}

    Notes
    -----
    This function uses SpeechRecognition's AudioFile instead of
    SpeechRecognition's Microphone class. Therefore PyAudio is not required.
    Google speech recognition requires an internet connection.
    """
    recognizer = sr.Recognizer()

    try:
        audio_file = io.BytesIO(audio_bytes)

        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)

        response = recognizer.recognize_google(audio)

        return {
            "success": True,
            "text": response.strip(),
        }

    except sr.UnknownValueError:
        return {
            "success": False,
            "text": (
                "Sorry, I could not understand the recording. "
                "Please speak clearly and try again."
            ),
        }

    except sr.RequestError:
        return {
            "success": False,
            "text": (
                "Speech recognition service could not be reached. "
                "Please check your internet connection and try again."
            ),
        }

    except ValueError:
        return {
            "success": False,
            "text": (
                "The recorded audio format could not be processed. "
                "Please record your answer again."
            ),
        }

    except Exception as exc:
        return {
            "success": False,
            "text": f"Audio processing error: {exc}",
        }


# ============================================================
# INTERVIEW FEEDBACK
# ============================================================

def generate_voice_feedback(response):
    """Generate simple communication feedback from the transcript."""
    if not response or not response.strip():
        return "No response was detected. Please try answering the question again."

    response = response.strip()
    word_count = len(response.split())
    feedback = []

    if word_count < 10:
        feedback.append(
            "Your answer is quite short. Try to explain your thoughts in more detail."
        )
    elif word_count < 30:
        feedback.append(
            "Your answer is reasonably concise. You could add a little more detail if appropriate."
        )
    else:
        feedback.append("Your answer provides a good amount of detail.")

    feedback.append(
        "For interviews, try to explain the concept clearly and support your answer with a simple example."
    )

    return " ".join(feedback)


# ============================================================
# COMPLETE VOICE SCREENING HELPER
# ============================================================

def voice_screening(question=None, audio_bytes=None):
    """Run the complete question -> transcription -> feedback workflow.

    Streamlit normally calls the individual functions so that the UI can
    display the recording widget. This helper is also available for other
    callers that already have audio bytes.
    """
    if question is None:
        question = (
            "Hello! Please introduce yourself and describe your experience "
            "with machine learning."
        )

    spoken = speak_text(question)

    if audio_bytes is None:
        return {
            "success": False,
            "question": question,
            "response": "",
            "feedback": "Please record your answer using the microphone.",
            "audio_analysis": None,
            "spoken": spoken,
        }

    transcription = listen_to_candidate(audio_bytes)

    if not transcription["success"]:
        return {
            "success": False,
            "question": question,
            "response": "",
            "feedback": transcription["text"],
            "audio_analysis": None,
            "spoken": spoken,
        }

    response = transcription["text"]

    return {
        "success": True,
        "question": question,
        "response": response,
        "feedback": generate_voice_feedback(response),
        "audio_analysis": analyze_audio(audio_bytes),
        "spoken": spoken,
    }


# ============================================================
# OPTIONAL TEST
# ============================================================

def test_text_to_speech():
    """Quick local test for pyttsx3."""
    return speak_text(
        "Hello! This is your AI recruitment interviewer. "
        "Please introduce yourself."
    )
