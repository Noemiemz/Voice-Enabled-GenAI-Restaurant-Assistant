from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO
import base64
import logging

from data.mongodb import MongoDBManager
from models.tts import TTSEngine
from models.stt import WhisperWrapper
from models.agents import ConversationState, create_supervisor_agent

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
socket = SocketIO(app, cors_allowed_origins=["http://localhost:3000"])

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
    audio_bytes = data['audio_data']
    audio_np = np.frombuffer(audio_bytes, dtype=np.float32)

    logger.info("Transcribing audio...")
    result = stt_model.transcribe(audio_np)
    socket.emit('transcription_result', {'text': result})

@socket.on('synthesize_speech')
def synthesize_speech(data):
    messages = data['messages']
    llm_response = supervisor_agent.stream({"messages": messages})
    lang = "fr" # TO BE CHANGED
    for step in llm_response:
        for update in step.values():
            for message in update.get("messages", []):
                tts_audio = tts_engine.stream_speech(lang, message.text)
                for audio_chunk in tts_audio:
                    socket.emit('llm_audio_chunk', audio_chunk)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    conversation_state.clear_history()
    return {'status': 'history_cleared'}, 200

if __name__ == '__main__':
    logger.info("Starting Flask-SocketIO server...")
    socket.run(app, host='0.0.0.0', port=5000, debug=True)