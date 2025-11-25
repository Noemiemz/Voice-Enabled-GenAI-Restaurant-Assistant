from supertonic.helper import load_text_to_speech, load_voice_style
import numpy as np

def generate_speech(
    text: str,
    onnx_dir: str = "./src/supertonic/assets/onnx",
    voice_style_path: str = "./src/supertonic/assets/voice_styles/M1.json",
    speed: float = 1.05,
    total_step: int = 5
) -> tuple[np.ndarray, float]:
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