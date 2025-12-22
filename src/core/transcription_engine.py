import os
import subprocess
from faster_whisper import WhisperModel


SUPPORTED_LANGUAGES = [
    "de", "en", "es", "fr", "ja", "pt", "ko"
]


class TranscriptionEngine:
    def __init__(self, gpu_info: dict):
        self.gpu_info = gpu_info
        self.model = self._load_model()

    def _load_model(self):
        device = "cpu"
        compute_type = "int8"

        if self.gpu_info.get("available"):
            device = "cuda"
            compute_type = "float16"

        return WhisperModel(
            "large-v3",
            device=device,
            compute_type=compute_type
        )

    def extract_audio(self, video_path: str, wav_path: str):
        """
        Extrai áudio do vídeo usando ffmpeg
        """
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            wav_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def transcribe(self, video_path: str):
        """
        Retorna:
        - idioma detectado
        - lista de segmentos (start, end, text)
        """
        temp_audio = video_path + ".wav"
        self.extract_audio(video_path, temp_audio)

        segments, info = self.model.transcribe(
            temp_audio,
            beam_size=5,
            vad_filter=True
        )

        result_segments = []
        for segment in segments:
            result_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })

        if os.path.exists(temp_audio):
            os.remove(temp_audio)

        return info.language, result_segments
