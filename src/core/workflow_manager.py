import os
import logging
from PyQt6.QtCore import QThread, pyqtSignal
from src.core.transcription_engine import TranscriptionEngine

# Tenta importar o tradutor, se não tiver, o app avisa no log
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

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

            # Busca vídeos na pasta
            videos = [f for f in os.listdir(self.directory) 
                     if f.lower().endswith(('.mp4', '.mkv', '.avi', '.mov'))]
            
            if not videos:
                self.finished.emit(False, "Nenhum vídeo encontrado.")
                return

            # Puxa configurações da UI
            font_color = self.config.get("font_color", "#f4c430")
            font_size_label = self.config.get("font_size_label", "Médio")
            is_bold = self.config.get("font_bold", True)
            target_lang = self.config.get("target_lang", "Original")

            # Mapeamento de tamanho
            size_map = {"Pequeno": "18", "Médio": "22", "Grande": "28"}
            font_size = size_map.get(font_size_label, "22")

            # Mapeamento de idiomas
            lang_map = {"Português": "pt", "Inglês": "en", "Espanhol": "es"}

            for index, video in enumerate(videos):
                video_path = os.path.join(self.directory, video)
                self.preview_update.emit(f"Transcrevendo: {video}")
                
                # Transcrição
                result = self.engine.transcribe(video_path)
                segments = result['segments']

                # Lógica de Tradução Segura
                if target_lang != "Original":
                    if not HAS_TRANSLATOR:
                        self.preview_update.emit("Erro: Biblioteca 'deep-translator' não instalada.")
                    else:
                        dest_code = lang_map.get(target_lang, "pt")
                        self.preview_update.emit(f"Traduzindo para {target_lang}...")
                        try:
                            translator = GoogleTranslator(source='auto', target=dest_code)
                            for seg in segments:
                                # Traduz apenas se houver texto
                                if seg['text'].strip():
                                    seg['text'] = translator.translate(seg['text'])
                        except Exception as e:
                            self.preview_update.emit(f"Aviso: Falha na tradução ({e}). Usando original.")

                # Salva o SRT
                srt_path = os.path.splitext(video_path)[0] + ".srt"
                self._save_as_srt(segments, srt_path, font_color, font_size, is_bold)
                
                # Progresso
                progress = int(((index + 1) / len(videos)) * 100)
                self.progress_update.emit(progress)

            self.finished.emit(True, f"Processado com sucesso: {len(videos)} vídeos.")

        except Exception as e:
            logger.error(f"Erro no Workflow: {e}")
            self.finished.emit(False, f"Erro crítico: {str(e)}")

    def _save_as_srt(self, segments, srt_path, color, size, bold):
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, start=1):
                start = self._format_time(segment['start'])
                end = self._format_time(segment['end'])
                text = segment['text'].strip()
                
                # Tag font com cor e tamanho
                styled_text = f'<font color="{color}" size="{size}">{text}</font>'
                if bold:
                    styled_text = f'<b>{styled_text}</b>'
                
                f.write(f"{i}\n{start} --> {end}\n{styled_text}\n\n")

    def _format_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"