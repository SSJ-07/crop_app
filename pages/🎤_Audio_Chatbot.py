import streamlit as st
import speech_recognition as sr
import googlesearch

import logging
from deep_translator import GoogleTranslator
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import time
import re
import os
from dotenv import load_dotenv
from st_audiorec import st_audiorec

load_dotenv()

st.set_page_config("Audio Chatbot", page_icon=":microphone:")

languages = {
    "Hindi": "hi",
    "Marathi": "mr",
    "Tamil": "ta",
    "Telugu": "te",
    "Bengali": "bn",
    "Gujarati": "gu",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Urdu": "ur",
}

language = st.selectbox(
    "Which Language would you like?",
    (
        "Hindi",
        "Marathi",
        "Tamil",
        "Telugu",
        "Bengali",
        "Gujarati",
        "Kannada",
        "Urdu",
        "Malayalam",
    ),
)

st.write("You selected:", language)
selected_language = languages[language]


# Function number 1
def transcribe_audio(audio_data):
    recognizer = sr.Recognizer()
    
    # Configure recognizer for better accuracy
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    
    audio_bytes = BytesIO(audio_data)
    
    try:
        with sr.AudioFile(audio_bytes) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.record(source)
        
        # Check if audio is too short or silent
        if len(audio.frame_data) < 1000:  # Very short audio
            return None, "Audio is too short. Please speak for at least 1 second."
        
        # this uses the google speech API for different languages. Generally not used in production,
        # but it will do for our purpose as it eliminates the need for Google Cloud Authentication which
        # is quite troublesome
        text = recognizer.recognize_google(audio, language=f"{selected_language}-IN")
        
        # Check if the recognized text is meaningful
        if not text or len(text.strip()) < 2:
            return None, "No clear speech detected. Please speak clearly and try again."
        
        return text, None
        
    except sr.UnknownValueError:
        return None, "Could not understand the audio. Please speak clearly and try again."
    except sr.RequestError as e:
        return None, f"Speech recognition service error: {e}. Please check your internet connection."
    except Exception as e:
        return None, f"Audio processing error: {e}. Please try recording again."


# Function number 2
def translate_to_english(text, source_language):
    if text is None:
        return "Unable to translate: No input text"
    try:
        translator = GoogleTranslator(source=source_language, target="en")
        translation = translator.translate(text)
        return translation
    except Exception as e:
        logging.error(f"Error during translation: {e}")
        return "Unable to translate due to an error"


# function number 3
# does simple google searches and gets the top links
def search_google(query):
    results = []
    for j in googlesearch.search(query, num=5, stop=5, pause=2):
        results.append(j)
    return results


# Settings for LLM
# gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# configuring the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]

# actually creates the LLM responsible for giving the output
gemini_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    safety_settings=safety_settings,
    generation_config=generation_config,
)


# function number 4
def generate_content_with_LLM(prompt):
    try:
        response = gemini_model.generate_content(prompt)
        # response2 = gemini_model.
        output = response.text
        return output

    except Exception as e:
        logging.error(f"Error during content generation - {e}")
        return "Encoutered error, please try again later!"


# function number 5 to translate back into regional language
def translate_to_regional_language(text, target_language):
    try:
        translator = GoogleTranslator(source="en", target=target_language)
        translation = translator.translate(text)
        return translation
    except Exception as e:
        logging.error(f"Error during translation to regional language: {e}")
        return "Unable to translate to regional language due to an error"


# function number 5
def text_to_speech(text, language):
    cleaned_text = remove_emojis_and_symbols(text)
    try:
        tts = gTTS(text=cleaned_text, lang=language)
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except Exception as e:
        logging.error(f"Error during text-to-speech conversion: {e}")
        return None


# helper function to remove emojis and symbols from the regional language output text
def remove_emojis_and_symbols(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text)


def main():
    st.title("Regional Language Audio Chatbot with Google Search and Summarization")

    st.write(
        f"Speak in {language} and the chatbot will transcribe your speech. It will also display search results based on your speech along with summaries of each link."
    )
    
    # Add helpful instructions
    with st.expander("📝 Recording Instructions"):
        st.write("**For best results:**")
        st.write("1. 🎤 Use a good quality microphone")
        st.write("2. 🔇 Minimize background noise")
        st.write("3. 🗣️ Speak clearly and at normal pace")
        st.write("4. ⏱️ Record for at least 2-3 seconds")
        st.write("5. 📍 Ensure stable internet connection")
        st.write("6. 🔄 If recognition fails, try speaking slower or louder")

    wave_audio_data = st_audiorec()

    # button for audio instructions
    if wave_audio_data != None:
        st.info("Processing audio...")

        # transcribe audio using fn1
        text, error = transcribe_audio(wave_audio_data)

        # display transcribed text or error
        if error:
            st.error(f"❌ {error}")
            st.info("💡 **Tips for better recognition:**")
            st.write("- Speak clearly and at a normal pace")
            st.write("- Ensure good microphone quality")
            st.write("- Reduce background noise")
            st.write("- Speak for at least 2-3 seconds")
        elif text:
            st.success(f"🎤 **You said:** {text}")
            
            st.info("🔄 Translating text to English...")

            # using fn2
            english_text = translate_to_english(text, selected_language)
            st.success(f"🌐 **Translated Query:** {english_text}")

            # fn3
            # call the google search method and display relevant links
            st.info("🔍 Searching Google...")
            results = search_google(english_text)
            with st.expander("📋 Google Search Results:"):
                for i, result in enumerate(results, start=1):
                    st.write(f"{i}. {result}")

            st.info("🤖 Generating AI response...")

            # fn4
            llm_output = generate_content_with_LLM(english_text)

            def stream_data():
                for word in llm_output.split(" "):
                    yield word + " "
                    time.sleep(0.002)

            st.write("**AI Response:**")
            st.write_stream(stream_data)

            # fn5
            st.info("🔄 Translating response to regional language...")
            regional_output = translate_to_regional_language(llm_output, selected_language)
            st.write(f"**{language} Response:** {regional_output}")

            # fn6
            st.info("🔊 Generating audio...")
            audio_bytes = text_to_speech(regional_output, selected_language)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3", start_time=0)
                st.success("✅ Audio generated successfully!")
            else:
                st.warning("⚠️ Unable to generate audio for the answer.")
        else:
            st.error("❌ No audio data received. Please try recording again.")


if __name__ == "__main__":
    main()
