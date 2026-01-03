import os
import time
import traceback
from PyQt6.QtCore import QThread, pyqtSignal

# Tentativa de importação robusta
try:
    from src.core.transcription_engine import TranscriptionEngine
    from src.core.translation_engine import TranslationEngine
    from src.core.subtitle_generator import SubtitleGenerator
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from transcription_engine import TranscriptionEngine
    from translation_engine import TranslationEngine
    from subtitle_generator import SubtitleGenerator

class WorkflowManager(QThread):
    progress_update = pyqtSignal(int)
    preview_update = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.directory = ""
        # Inicializa aqui para evitar erros de importação tardios
        self.transcriber = TranscriptionEngine(self.config)
        self.translator = TranslationEngine(self.config)
        self.subtitle_gen = SubtitleGenerator(self.config)

    def set_directory(self, directory):
        self.directory = directory

    def run(self):
        try:
            if not self.directory or not os.path.exists(self.directory):
                self.finished.emit(False, "Pasta não encontrada.")
                return

            exts = ('.mp4', '.mkv', '.avi', '.mov')
            videos = [f for f in os.listdir(self.directory) if f.lower().endswith(exts)]
            
            if not videos:
                self.finished.emit(False, "Nenhum vídeo compatível.")
                return

            for video in videos:
                video_path = os.path.join(self.directory, video)
                self.preview_update.emit(f"Processando: {video}")

                # Transcrição com Progresso (98%)
                result = self.transcriber.transcribe(
                    video_path, 
                    progress_callback=self.progress_update.emit,
                    preview_callback=self.preview_update.emit
                )

                # Tradução
                target_lang = self.config.get("target_lang", "Original")
                segments = result.get('segments', [])
                
                if target_lang != "Original" and segments:
                    self.preview_update.emit(f"Traduzindo para {target_lang}...")
                    segments = self.translator.translate_segments(segments, target_lang)

                # Gerar SRT
                srt_path = os.path.join(self.directory, os.path.splitext(video)[0] + ".srt")
                self.subtitle_gen.generate(segments, srt_path)
                
            self.finished.emit(True, "Processo concluído com sucesso!")

        except Exception as e:
            print(f"DEBUG: {traceback.format_exc()}")
            self.finished.emit(False, str(e))