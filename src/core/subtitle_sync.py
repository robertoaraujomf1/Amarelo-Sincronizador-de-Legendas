import os
import subprocess

from core.transcription_engine import TranscriptionEngine
from core.subtitle_generator import SubtitleGenerator


class SubtitleSynchronizer:
    def __init__(self):
        self.generator = SubtitleGenerator()

    def _extract_audio(self, video_path: str, wav_path: str):
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

    def sync(self, video_path: str, subtitle_path: str) -> str:
        """
        Retorna o conteúdo SRT sincronizado
        """
        with open(subtitle_path, "r", encoding="utf-8") as f:
            original_srt = f.read()

        subtitles = self.editor.parse(original_srt)
        if not subtitles:
            return original_srt

        temp_audio = video_path + ".sync.wav"
        self._extract_audio(video_path, temp_audio)

        # Re-transcrição para alinhamento
        engine = TranscriptionEngine({"available": False})
        _, segments = engine.transcribe(video_path)

        # Recria SRT com tempos novos, texto antigo
        synced_segments = []
        for i, seg in enumerate(segments):
            if i >= len(subtitles):
                break

            synced_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": subtitles[i]["text"]
            })

        if os.path.exists(temp_audio):
            os.remove(temp_audio)

        return self.generator.generate_from_segments(synced_segments)
