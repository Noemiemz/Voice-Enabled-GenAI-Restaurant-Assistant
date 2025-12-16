from supertonic.helper import load_text_to_speech, load_voice_style
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