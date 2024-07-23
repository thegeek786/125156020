import streamlit as st
import os
import speech_recognition as sr
import pyttsx3
import wave
import pyaudio
import threading
from googletrans import Translator

# Initialize text-to-speech engine and translator
engine = pyttsx3.init()
translator = Translator()

# Global variables for recording
recording = False
audio_file = "recorded_audio.wav"
translated_audio_file = "translated_audio.wav"
stop_recording_event = threading.Event()

# Define Streamlit UI
st.title("Speech-to-Text and Translation")

if 'recording' not in st.session_state:
    st.session_state.recording = False

# Functions for recording
def record_audio():
    global stop_recording_event

    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

    frames = []

    while not stop_recording_event.is_set():
        data = stream.read(1024)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(audio_file, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(frames))

# Start recording
if st.button("Start Recording"):
    if not st.session_state.recording:
        st.session_state.recording = True
        stop_recording_event.clear()
        thread = threading.Thread(target=record_audio)
        thread.start()
        st.success("Recording started")
    else:
        st.warning("Already recording")

# Stop recording
if st.button("Stop Recording"):
    if st.session_state.recording:
        stop_recording_event.set()  # Signal to stop recording
        st.session_state.recording = False
        st.success("Recording stopped")
    else:
        st.warning("No recording in progress")

# Play recorded audio
if st.button("Play Audio"):
    if os.path.exists(audio_file):
        st.audio(audio_file)
    else:
        st.error("No audio file found")

# Speech-to-text conversion
if st.button("Convert Speech to Text"):
    if os.path.exists(audio_file):
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                st.text_area("Transcribed Text", value=text, height=200)
            except sr.UnknownValueError:
                st.error("Speech recognition could not understand audio")
            except sr.RequestError:
                st.error("Could not request results from Google Speech Recognition service")
    else:
        st.error("No audio file found")

# Text input for translation
text = st.text_input("Text for Translation")

# Language selection for translation
target_lang = st.selectbox("Target Language", options=["en", "es", "fr", "de", "hi", "ta", "te", "ar"])

# Translate text
if st.button("Translate"):
    if text:
        try:
            translated = translator.translate(text, dest=target_lang)
            translated_text = translated.text

            # Convert the translated text to speech
            engine.save_to_file(translated_text, translated_audio_file)
            engine.runAndWait()

            st.success("Translation successful")
            st.text_area("Translated Text", value=translated_text, height=200)

            # Play translated audio
            if os.path.exists(translated_audio_file):
                st.audio(translated_audio_file)
            else:
                st.error("Failed to play translated audio")
        except Exception as e:
            st.error(f"Translation failed: {str(e)}")
    else:
        st.error("No text provided for translation")

# Run the Streamlit app
if __name__ == '__main__':
    st.set_option('deprecation.showfileUploaderEncoding', False)
    st.write("App is running...")
