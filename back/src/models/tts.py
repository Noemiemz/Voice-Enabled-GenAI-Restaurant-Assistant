from supertonic import TTS
from supertonic.utils import chunk_text

class TextToSpeechModel:
    def __init__(self):
        self.tts = TTS(auto_download=True)

    def generate_speech(
        self,
        text: str,
        voice_name: str = "M1"
    ):
        voice_style = self.tts.get_voice_style(voice_name=voice_name)
        wav, duration = self.tts.synthesize(text=text, voice_style=voice_style)

        return wav, duration, self.tts.sample_rate
    
    def stream_speech(
        self,
        text: str,
        voice_name: str = "M1"
    ):
        voice_style = self.tts.get_voice_style(voice_name=voice_name)
        text_list = chunk_text(text, max_len=1)  # max_len=1 will chunk by sentences

        for chunk in text_list:
            wav, duration = self.tts.synthesize(text=chunk, voice_style=voice_style)
            yield wav, duration, self.tts.sample_rate