import speech_recognition as sr

def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe audio file to text using SpeechRecognition library
    """
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)
            
            # Use Google Web Speech API (requires internet connection)
            text = recognizer.recognize_google(audio_data, language="fr-FR")
            print(f"Successfully transcribed: {text}")
            return text
            
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return ""
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return ""