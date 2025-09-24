import streamlit as st
import speech_recognition as sr
import time
import os
from datetime import datetime
from deep_translator import GoogleTranslator
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile
from st_audiorec import st_audiorec
from gtts import gTTS
import pygame

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Audio Chatbot V2",
    page_icon="🎤",
    layout="wide"
)

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'current_language' not in st.session_state:
    st.session_state.current_language = "hi"
if 'is_playing_audio' not in st.session_state:
    st.session_state.is_playing_audio = False
if 'current_audio_file' not in st.session_state:
    st.session_state.current_audio_file = None
if 'last_processed_audio' not in st.session_state:
    st.session_state.last_processed_audio = None
if 'last_processed_text' not in st.session_state:
    st.session_state.last_processed_text = None

# Initialize AI
def initialize_ai():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            return model
        except Exception as e:
            st.error(f"AI initialization failed: {e}")
            return None
    return None

# Initialize TTS
def initialize_tts():
    try:
        # Try to initialize pygame mixer with dummy driver for headless environments
        import os
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        return True
    except Exception as e:
        st.warning(f"TTS initialization failed (audio may not be available in this environment): {e}")
        return False

# Audio recording functions - using streamlit-audiorec
def get_audio_recording():
    """Get audio recording from streamlit-audiorec component"""
    return st_audiorec()

# Speech recognition
def transcribe_audio(audio_data, language="hi"):
    try:
        recognizer = sr.Recognizer()
        
        # Save audio data to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_data)
            tmp_file.flush()
        
        # Transcribe audio
        with sr.AudioFile(tmp_file.name) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language=f"{language}-IN")
        
        # Clean up
        os.unlink(tmp_file.name)
        return text, None
        
    except sr.UnknownValueError:
        return None, "Could not understand the audio. Please speak clearly."
    except sr.RequestError as e:
        return None, f"Speech recognition service error: {e}"
    except Exception as e:
        return None, f"Audio processing error: {e}"

# Translation functions
def translate_text(text, source_lang, target_lang="en"):
    try:
        if source_lang == target_lang:
            return text, None
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated = translator.translate(text)
        return translated, None
    except Exception as e:
        return None, f"Translation error: {e}"

# Detect language of input text
def detect_language(text):
    """Simple language detection based on character patterns"""
    # Count Devanagari characters (Hindi, Marathi, etc.)
    devanagari_chars = sum(1 for char in text if '\u0900' <= char <= '\u097F')
    # Count Latin characters (English, etc.)
    latin_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)
    
    
    # If there are any Devanagari characters, it's likely Hindi
    if devanagari_chars > 0:
        return "hi"  # Hindi/Devanagari script
    else:
        return "en"  # English

# AI response generation
def generate_ai_response(prompt, model, detected_language="hi"):
    if not model:
        return "AI service is not available. Please check your API key configuration.", None
    
    try:
        # Create a more specific prompt for crop-related questions
        if detected_language == "hi":
            enhanced_prompt = f"""
            आप एक अनुभवी कृषि विशेषज्ञ हैं। उपयोगकर्ता ने पूछा: "{prompt}"
            
            निम्नलिखित जानकारी प्रदान करें:
            1. सीधा और व्यावहारिक जवाब दें
            2. फसलों के नाम, बुवाई का समय, मिट्टी की आवश्यकता बताएं
            3. सिंचाई, उर्वरक और कीट नियंत्रण की सलाह दें
            4. स्थानीय कृषि अधिकारी से संपर्क करने की सलाह दें
            5. संक्षिप्त और स्पष्ट जवाब दें
            6. हमेशा हिंदी में जवाब दें
            """
        else:
            enhanced_prompt = f"""
            You are an experienced agricultural expert. The user asked: "{prompt}"
            
            Provide the following information:
            1. Give direct and practical answers
            2. Mention crop names, planting seasons, soil requirements
            3. Advise on irrigation, fertilizers, and pest control
            4. Suggest contacting local agricultural officers
            5. Keep responses concise and clear
            6. Always respond in English
            """
        
        response = model.generate_content(enhanced_prompt)
        return response.text, None
    except Exception as e:
        return None, f"AI response error: {e}"

