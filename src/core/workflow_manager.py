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
        # Inicializa o motor Whisper
        self.engine = TranscriptionEngine(config_manager=self.config)

    def set_directory(self, directory):
        self.directory = directory

    def run(self):
        try:
            if not self.directory:
                self.finished.emit(False, "Diretório não selecionado.")
                return

            # Lista arquivos de vídeo suportados
            videos = [f for f in os.listdir(self.directory) 
                     if f.lower().endswith(('.mp4', '.mkv', '.avi', '.mov'))]
            
            if not videos:
                self.finished.emit(False, "Nenhum vídeo encontrado na pasta selecionada.")
                return

            # Captura as preferências de estilo salvas pela UI
            font_color = self.config.get("font_color", "#f4c430")
            font_size_label = self.config.get("font_size_label", "Médio")
            is_bold = self.config.get("font_bold", True)

            # Mapeamento do rótulo para valor numérico de fonte compatível com SRT
            size_map = {
                "Pequeno": "16",
                "Médio": "22",
                "Grande": "28" # Mantido dentro do limite de 33% da tela
            }
            font_size = size_map.get(font_size_label, "22")

            for index, video in enumerate(videos):
                video_path = os.path.join(self.directory, video)
                self.preview_update.emit(f"Processando: {video}")
                
                # Executa a transcrição via Whisper
                result = self.engine.transcribe(video_path)
                
                # Define o caminho do arquivo SRT (mesmo nome do vídeo)
                srt_path = os.path.splitext(video_path)[0] + ".srt"
                
                # Salva o arquivo com as tags de estilo
                self._save_as_srt(
                    result['segments'], 
                    srt_path, 
                    font_color, 
                    font_size, 
                    is_bold
                )
                
                # Atualiza o progresso global
                progress = int(((index + 1) / len(videos)) * 100)
                self.progress_update.emit(progress)

            self.finished.emit(True, f"Sucesso! {len(videos)} vídeo(s) legendado(s).")

        except Exception as e:
            logger.error(f"Erro no workflow: {e}")
            self.finished.emit(False, f"Erro inesperado: {str(e)}")

    def _save_as_srt(self, segments, srt_path, color, size, bold):
        """Gera o arquivo SRT aplicando tags HTML-like de estilo."""
        try:
            with open(srt_path, "w", encoding="utf-8") as f:
                for i, segment in enumerate(segments, start=1):
                    start = self._format_time(segment['start'])
                    end = self._format_time(segment['end'])
                    text = segment['text'].strip()
                    
                    # Montagem da estrutura de estilo: <font> e <b>
                    # A tag <font> suporta 'color' e 'size' em muitos players (ex: VLC)
                    styled_text = f'<font color="{color}" size="{size}">{text}</font>'
                    
                    if bold:
                        styled_text = f'<b>{styled_text}</b>'
                    
                    f.write(f"{i}\n{start} --> {end}\n{styled_text}\n\n")
        except Exception as e:
            logger.error(f"Erro ao salvar SRT: {e}")
            raise

    def _format_time(self, seconds):
        """Converte segundos para o formato de tempo SRT (00:00:00,000)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"