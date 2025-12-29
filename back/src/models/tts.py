from piper import PiperVoice, SynthesisConfig
from piper.download_voices import download_voice

from typing import Generator
import numpy as np
from pathlib import Path

from pathseeker import VOICES_DIR
from settings import VOICES_CONFIG

class TTSModel:
    def __init__(self, voice_path: str | Path, **synthesis_config_args):
        self.voice = PiperVoice.load(voice_path)
        self.config = SynthesisConfig(**synthesis_config_args)
    
    def stream_speech(self, text: str) -> Generator[tuple[np.ndarray, int], None, None]:
        for chunk in self.voice.synthesize(text, self.config):
            yield chunk.audio_int16_array, chunk.sample_rate

class TTSEngine:
    def __init__(self, default_languages: list[str] = ['de', 'en', 'es', 'fr', 'it']):
        self.models: dict[str, TTSModel] = {}
        for lang in default_languages:
            self._add_model(lang)
    
    def _add_model(self, language: str):
        if language in self.models:
            return  # Model already loaded

        if language not in VOICES_CONFIG:
            raise ValueError(f"No voice configuration found for language '{language}'")

        voice_info = VOICES_CONFIG[language]
        voice_name = voice_info["voice_name"]
        synthesis_config_args = voice_info.get("synthesis_config", {})

        voice_path = VOICES_DIR / f"{voice_name}.onnx"
        if not voice_path.exists():
            if not VOICES_DIR.exists():
                VOICES_DIR.mkdir(parents=True, exist_ok=True)
            print(f"Downloading voice model for language '{language}'...")
            download_voice(voice_name, VOICES_DIR)

        model = TTSModel(voice_path, **synthesis_config_args)
        self.models[language] = model
    
    def stream_speech(self, language: str, text: str) -> Generator[tuple[np.ndarray, int], None, None]:
        if language not in self.models:
            self._add_model(language)
        
        model = self.models[language]
        yield from model.stream_speech(text)