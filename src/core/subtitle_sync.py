import os
import subprocess
from pathlib import Path
from typing import Optional

from src.core.transcription_engine import TranscriptionEngine
from src.core.subtitle_generator import SubtitleGenerator
from src.utils.config_manager import ConfigManager


class SubtitleSynchronizer:
    def __init__(self, config: Optional[ConfigManager] = None):
        self.generator = SubtitleGenerator()
        self.config = config

    def _extract_audio(self, video_path: str, wav_path: str):
        """Extrai áudio do vídeo usando ffmpeg"""
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(wav_path)
        ]
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )

    def synchronize(self, video_path: Path, subtitle_path: Path) -> str:
        """
        Sincroniza legendas com o vídeo.
        Retorna o conteúdo SRT sincronizado.
        """
        # Lê o arquivo de legenda original
        with open(subtitle_path, "r", encoding="utf-8") as f:
            original_srt = f.read()

        # Parse das legendas originais
        subtitles = self.generator.parse_srt(original_srt)
        if not subtitles:
            return original_srt

        # Obtém informações de GPU do config se disponível
        gpu_info = {}
        if self.config:
            gpu_info = {
                "available": self.config.get_runtime_value("gpu_available", False),
                "name": self.config.get_runtime_value("gpu_name"),
                "backend": self.config.get_runtime_value("gpu_backend")
            }

        # Re-transcrição para alinhamento
        engine = TranscriptionEngine(gpu_info)
        _, segments = engine.transcribe(str(video_path))

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

        # Se houver mais legendas originais que segmentos transcritos, adiciona as restantes
        if len(subtitles) > len(segments):
            last_end = segments[-1]["end"] if segments else 0
            for i in range(len(segments), len(subtitles)):
                duration = subtitles[i]["end"] - subtitles[i]["start"]
                synced_segments.append({
                    "start": last_end,
                    "end": last_end + duration,
                    "text": subtitles[i]["text"]
                })
                last_end += duration

        return self.generator.generate_from_segments(synced_segments)
