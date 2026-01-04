import os
from PyQt6.QtCore import QThread, pyqtSignal
from src.core.transcription_engine import TranscriptionEngine
from src.core.translation_engine import TranslationEngine
from src.core.subtitle_generator import SubtitleGenerator

class WorkflowManager(QThread):
    progress_individual = pyqtSignal(int)
    progress_general = pyqtSignal(int)
    preview_update = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.directory = ""
        self.transcriber = TranscriptionEngine(self.config)
        self.translator = TranslationEngine(self.config)
        self.subtitle_gen = SubtitleGenerator(self.config)

    def set_directory(self, directory):
        self.directory = directory

    def run(self):
        try:
            extensions = ('.mp4', '.mkv', '.avi', '.mov')
            videos = [f for f in os.listdir(self.directory) if f.lower().endswith(extensions)]
            
            if not videos:
                self.finished.emit(False, "Nenhum vídeo encontrado.")
                return

            total_videos = len(videos)
            self.progress_general.emit(0)
            self.progress_individual.emit(0)

            for index, video in enumerate(videos):
                video_path = os.path.join(self.directory, video)
                self.preview_update.emit(f"<b>🎬 Processando ({index+1}/{total_videos}):</b> {video}")
                
                base_geral = int((index / total_videos) * 100)
                porcao_video = 100 / total_videos

                def update_sync_progress(p_ind):
                    self.progress_individual.emit(p_ind)
                    # Sincronização em tempo real da barra geral
                    p_geral = int(base_geral + (p_ind * porcao_video / 100))
                    self.progress_general.emit(p_geral)

                # 1. Transcrição (0-70%)
                def trans_cb(p):
                    update_sync_progress(int(p * 0.7))

                result = self.transcriber.transcribe(video_path, progress_callback=trans_cb)
                segments = result['segments']

                # 2. Tradução (70-100%)
                is_enabled = self.config.get("translation.enabled", False)
                target_lang = self.config.get("translation.target_language", "pt")
                
                if is_enabled:
                    def trad_cb(p):
                        update_sync_progress(70 + int(p * 0.3))
                    segments = self.translator.translate_segments(segments, target_lang, progress_callback=trad_cb)
                else:
                    update_sync_progress(100)

                # 3. Gerar Arquivo
                srt_path = os.path.join(self.directory, os.path.splitext(video)[0] + ".srt")
                self.subtitle_gen.generate(segments, srt_path)
                
            self.progress_general.emit(100)
            self.finished.emit(True, "Sucesso")
        except Exception as e:
            self.finished.emit(False, str(e))