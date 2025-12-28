from piper import PiperVoice, SynthesisConfig, AudioChunk
from typing import Generator
import numpy as np

lang_config = {
    'fr': {
        'model': PiperVoice.load(f"./src/data/piper_voices/fr_FR-tom-medium.onnx"),
        'config': SynthesisConfig(length_scale=0.75)
    },
    'en': {
        'model': PiperVoice.load(f"./src/data/piper_voices/en_US-ryan-high.onnx"),
        'config': SynthesisConfig()
    },
}

def stream_speech(text: str, language: str) -> Generator[tuple[np.ndarray, int], None, None]:
    voice: PiperVoice = lang_config.get(language, lang_config['en'])['model']
    config: SynthesisConfig = lang_config.get(language, lang_config['en'])['config']

    for chunk in voice.synthesize(text, config):
        yield chunk.audio_int16_array, chunk.sample_rate