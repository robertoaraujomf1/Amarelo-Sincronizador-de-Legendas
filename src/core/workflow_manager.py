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
            for index, video in enumerate(videos):
                video_path = os.path.join(self.directory, video)
                self.preview_update.emit(f"<b>🎬 Processando ({index+1}/{total_videos}):</b> {video}")
                
                # Reset barra individual para cada vídeo
                self.progress_individual.emit(0)

                # 1. Transcrição
                result = self.transcriber.transcribe(
                    video_path, 
                    progress_callback=self.progress_individual.emit
                )

                # --- CORREÇÃO DA TRADUÇÃO AQUI ---
                # Lemos se está habilitado e qual o idioma usando o padrão do seu ConfigManager
                is_enabled = self.config.get("translation.enabled", False)
                target_lang = self.config.get("translation.target_language", "pt")
                
                segments = result['segments']
                
                if is_enabled:
                    self.preview_update.emit(f"🌍 Traduzindo para: <b>{target_lang.upper()}</b>...")
                    # Chama o motor de tradução com os dados corretos
                    segments = self.translator.translate_segments(segments, target_lang)
                else:
                    self.preview_update.emit("📄 Mantendo idioma original...")
                # --------------------------------

                # 3. Geração de SRT Estilizado
                srt_path = os.path.join(self.directory, os.path.splitext(video)[0] + ".srt")
                self.subtitle_gen.generate(segments, srt_path)
                
                # Atualiza Barra Geral
                geral_percent = int(((index + 1) / total_videos) * 100)
                self.progress_general.emit(geral_percent)
                
            self.finished.emit(True, "Processamento em lote concluído!")
        except Exception as e:
            self.finished.emit(False, f"Erro: {str(e)}")