from pathlib import Path
from typing import Optional

from core.file_matcher import match_videos_and_subtitles
from core.video_analyzer import VideoAnalyzer
from core.subtitle_generator import SubtitleGenerator
from core.subtitle_sync import SubtitleSynchronizer
from core.translator import SubtitleTranslator
from utils.config_manager import ConfigManager


class WorkflowManager:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.video_analyzer = VideoAnalyzer()
        self.subtitle_generator = SubtitleGenerator()
        self.subtitle_synchronizer = SubtitleSynchronizer()
        self.translator = SubtitleTranslator()

    def process_directory(
        self,
        directory: Path,
        target_language: Optional[str] = None,
        translate_existing: bool = False,
        progress_callback: Optional[callable] = None
    ):
        pairs = match_videos_and_subtitles(directory)
        total = len(pairs)

        if total == 0:
            return

        for index, pair in enumerate(pairs, start=1):
            video_path = pair["video"]
            subtitle_path = pair.get("subtitle")

            if progress_callback:
                progress_callback(
                    f"Processando {video_path.name}",
                    index,
                    total
                )

            self._process_single_video(
                video_path,
                subtitle_path,
                target_language,
                translate_existing
            )

    def _process_single_video(
        self,
        video_path: Path,
        subtitle_path: Optional[Path],
        target_language: Optional[str],
        translate_existing: bool
    ):
        audio_language = self.video_analyzer.detect_language(video_path)

        if subtitle_path is None:
            subtitles = self.subtitle_generator.generate(
                video_path=video_path,
                source_language=audio_language
            )

            if target_language and target_language != audio_language:
                subtitles = self.translator.translate(
                    subtitles,
                    audio_language,
                    target_language
                )

            output_path = self._resolve_output_path(video_path, target_language)
            self.subtitle_generator.save(subtitles, output_path)
            return

        synced_subtitles = self.subtitle_synchronizer.synchronize(
            video_path,
            subtitle_path
        )

        if translate_existing and target_language:
            synced_subtitles = self.translator.translate(
                synced_subtitles,
                audio_language,
                target_language
            )

        output_path = self._resolve_output_path(video_path, target_language)
        self.subtitle_generator.save(synced_subtitles, output_path)

    def _resolve_output_path(self, video_path: Path, language: Optional[str]) -> Path:
        mode = self.config.get("output_mode", "overwrite")
        base_name = video_path.stem
        extension = ".srt"

        if language:
            base_name = f"{base_name}.{language}"

        if mode == "overwrite":
            return video_path.with_suffix(extension)

        if mode == "alternate_name":
            return video_path.with_name(f"{base_name}{extension}")

        if mode == "output_folder":
            output_dir = Path(self.config.get("output_directory"))
            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir / f"{base_name}{extension}"

        return video_path.with_suffix(extension)
