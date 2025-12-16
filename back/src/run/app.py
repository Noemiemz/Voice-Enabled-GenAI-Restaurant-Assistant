from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import tempfile
import numpy as np
from datetime import datetime
import json


import dotenv
dotenv.load_dotenv()

# Add the parent directory to the path so we can import from models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import our models
from models.llm import MistralWrapper
from models.tts import generate_speech
from models.stt import transcribe_audio

app = Flask(__name__)
CORS(app)

# Load environment variables
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")


# Initialize LLM
llm = MistralWrapper(api_key=MISTRAL_API_KEY)

# Initialize in-memory storage (MongoDB will be lazy-loaded when needed)
USE_MONGODB = False
reservations = []
menu = {
    "categories": [
        {
            "name": "Entrées",
            "items": [
                {"name": "Terrine de campagne", "price": "12€", "description": "Maison avec pain grillé"},
                {"name": "Salade niçoise", "price": "14€", "description": "Thon, œufs, olives, légumes frais"},
                {"name": "Soupe à l'oignon", "price": "10€", "description": "Gratinée au fromage"}
            ]
        },
        {
            "name": "Plats principaux",
            "items": [
                {"name": "Boeuf bourguignon", "price": "22€", "description": "Viande fondante, champignons, carottes"},
                {"name": "Poulet rôti", "price": "18€", "description": "Avec pommes de terre et légumes de saison"},
                {"name": "Filet de saumon", "price": "20€", "description": "Sauce citronnée, riz basmati"}
            ]
        },
        {
            "name": "Desserts",
            "items": [
                {"name": "Tarte tatin", "price": "9€", "description": "Pommes caramélisées, crème fraîche"},
                {"name": "Crème brûlée", "price": "8€", "description": "Vanille de Madagascar"},
                {"name": "Mousse au chocolat", "price": "7€", "description": "Chocolat noir 70%"}
            ]
        }
    ]
}

def get_db():
    """Lazy-load MongoDB connection"""
    global USE_MONGODB
    if not USE_MONGODB:
        try:
            from models.mongodb import db
            if db.connected:
                USE_MONGODB = True
                print("[SUCCESS] MongoDB connected successfully")
            else:
                print("[INFO] MongoDB not available, using in-memory storage")
        except Exception as e:
            print(f"[WARNING] MongoDB not available: {e}")
            print("[INFO] Using in-memory storage")
            return None
    
    # Import db here to ensure it's available
    from models.mongodb import db
    return db if USE_MONGODB else None

@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    """
    Process audio recording: convert speech to text, then get LLM response
    """
    try:
        # Check if audio file is provided
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        
        # Validate audio file
        if audio_file.filename == '':
            return jsonify({"error": "Empty audio filename"}), 400
        
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            return jsonify({"error": "Invalid audio file type"}), 400
        
        # Check file size
        audio_file.seek(0, 2)  # Move to end of file
        file_size = audio_file.tell()
        audio_file.seek(0)  # Reset to beginning
        
        if file_size == 0:
            return jsonify({"error": "Empty audio file"}), 400
        
        if file_size < 1024:  # Less than 1KB
            return jsonify({"error": "Audio file too short"}), 400
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            audio_file.save(temp_audio.name)
            temp_audio_path = temp_audio.name
        
        print(f"Audio file saved: {temp_audio_path}, size: {file_size} bytes")
        
        # Transcribe audio to text using STT
        user_text = transcribe_audio(temp_audio_path)
        
        if not user_text:
            os.unlink(temp_audio_path)
            return jsonify({"error": "Could not transcribe audio - please speak clearly"}), 400
        
        print(f"Transcribed text: {user_text}")
        
        # Get LLM response
        text_response, history = llm.generate(user_text)
        
        # Clean up temporary file
        os.unlink(temp_audio_path)
        
        return jsonify({
            "textResponse": text_response,
            "history": history
        })
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Audio processing error: {str(e)}"}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Handle text-based chat messages
    """
    try:
        data = request.get_json()
        message = data.get('message')
        history = data.get('history', [])
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        # Get LLM response
        text_response, updated_history = llm.generate(message, history)
        
        return jsonify({
            "textResponse": text_response,
            "history": updated_history
        })
        
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/menu', methods=['GET'])
def get_menu():
    """
    Get restaurant menu from MongoDB or in-memory storage
    """
    try:
        # Try to get menu from MongoDB first
        db_instance = get_db()
        if db_instance and db_instance.connected:
            menu_data = db_instance.get_menu()
            if menu_data:
                return jsonify(menu_data)
        
        # Fallback to in-memory menu data
        if menu:
            return jsonify(menu)
        else:
            return jsonify({"error": "Menu not found"}), 404
    except Exception as e:
        print(f"Error getting menu: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/dishes', methods=['GET'])
def get_dishes():
    """
    Get all dishes grouped by category from MongoDB
    """
    try:
        # Try to get dishes from MongoDB
        db_instance = get_db()
        if db_instance and db_instance.connected:
            dishes_by_category = db_instance.get_dishes_by_category()
            if dishes_by_category:
                return jsonify(dishes_by_category)
            else:
                return jsonify({"error": "No dishes found"}), 404
        else:
            return jsonify({"error": "Database not available"}), 503
    except Exception as e:
        print(f"Error getting dishes: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    """
    Create a new reservation in MongoDB
    """
    try:
        data = request.get_json()
        
        required_fields = ['name', 'phone', 'date', 'time', 'guests']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create reservation using MongoDB
        reservation_data = {
            "name": data['name'],
            "phone": data['phone'],
            "date": data['date'],
            "time": data['time'],
            "guests": data['guests'],
            "specialRequests": data.get('specialRequests', '')
        }
        
        db_instance = get_db()
        if not db_instance or not db_instance.connected:
            return jsonify({"error": "Database not available"}), 503
        
        created_reservation = db_instance.create_reservation(reservation_data)
        
        if created_reservation:
            return jsonify({
                "success": True,
                "reservation": created_reservation
            })
        else:
            return jsonify({"error": "Failed to create reservation"}), 500
        
    except Exception as e:
        print(f"Error creating reservation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/info', methods=['GET'])
def get_restaurant_info():
    """
    Get restaurant information from MongoDB
    """
    try:
        db_instance = get_db()
        if not db_instance or not db_instance.connected:
            return jsonify({"error": "Database not available"}), 503
        
        info = db_instance.get_restaurant_info()
        return jsonify(info)
        
    except Exception as e:
        print(f"Error getting restaurant info: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """
    Convert text to speech
    """
    try:
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Generate speech
        audio, sample_rate = generate_speech(text)
        
        # Convert numpy array to bytes
        import io
        import soundfile as sf
        
        # Save audio to bytes
        audio_bytes = io.BytesIO()
        sf.write(audio_bytes, audio, sample_rate, format='WAV')
        audio_bytes.seek(0)
        
        return jsonify({
            "audio": audio_bytes.getvalue().hex(),
            "sampleRate": sample_rate
        })
        
    except Exception as e:
        print(f"Error in TTS: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    """
    Shutdown the server and close MongoDB connection
    """
    try:
        db_instance = get_db()
        if db_instance:
            db_instance.close()
        
        # Shutdown Flask server
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        
        return jsonify({"message": "Server shutting down..."}), 200
        
    except Exception as e:
        print(f"Error shutting down: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)