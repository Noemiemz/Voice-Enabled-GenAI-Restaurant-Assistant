from faster_whisper import WhisperModel
import numpy as np

from utils.logger import log_execution
class WhisperWrapper:
    """
    Wrapper for the Faster Whisper model for speech-to-text transcription.
    """
    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
        """
        Initialize and load the Whisper model.

        Args:
            model_size: tiny / base / small / medium / large-v3
            device: "cpu" or "cuda"
            compute_type: "int8", "float16", etc.
        """
        print("Loading Whisper model...")
        self.model = WhisperModel(
            model_size_or_path=model_size,
            device=device,
            compute_type=compute_type,
        )
        print("Whisper model loaded.")

    @log_execution
    def transcribe(self, audio_data: np.ndarray, beam_size: int = 5) -> dict:
        """
        Transcribe an audio file.

        Args:
            audio_data: NumPy array containing audio data
            beam_size: Beam search size

        Returns:
            A dictionary with transcribed text and detected language
        """
        segments, info = self.model.transcribe(
            audio=audio_data,
            beam_size=beam_size,
            vad_filter=True,
        )

        full_text = " ".join([segment.text for segment in segments])

        return full_text, info.language


