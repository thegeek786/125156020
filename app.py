import streamlit as st
import sounddevice as sd
import numpy as np
import wave
import threading
from googletrans import Translator
import speech_recognition as sr
import pyttsx3
import tempfile

# Initialize text-to-speech engine and translator
engine = pyttsx3.init()
translator = Translator()

# Global variables for recording
stop_recording_event = threading.Event()

def record_audio():
    fs = 44100  # Sample rate
    channels = 1  # Number of audio channels
    dtype = 'int16'  # Data type of the audio samples

    frames_queue = []

    def callback(indata, frames, time, status):
        if stop_recording_event.is_set():
            raise sd.CallbackStop()
        frames_queue.append(indata.copy())

    with sd.InputStream(samplerate=fs, channels=channels, dtype=dtype, callback=callback):
        stop_recording_event.wait()  # Wait until recording is stopped

    audio_data = np.concatenate(frames_queue, axis=0)
    return audio_data, fs, channels, dtype

def save_audio_file(audio_data, fs, channels, dtype):
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with wave.open(temp_audio_file.name, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(np.dtype(dtype).itemsize)
        wf.setframerate(fs)
        wf.writeframes(audio_data.tobytes())
    return temp_audio_file.name

def convert_speech_to_text(filename):
    recognizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return "Speech recognition could not understand audio"
        except sr.RequestError:
            return "Could not request results from Google Speech Recognition service"

def text_to_speech(text, filename):
    engine.save_to_file(text, filename)
    engine.runAndWait()

st.title("Speech-to-Text and Translation")

# Check if recording state exists in session state
if "recording" not in st.session_state:
    st.session_state.recording = False

# Check if audio file path exists in session state
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None

if st.button("Start Recording"):
    if not st.session_state.recording:
        st.session_state.recording = True
        stop_recording_event.clear()
        thread = threading.Thread(target=lambda: st.session_state.update(audio_data=record_audio()))
        thread.start()
        st.success("Recording started")
    else:
        st.warning("Already recording")

if st.button("Stop Recording"):
    if st.session_state.recording:
        stop_recording_event.set()  # Signal to stop recording
        st.session_state.recording = False
        thread.join()
        audio_data, fs, channels, dtype = st.session_state.audio_data
        st.session_state.audio_file = save_audio_file(audio_data, fs, channels, dtype)
        st.success("Recording stopped")
    else:
        st.warning("No recording in progress")

if st.session_state.audio_file:
    if st.button("Play Audio"):
        st.audio(st.session_state.audio_file, format="audio/wav")

    if st.button("Convert Speech to Text"):
        transcribed_text = convert_speech_to_text(st.session_state.audio_file)
        st.session_state.transcribed_text = transcribed_text
        st.text_area("Transcribed Text", transcribed_text)

text_to_translate = st.text_input("Text for Translation")
target_lang = st.selectbox("Target Language", ["en", "es", "fr", "de", "hi", "ta", "te", "ar"])

if text_to_translate and st.button("Translate"):
    try:
        translated = translator.translate(text_to_translate, dest=target_lang)
        translated_text = translated.text
        st.session_state.translated_text = translated_text
        st.success(f"Translated Text: {translated_text}")

        translated_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        text_to_speech(translated_text, translated_audio_file.name)
        st.session_state.translated_audio_file = translated_audio_file.name

    except Exception as e:
        st.error(f"Translation failed: {str(e)}")

if "translated_audio_file" in st.session_state and st.button("Play Translated Audio"):
    st.audio(st.session_state.translated_audio_file, format="audio/wav")
