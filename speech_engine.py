# ============================================================
# JARVIS SPEECH ENGINE (TEXT-TO-SPEECH & RECOGNITION)
# ============================================================

import os
import queue
import threading
import time

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False

from config import (
    VOICE_ENABLED,
    VOICE_PREFERRED_NAME,
    VOICE_RATE,
    VOICE_VOLUME,
    SPEECH_ENERGY_THRESHOLD,
    SPEECH_PAUSE_THRESHOLD,
    SPEECH_LISTEN_TIMEOUT,
    SPEECH_PHRASE_TIME_LIMIT,
)

# Global speech queue and state
_speech_queue = queue.Queue()
_voice_enabled = VOICE_ENABLED
_tts_thread = None
_tts_running = False
_is_speaking = False


# ============================================================
# TTS WORKER THREAD
# ============================================================

def _tts_worker():
    """
    Dedicated worker thread for pyttsx3.
    Prevents blocking the CLI and avoids COM threading issues on Windows.
    """
    global _tts_running, _is_speaking

    if not HAS_PYTTSX3:
        return

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", VOICE_RATE)
        engine.setProperty("volume", VOICE_VOLUME)

        # Select preferred voice (e.g., David for British/Jarvis tone)
        voices = engine.getProperty("voices")
        selected_voice = None
        for voice in voices:
            if VOICE_PREFERRED_NAME.lower() in voice.name.lower():
                selected_voice = voice.id
                break

        if selected_voice:
            engine.setProperty("voice", selected_voice)
        elif voices:
            engine.setProperty("voice", voices[0].id)

    except Exception as e:
        print(f"[Speech Engine Init Warning: {e}]")
        return

    _tts_running = True

    while _tts_running:
        try:
            # Wait up to 0.5s for new phrase
            text = _speech_queue.get(timeout=0.5)
            if text is None:  # Shutdown sentinel
                break

            if _voice_enabled and text.strip():
                _is_speaking = True
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception:
                    pass
                finally:
                    _is_speaking = False

            _speech_queue.task_done()
        except queue.Empty:
            continue
        except Exception:
            _is_speaking = False
            time.sleep(0.1)


def init_speech_engine():
    """
    Start the background TTS synthesizer.
    """
    global _tts_thread, _tts_running
    if not HAS_PYTTSX3:
        return False

    if _tts_thread is None or not _tts_thread.is_alive():
        _tts_running = True
        _tts_thread = threading.Thread(target=_tts_worker, daemon=True, name="JarvisTTS")
        _tts_thread.start()
    return True


def speak(text, wait=False):
    """
    Queue speech output for Jarvis.
    Non-blocking by default.
    """
    global _voice_enabled
    if not HAS_PYTTSX3 or not _voice_enabled or not text:
        return

    # Clean text of markdown, code blocks, or URLs that shouldn't be read out loud
    clean_text = _clean_for_speech(text)
    if not clean_text:
        return

    init_speech_engine()
    _speech_queue.put(clean_text)

    if wait:
        _speech_queue.join()


def _clean_for_speech(text):
    """
    Clean technical markup, URLs, or file paths so speech sounds natural.
    """
    import re
    # Remove markdown bold/italics
    cleaned = re.sub(r"[\*_`#]", "", text)
    # Remove URLs
    cleaned = re.sub(r"https?://\S+", "a link", cleaned)
    # Shorten long lists or file paths
    cleaned = re.sub(r"[a-zA-Z]:\\[\w\\\.-]+", "the file path", cleaned)
    return cleaned.strip()


def stop_speaking():
    """
    Clear pending speech.
    """
    while not _speech_queue.empty():
        try:
            _speech_queue.get_nowait()
            _speech_queue.task_done()
        except queue.Empty:
            break


def is_speaking():
    return _is_speaking


def is_voice_enabled():
    return _voice_enabled


def set_voice_enabled(enabled: bool):
    global _voice_enabled
    _voice_enabled = enabled
    if not enabled:
        stop_speaking()
    return _voice_enabled


def toggle_voice():
    global _voice_enabled
    _voice_enabled = not _voice_enabled
    if not _voice_enabled:
        stop_speaking()
    return _voice_enabled


# ============================================================
# SPEECH RECOGNITION (LISTENING MODE)
# ============================================================

def listen_for_command(prompt_callback=None):
    """
    Listen to the microphone and convert speech to text.
    Returns the recognized string, or None if unrecognized / timed out.
    """
    if not HAS_SPEECH_RECOGNITION:
        return None, "Speech recognition library not installed."

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = SPEECH_ENERGY_THRESHOLD
    recognizer.pause_threshold = SPEECH_PAUSE_THRESHOLD
    recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            if prompt_callback:
                prompt_callback("Calibrating background noise...")
            recognizer.adjust_for_ambient_noise(source, duration=0.6)

            if prompt_callback:
                prompt_callback("Listening...")

            audio = recognizer.listen(
                source,
                timeout=SPEECH_LISTEN_TIMEOUT,
                phrase_time_limit=SPEECH_PHRASE_TIME_LIMIT
            )

            if prompt_callback:
                prompt_callback("Processing audio...")

            text = recognizer.recognize_google(audio)
            return text, None

    except sr.WaitTimeoutError:
        return None, "Listening timed out (no speech detected)."
    except sr.UnknownValueError:
        return None, "Could not understand audio."
    except sr.RequestError as e:
        return None, f"Speech recognition service error: {e}"
    except Exception as e:
        return None, f"Microphone error: {e}"