# Text-to-speech
def speak_text(text, language="hi", tts_available=False):
    try:
        if tts_available:
            # Clean text for better TTS - remove markdown and special characters
            cleaned_text = text
            
            # Remove markdown formatting
            import re
            cleaned_text = re.sub(r'\*+', '', cleaned_text)  # Remove asterisks
            cleaned_text = re.sub(r'#+', '', cleaned_text)   # Remove hash symbols
            cleaned_text = re.sub(r'`+', '', cleaned_text)   # Remove backticks
            cleaned_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned_text)  # Remove markdown links
            cleaned_text = re.sub(r'[^\w\s\u0900-\u097F.,!?।]', ' ', cleaned_text)  # Keep only letters, numbers, spaces, and basic punctuation
            
            # Clean punctuation
            cleaned_text = cleaned_text.replace(',', ' ').replace(';', ' ').replace(':', ' ')
            cleaned_text = ' '.join(cleaned_text.split())  # Remove extra spaces
            
            # Limit text length for TTS
            if len(cleaned_text) > 500:
                cleaned_text = cleaned_text[:500] + "..."
            
            tts = gTTS(text=cleaned_text, lang=language, slow=False)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tts.save(tmp_file.name)
                
                try:
                    pygame.mixer.music.load(tmp_file.name)
                    pygame.mixer.music.play()
                    # Return the temp file path so we can stop it later
                    return True, tmp_file.name
                except Exception as audio_error:
                    # If audio playback fails, still return success but without playback
                    st.info("Audio file generated but playback not available in this environment")
                    return True, tmp_file.name
        else:
            return False, "TTS not available"
    except Exception as e:
        return False, f"TTS error: {e}"

# Stop audio playback
def stop_audio():
    try:
        pygame.mixer.music.stop()
        return True
    except Exception as e:
        # Audio may not be available, that's okay
        return False

# Fallback responses for when AI is not available
def get_fallback_response(text, language="hi"):
    text_lower = text.lower()
    
    # Summer crops
    if any(word in text_lower for word in ["summer", "गर्मी", "ग्रीष्म", "summer crops", "गर्मी की फसल"]):
        if language == "hi":
            return "गर्मियों में आप ये फसलें उगा सकते हैं: तरबूज, खरबूजा, भिंडी, करेला, टमाटर, मिर्च, मक्का, लोबिया, मूंग। इन्हें पर्याप्त पानी और धूप की जरूरत होती है।"
        else:
            return "For summer, you can grow: watermelon, muskmelon, okra, bitter gourd, tomato, chili, maize, cowpea, moong. These need adequate water and sunlight."
    
    # Winter crops
    elif any(word in text_lower for word in ["winter", "सर्दी", "शीत", "winter crops", "सर्दी की फसल"]):
        if language == "hi":
            return "सर्दियों में आप ये फसलें उगा सकते हैं: गेहूं, चना, सरसों, आलू, प्याज, गाजर, मूली, पालक। ये ठंडे मौसम में अच्छी तरह उगती हैं।"
        else:
            return "For winter, you can grow: wheat, chickpea, mustard, potato, onion, carrot, radish, spinach. These grow well in cold weather."
    
    # Crop-related responses
    elif any(word in text_lower for word in ["फसल", "crop", "बीज", "seed", "खेती", "farming"]):
        if language == "hi":
            return "मैं आपकी फसल संबंधी जानकारी में मदद कर सकता हूं। कृपया बताएं कि आप कौन सी फसल के बारे में जानना चाहते हैं - जैसे गेहूं, चावल, सब्जियां, या फल।"
        else:
            return "I can help you with crop information. Please tell me which crop you want to know about - like wheat, rice, vegetables, or fruits."
    
    # Weather-related responses
    elif any(word in text_lower for word in ["मौसम", "weather", "बारिश", "rain", "तापमान", "temperature"]):
        if language == "hi":
            return "मौसम की जानकारी के लिए आप अपने स्थानीय मौसम विभाग से संपर्क कर सकते हैं या मौसम ऐप का उपयोग कर सकते हैं।"
        else:
            return "For weather information, you can contact your local weather department or use a weather app."
    
    # General farming advice
    elif any(word in text_lower for word in ["सलाह", "advice", "मदद", "help", "कैसे", "how"]):
        if language == "hi":
            return "मैं आपकी कृषि संबंधी समस्याओं में मदद कर सकता हूं। कृपया अपनी समस्या को विस्तार से बताएं।"
        else:
            return "I can help you with agricultural problems. Please describe your issue in detail."
    
    # Default response
    else:
        if language == "hi":
            return f"मैंने आपकी बात सुनी: '{text}'। कृपया अपनी कृषि संबंधी जरूरतों के बारे में बताएं।"
        else:
            return f"I heard you say: '{text}'. Please tell me about your agricultural needs."

