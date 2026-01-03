import whisper
import logging
import tqdm
import os

logger = logging.getLogger(__name__)

class ProgressHook(tqdm.tqdm):
    """
    Classe especial para interceptar o progresso interno do Whisper
    e enviar para a interface gráfica.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.progress_callback = None
        self.preview_callback = None

    def update(self, n=1):
        displayed = super().update(n)
        if self.progress_callback and self.total:
            # Calcula a porcentagem real (0-100)
            percentage = int((self.n / self.total) * 100)
            # Garante que não ultrapasse 100% por arredondamento
            self.progress_callback(min(percentage, 100))
        return displayed

class TranscriptionEngine:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.model_size = "base"
        if hasattr(self.config, 'get'):
            self.model_size = self.config.get("model_size", "base")
            
        self._model = None

    @property
    def model(self):
        if self._model is None:
            logger.info(f"Carregando modelo Whisper: {self.model_size}")
            self._model = whisper.load_model(self.model_size)
        return self._model

    def transcribe(self, audio_path, progress_callback=None, preview_callback=None):
        """
        Transcreve o áudio enviando atualizações de progresso e prévia.
        """
        # 1. Avisa a UI que a transcrição começou
        if preview_callback:
            preview_callback("Iniciando transcrição neural...")

        # 2. Patch temporário no tqdm para capturar o progresso do Whisper
        # O Whisper usa tqdm internamente. Ao substituir o tqdm original pelo nosso,
        # conseguimos ler a porcentagem que antes só aparecia no terminal.
        original_tqdm = tqdm.tqdm
        tqdm.tqdm = ProgressHook
        
        try:
            # Injetamos nossos callbacks no novo tqdm
            def custom_hook(*args, **kwargs):
                pbar = ProgressHook(*args, **kwargs)
                pbar.progress_callback = progress_callback
                pbar.preview_callback = preview_callback
                return pbar
            
            tqdm.tqdm = custom_hook
            
            # Executa a transcrição
            # verbose=True agora é permitido porque nosso Hook gerencia a saída
            result = self.model.transcribe(audio_path, verbose=False)
            
            return result
            
        finally:
            # Restaura o tqdm original para não quebrar outras partes do sistema
            tqdm.tqdm = original_tqdm