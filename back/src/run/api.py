import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

import numpy as np
import base64
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

from utils.logger import log_function_execution
from data.mongodb import MongoDBManager
from models.tts import TTSEngine
from models.stt import WhisperWrapper
from models.agents import ConversationState, create_supervisor_agent

from settings import AVAILABLE_VOICES


app = Flask(__name__)
app.config["DEBUG"] = True
CORS(app, origins=["http://localhost:3000", "http://frontend:3000"], supports_credentials=True)
socket = SocketIO(
    app, 
    cors_allowed_origins=["http://localhost:3000", "http://frontend:3000"],
    async_mode="threading",
    max_http_buffer_size=100 * 1024 * 1024,  # 100MB max message size
    ping_timeout=60,
    ping_interval=25,
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
    audio_data = data['audio_data']
    audio_bytes = base64.b64decode(audio_data)
    audio_np = np.frombuffer(audio_bytes, dtype=np.float32)
    
    print("Transcribing audio...")
    transcription, user_language = stt_model.transcribe(audio_np)
    print(f"Transcription result: {transcription}")

    error = None
    if user_language not in AVAILABLE_VOICES:
        user_language = "en"  # Default to English if language not supported
        error = "Selected language not supported for TTS. Defaulted to English."

    emit('transcription_result', {'text': transcription, 'language': user_language, 'error': error})

@socket.on('synthesize_speech')
def synthesize_speech(data):
    messages = data['messages']
    language = data['language']
    print(f"Generating LLM response with language: {language}")
    print(f"Messages received: {messages}")
    start = time.time()
    llm_response = supervisor_agent.invoke({"messages": messages})['messages'][-1].content
    end = time.time()
    log_function_execution("LLM Response Generation", end - start)
    
    print(f"LLM response: {llm_response}")
    
    emit('llm_text_response', {'text': llm_response})
    
    print(f"Starting TTS generation for language: {language}")
    start_tts = time.time()
    for audio_chunk, sample_rate in tts_engine.stream_speech(language, llm_response):
        print(f"Generated audio chunk: {len(audio_chunk)} samples at {sample_rate}Hz")
        audio_bytes = audio_chunk.tobytes()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        emit('llm_audio_chunk', {'audio': audio_b64, 'sample_rate': sample_rate})
    end_tts = time.time()
    log_function_execution("TTS Generation", end_tts - start_tts)
    print("TTS generation completed")

@app.route('/clear_history', methods=['POST'])
def clear_history():
    conversation_state.clear_history()
    return {'status': 'history_cleared'}, 200

@app.route('/logs', methods=['GET'])
def get_logs():
    """Endpoint to retrieve all logs"""
    logs_folder = os.path.join(os.path.dirname(__file__), "..", "logs")
    logs = []
    
    if os.path.exists(logs_folder):
        # Get all log files
        log_files = sorted(Path(logs_folder).glob("*.log"), reverse=True)
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"Error reading log file {log_file}: {e}")
    
    return jsonify(logs), 200

@app.route('/logs/stats', methods=['GET'])
def get_logs_stats():
    """Endpoint to retrieve statistics about logs"""
    logs_folder = os.path.join(os.path.dirname(__file__), "..", "logs")
    logs = []
    
    if os.path.exists(logs_folder):
        log_files = sorted(Path(logs_folder).glob("*.log"), reverse=True)
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"Error reading log file {log_file}: {e}")
    
    # Calculate statistics
    stats = {
        'total_logs': len(logs),
        'by_level': {},
        'by_function': {},
        'by_object_name': {},
        'by_hour': {},
        'avg_execution_time_by_function': {},
    }
    
    for log in logs:
        # Count by level
        level = log.get('level', 'UNKNOWN')
        stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
        
        # Count by function
        function_name = log.get('function_name', 'UNKNOWN')
        stats['by_function'][function_name] = stats['by_function'].get(function_name, 0) + 1
        
        # Count by object name
        object_name = log.get('object_name', 'unknown')
        stats['by_object_name'][object_name] = stats['by_object_name'].get(object_name, 0) + 1
        
        # Count by hour
        try:
            timestamp = datetime.fromisoformat(log.get('timestamp', ''))
            hour = timestamp.strftime('%Y-%m-%d %H:00')
            stats['by_hour'][hour] = stats['by_hour'].get(hour, 0) + 1
        except:
            pass
        
        # Calculate average execution time by function
        if 'execution_time_seconds' in log:
            function = log.get('function_name', 'UNKNOWN')
            if function not in stats['avg_execution_time_by_function']:
                stats['avg_execution_time_by_function'][function] = {'total': 0, 'count': 0}
            stats['avg_execution_time_by_function'][function]['total'] += log['execution_time_seconds']
            stats['avg_execution_time_by_function'][function]['count'] += 1
    
    # Calculate averages
    for function, data in stats['avg_execution_time_by_function'].items():
        if data['count'] > 0:
            stats['avg_execution_time_by_function'][function] = round(data['total'] / data['count'], 4)
    
    return jsonify(stats), 200

if __name__ == '__main__':
    socket.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)