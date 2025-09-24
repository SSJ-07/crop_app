import streamlit as st
import speech_recognition as sr
from googlesearch import search

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
    try:
        for j in search(query, num_results=5, sleep_interval=2):
            results.append(j)
    except Exception as e:
        st.error(f"Search error: {e}")
        # Fallback to a simple search result
        results = [f"Search for: {query}"]
    return results


# Settings for LLM
# gemini API - only configure if API key is available
gemini_model = None
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
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
    except Exception as e:
        st.warning(f"⚠️ Could not initialize Gemini AI: {e}")
        gemini_model = None
else:
    st.info("ℹ️ No Google API key found. AI responses will use a simple fallback.")


# function number 4
def generate_content_with_LLM(prompt):
    if gemini_model is None:
        # Fallback response when no API key is available
        return f"Based on your query '{prompt}', here's some helpful information:\n\n" \
               f"• This is a crop-related query about agricultural practices\n" \
               f"• For detailed information, please check the search results above\n" \
               f"• Consider consulting local agricultural experts for specific advice\n\n" \
               f"Note: To get AI-powered responses, please add your Google API key to the environment variables."
    
    try:
        response = gemini_model.generate_content(prompt)
        output = response.text
        return output

    except Exception as e:
        logging.error(f"Error during content generation - {e}")
        return f"I encountered an error while generating a response. Here's what I can tell you about your query '{prompt}':\n\n" \
               f"• This appears to be a question about crops and agriculture\n" \
               f"• Please check the search results above for more detailed information\n" \
               f"• For specific agricultural advice, consider consulting local farming experts"


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
    if not text or not text.strip():
        st.warning("⚠️ No text provided for audio generation")
        return None
        
    cleaned_text = remove_emojis_and_symbols(text)
    
    # Limit text length to avoid issues
    if len(cleaned_text) > 500:
        cleaned_text = cleaned_text[:500] + "..."
    
    try:
        # Use a more reliable language code mapping
        lang_codes = {
            "hi": "hi",  # Hindi
            "mr": "mr",  # Marathi
            "ta": "ta",  # Tamil
            "te": "te",  # Telugu
            "bn": "bn",  # Bengali
            "gu": "gu",  # Gujarati
            "kn": "kn",  # Kannada
            "ml": "ml",  # Malayalam
            "ur": "ur",  # Urdu
        }
        
        lang_code = lang_codes.get(language, "en")  # Default to English if language not found
        
        
        tts = gTTS(text=cleaned_text, lang=lang_code, slow=False)
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        
        # Check if audio was generated successfully
        audio_data = audio_bytes.getvalue()
        if audio_data and len(audio_data) > 0:
            st.success(f"✅ Audio bytes generated successfully ({len(audio_data)} bytes)")
            # Reset the BytesIO object for proper reading
            audio_bytes.seek(0)
            return audio_bytes
        else:
            st.error("❌ Audio generation produced empty result")
            return None
            
    except Exception as e:
        st.error(f"❌ Text-to-speech error: {e}")
        st.info("💡 Trying with English as fallback...")
        
        # Fallback to English
        try:
            tts = gTTS(text=cleaned_text, lang="en", slow=False)
            audio_bytes = BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            return audio_bytes
        except Exception as e2:
            st.error(f"❌ Fallback audio generation also failed: {e2}")
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
        st.write("**Instructions:**")
        st.write("1. ▶️ Click Start to begin recording")
        st.write("2. ⏹️ Click Stop to end recording")
        st.write("3. 🔄 If you encounter an error, click Reset and start again")

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
            try:
                audio_bytes = text_to_speech(regional_output, selected_language)
                if audio_bytes and audio_bytes.getvalue():
                    try:
                        # Try different audio formats for better compatibility
                        audio_data = audio_bytes.getvalue()
                        st.audio(audio_data, format="audio/mpeg")
                        st.success("✅ Audio generated and ready to play!")
                    except Exception as audio_error:
                        st.error(f"❌ Audio playback error: {audio_error}")
                        st.info("💡 Audio was generated but couldn't be played. You can still read the text response above.")
                        
                        # Try alternative approach - save to temporary file
                        try:
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                                tmp_file.write(audio_data)
                                tmp_file.flush()
                                st.audio(tmp_file.name, format="audio/mpeg")
                                st.success("✅ Audio generated and ready to play! (Alternative method)")
                        except Exception as alt_error:
                            st.error(f"❌ Alternative audio method also failed: {alt_error}")
                            st.info("💡 You can still read the text response above.")
                else:
                    st.warning("⚠️ Unable to generate audio for the answer.")
                    st.info("💡 This might be due to text length, language support, or network issues.")
            except Exception as e:
                st.error(f"❌ Audio generation failed: {e}")
                st.info("💡 You can still read the text response above.")
        else:
            st.error("❌ No audio data received. Please try recording again.")


if __name__ == "__main__":
    main()
