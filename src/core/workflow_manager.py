import os
import logging
from PyQt6.QtCore import QThread, pyqtSignal
from src.core.transcription_engine import TranscriptionEngine

logger = logging.getLogger(__name__)

class WorkflowManager(QThread):
    progress_update = pyqtSignal(int)
    preview_update = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.directory = None
        self.engine = TranscriptionEngine(config_manager=self.config)

    def set_directory(self, directory):
        self.directory = directory

    def run(self):
        try:
            if not self.directory:
                self.finished.emit(False, "Diretório não selecionado.")
                return

            videos = [f for f in os.listdir(self.directory) 
                     if f.lower().endswith(('.mp4', '.mkv', '.avi'))]
            
            if not videos:
                self.finished.emit(False, "Nenhum vídeo encontrado.")
                return

            # Mapeamento de cores para códigos Hexadecimal
            color_map = {
                "Amarelo": "#FFFF00",
                "Branco": "#FFFFFF",
                "Verde": "#00FF00",
                "Ciano": "#00FFFF"
            }

            # Captura as preferências da UI salvas no config
            font_color = color_map.get(self.config.get("font_color", "Amarelo"), "#FFFF00")
            is_bold = self.config.get("font_bold", True)

            for index, video in enumerate(videos):
                video_path = os.path.join(self.directory, video)
                self.preview_update.emit(f"Processando: {video}")
                
                result = self.engine.transcribe(video_path)
                
                srt_path = os.path.splitext(video_path)[0] + ".srt"
                
                # Salva com os estilos aplicados
                self._save_as_srt(result['segments'], srt_path, font_color, is_bold)
                
                self.progress_update.emit(int(((index + 1) / len(videos)) * 100))

            self.finished.emit(True, "Processamento concluído com sucesso!")

        except Exception as e:
            logger.error(f"Erro no workflow: {e}")
            self.finished.emit(False, str(e))

    def _save_as_srt(self, segments, srt_path, color, bold):
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, start=1):
                start = self._format_time(segment['start'])
                end = self._format_time(segment['end'])
                text = segment['text'].strip()
                
                # Aplica as Tags de Estilo
                styled_text = f'<font color="{color}">{text}</font>'
                if bold:
                    styled_text = f'<b>{styled_text}</b>'
                
                f.write(f"{i}\n{start} --> {end}\n{styled_text}\n\n")

    def _format_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"