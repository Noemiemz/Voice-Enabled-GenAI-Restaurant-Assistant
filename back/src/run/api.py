from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

import numpy as np
import base64

from data.mongodb import MongoDBManager
from models.tts import TTSEngine
from models.stt import WhisperWrapper
from models.agents import ConversationState, create_supervisor_agent

from settings import AVAILABLE_VOICES

app = Flask(__name__)
app.config["DEBUG"] = True
CORS(app, origins=["http://localhost:3000"])
socket = SocketIO(
    app, 
    cors_allowed_origins=["http://localhost:3000"],
    max_http_buffer_size=100 * 1024 * 1024,  # 100MB max message size
    ping_timeout=60,
    ping_interval=25
)

# Initialize models and agents
db = MongoDBManager()
stt_model = WhisperWrapper()
tts_engine = TTSEngine()
conversation_state = ConversationState()
supervisor_agent = create_supervisor_agent(db, conversation_state)

@app.route('/health', methods=['GET'])
def health_check():
    return {'status': 'ok'}, 200

@socket.on('transcribe_audio')
def transcribe_audio(data):
    try:
        audio_data = data['audio_data']
        audio_bytes = base64.b64decode(audio_data)
        audio_np = np.frombuffer(audio_bytes, dtype=np.float32)
        
        print("Transcribing audio...")
        transcription, user_language = stt_model.transcribe(audio_np)
        print(f"Transcription result: {transcription}")

        if user_language not in AVAILABLE_VOICES:
            user_language = "en"  # Default to English if language not supported

        emit('transcription_result', {'text': transcription, 'language': user_language})
    except Exception as e:
        print(f"Error in transcribe_audio: {e}")
        import traceback
        traceback.print_exc()
        emit('transcription_error', {'error': str(e)})

@socket.on('synthesize_speech')
def synthesize_speech(data):
    try:
        messages = data['messages']
        language = data['language']
        print(f"Generating LLM response with language: {language}")
        print(f"Messages received: {messages}")
        
        llm_response = supervisor_agent.invoke({"messages": messages})['messages'][-1].content
        print(f"LLM response: {llm_response}")
        
        emit('llm_text_response', {'text': llm_response})
        
        print(f"Starting TTS generation for language: {language}")
        for audio_chunk, sample_rate in tts_engine.stream_speech(language, llm_response):
            print(f"Generated audio chunk: {len(audio_chunk)} samples at {sample_rate}Hz")
            audio_bytes = audio_chunk.tobytes()
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            emit('llm_audio_chunk', {'audio': audio_b64, 'sample_rate': sample_rate})
        
        print("TTS generation completed")
    except Exception as e:
        print(f"Error in synthesize_speech: {e}")
        import traceback
        traceback.print_exc()
        emit('synthesis_error', {'error': str(e)})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    conversation_state.clear_history()
    return {'status': 'history_cleared'}, 200

if __name__ == '__main__':
    socket.run(app, host='0.0.0.0', port=5000, debug=True)