# Main UI
def main():
    st.title("🎤 Audio Chatbot V2")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        
        # Language selection
        language_options = {
            "Hindi": "hi",
            "English": "en",
            "Marathi": "mr",
            "Tamil": "ta",
            "Telugu": "te",
            "Bengali": "bn",
            "Gujarati": "gu",
            "Kannada": "kn",
            "Malayalam": "ml",
            "Urdu": "ur"
        }
        
        selected_language = st.selectbox(
            "Select Language",
            options=list(language_options.keys()),
            index=0
        )
        st.session_state.current_language = language_options[selected_language]
        
        # AI settings
        use_ai = st.checkbox("Enable AI Responses", value=True)
        auto_play = st.checkbox("Auto-play responses", value=True)
        
        # Clear conversation
        if st.button("🗑️ Clear Conversation", help="Clear all chat history"):
            st.session_state.conversation_history = []
            st.session_state.last_processed_audio = None
            st.session_state.last_processed_text = None
            st.session_state.is_playing_audio = False
            if st.session_state.current_audio_file:
                try:
                    os.unlink(st.session_state.current_audio_file)
                except:
                    pass
                st.session_state.current_audio_file = None
            st.rerun()
        
        # Refresh page
        if st.button("🔄 Refresh Page", help="Reload the entire page"):
            st.rerun()
    
    # Initialize components
    ai_model = initialize_ai() if use_ai else None
    tts_available = initialize_tts()
    
    # Audio controls
    if st.session_state.is_playing_audio:
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("⏹️ Stop Audio", type="secondary"):
                stop_audio()
                st.session_state.is_playing_audio = False
                if st.session_state.current_audio_file and os.path.exists(st.session_state.current_audio_file):
                    os.unlink(st.session_state.current_audio_file)
                st.session_state.current_audio_file = None
                st.rerun()
        with col2:
            st.write("🔊 Playing...")
    
    # Display conversation history
    st.subheader("Conversation")
    for message in st.session_state.conversation_history:
        if message['type'] == 'user':
            st.write(f"**You:** {message['text']} *({message['timestamp']})*")
        else:
            # Display bot response in a nice box
            with st.container():
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px 0;">
                    <strong>🤖 Bot:</strong> {message['text']}<br>
                    <small style="color: #666;">{message['timestamp']}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Add speak button for each response
                if st.button(f"🔊 Speak", key=f"speak_{message['timestamp']}"):
                    # Detect language of the response text
                    response_lang = detect_language(message['text'])
                    speak_success, speak_result = speak_text(message['text'], response_lang, tts_available)
                    if speak_success:
                        st.session_state.is_playing_audio = True
                        st.session_state.current_audio_file = speak_result
                        st.rerun()
                    else:
                        st.warning(f"TTS Warning: {speak_result}")
    
    # Audio recording
    st.subheader("🎤 Record Audio for Instructions/Questions")
    
    # Add helpful instructions
    with st.expander("📝 Recording Instructions"):
        st.write("**Instructions:**")
        st.write("1. ▶️ Click Start to begin recording")
        st.write("2. ⏹️ Click Stop to end recording")
        st.write("3. 🔄 If you encounter an error, click Reset and start again")
    
    audio_data = get_audio_recording()
    
    if audio_data is not None and audio_data != st.session_state.last_processed_audio:
        with st.spinner("Processing audio..."):
            # Transcribe
            transcribed_text, error = transcribe_audio(audio_data, st.session_state.current_language)
            
            if error:
                st.error(f"Error: {error}")
            elif transcribed_text and transcribed_text != st.session_state.last_processed_text:
                # Update last processed items
                st.session_state.last_processed_audio = audio_data
                st.session_state.last_processed_text = transcribed_text
                
                # Add to conversation
                timestamp = datetime.now().strftime("%H:%M:%S")
                st.session_state.conversation_history.append({
                    'type': 'user',
                    'text': transcribed_text,
                    'timestamp': timestamp
                })
                
                # Detect the language of the transcribed text
                detected_lang = detect_language(transcribed_text)
                
                # Generate AI response in the same language
                if use_ai and ai_model:
                    with st.spinner("Generating AI response..."):
                        ai_response, ai_error = generate_ai_response(transcribed_text, ai_model, detected_lang)
                        
                        if ai_error:
                            st.error(f"AI Error: {ai_error}")
                            ai_response = get_fallback_response(transcribed_text, detected_lang)
                else:
                    ai_response = get_fallback_response(transcribed_text, detected_lang)
                
                # Add bot response to conversation
                st.session_state.conversation_history.append({
                    'type': 'bot',
                    'text': ai_response,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })
                
                # Speak the response in the detected language
                if auto_play:
                    with st.spinner("Speaking response..."):
                        speak_success, speak_result = speak_text(ai_response, detected_lang, tts_available)
                        if speak_success:
                            st.session_state.is_playing_audio = True
                            st.session_state.current_audio_file = speak_result
                        else:
                            st.warning(f"TTS Warning: {speak_result}")
                
                st.rerun()
    
    # Text input as alternative
    st.subheader("Or type your message:")
    user_input = st.text_input("Type your message here:", key="text_input", placeholder="Ask about crops, farming, or agriculture...")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        send_clicked = st.button("Send", key="send_btn", type="primary")
    
    if send_clicked and user_input and user_input.strip():
        # Check if this is a new message
        if user_input != st.session_state.last_processed_text:
            # Update last processed text
            st.session_state.last_processed_text = user_input
            
            # Add user message
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.conversation_history.append({
                'type': 'user',
                'text': user_input,
                'timestamp': timestamp
            })
            
            # Detect the language of the input text
            detected_lang = detect_language(user_input)
            
            # Generate response in the same language
            if use_ai and ai_model:
                with st.spinner("Generating response..."):
                    response, error = generate_ai_response(user_input, ai_model, detected_lang)
                    if error:
                        response = get_fallback_response(user_input, detected_lang)
            else:
                response = get_fallback_response(user_input, detected_lang)
            
            # Add bot response
            st.session_state.conversation_history.append({
                'type': 'bot',
                'text': response,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
            
            # Speak response in the detected language
            if auto_play:
                speak_success, speak_result = speak_text(response, detected_lang, tts_available)
                if speak_success:
                    st.session_state.is_playing_audio = True
                    st.session_state.current_audio_file = speak_result
                else:
                    st.warning(f"TTS Warning: {speak_result}")
            
            st.rerun()
        else:
            st.info("Same message as before. Please type a new message.")
    elif send_clicked and not user_input.strip():
        st.warning("Please enter a message first.")

if __name__ == "__main__":
    main()
