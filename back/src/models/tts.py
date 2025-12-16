from typing import Generator
from supertonic.helper import load_text_to_speech, load_voice_style, chunk_text
import numpy as np
import os

def generate_speech(
    text: str,
    onnx_dir: str = None,
    voice_style_path: str = None,
    speed: float = 1.05,
    total_step: int = 5
) -> tuple[np.ndarray, float]:
    # Use absolute paths based on the current file location
    if onnx_dir is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        onnx_dir = os.path.join(current_dir, "..", "supertonic", "assets", "onnx")
    
    if voice_style_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        voice_style_path = os.path.join(current_dir, "..", "supertonic", "assets", "voice_styles", "M1.json")
    
    # Load TTS model
    tts_model = load_text_to_speech(onnx_dir)

    # Load voice style
    voice_style = load_voice_style([voice_style_path])

    # Synthesize speech
    audio, _ = tts_model(
        text=text,
        style=voice_style,
        speed=speed,
        total_step=total_step
    )

    return audio, tts_model.sample_rate

def stream_speech(
    text: str,
    onnx_dir: str = "./src/supertonic/assets/onnx",
    voice_style_path: str = "./src/supertonic/assets/voice_styles/M1.json",
    speed: float = 1.05,
    total_step: int = 5,
    silence_duration: float = 0.3
) -> Generator[tuple[np.ndarray, float], None, None]:
    # Load TTS model
    tts_model = load_text_to_speech(onnx_dir)

    # Load voice style
    voice_style = load_voice_style([voice_style_path])

    # Synthesize speech chunk by chunk
    text_list = chunk_text(text, max_len=1) # max_len=1 will chunk by sentences

    for text in text_list:
        wav, _ = tts_model._infer([text], voice_style, total_step, speed)
        
        yield wav, tts_model.sample_rate