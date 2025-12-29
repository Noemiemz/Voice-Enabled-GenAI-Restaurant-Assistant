import time
from typing import List, Dict, Optional
from faster_whisper import WhisperModel


class WhisperTranscriber:
    """
    Wrapper around faster-whisper for audio transcription.
    """

    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
        """
        Initialize and load the Whisper model.

        Args:
            model_size: tiny / base / small / medium / large-v3
            device: "cpu" or "cuda"
            compute_type: "int8", "float16", etc.
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

        self.model: Optional[WhisperModel] = None
        self._load_model()


    def _load_model(self) -> None:
        """Loads the Whisper model into memory."""
        print(f"Loading Whisper model '{self.model_size}'...")
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        print("Whisper model loaded.")

    def transcribe(self,audio_path: str, beam_size: int = 5, language: Optional[str] = None, vad_filter: bool = True,) -> Dict:
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to WAV/MP3 audio file (16kHz WAV recommended)
            beam_size: Beam search size
            language: Force language (ex: "en", "fr") or None for auto-detect
            vad_filter: Enable Voice Activity Detection

        Returns:
            Dictionary containing:
                - text: full transcription
                - segments: list of segments with timestamps
                - language: detected language
                - inference_time: processing time in seconds
        """
        if self.model is None:
            raise RuntimeError("Model is not loaded")

        start_time = time.perf_counter()

        segments, info = self.model.transcribe(
            audio_path,
            beam_size=beam_size,
            language=language,
            vad_filter=vad_filter,
        )

        segment_list: List[Dict] = []
        full_text_parts: List[str] = []

        for seg in segments:
            segment_list.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            })
            full_text_parts.append(seg.text.strip())

        end_time = time.perf_counter()

        return {
            "text": " ".join(full_text_parts),
            "segments": segment_list,
            "language": info.language,
            "inference_time": end_time - start_time,
        }


