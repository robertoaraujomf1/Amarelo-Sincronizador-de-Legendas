import whisper
import logging
import tqdm
import os

logger = logging.getLogger(__name__)

class ProgressHook(tqdm.tqdm):
    """
    Classe especial para interceptar o progresso interno do Whisper.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.progress_callback = None

    def update(self, n=1):
        displayed = super().update(n)
        if self.progress_callback and self.total:
            # Converte o progresso do terminal em porcentagem (0-100)
            percentage = int((self.n / self.total) * 100)
            self.progress_callback(min(percentage, 100))
        return displayed

class TranscriptionEngine:
    def __init__(self, config_manager=None):
        # Proteção contra config_manager None
        self.config = config_manager if config_manager else {}
        
        # Tenta pegar o tamanho do modelo, padrão é 'base'
        if hasattr(self.config, 'get'):
            self.model_size = self.config.get("model_size", "base")
        else:
            self.model_size = "base"
            
        self._model = None

    @property
    def model(self):
        if self._model is None:
            logger.info(f"Carregando modelo Whisper: {self.model_size}")
            # Carrega o modelo (usa o cache se já existir)
            self._model = whisper.load_model(self.model_size)
        return self._model

    def transcribe(self, audio_path, progress_callback=None, preview_callback=None):
        """
        Realiza a transcrição e envia os dados para a interface.
        """
        if preview_callback:
            preview_callback(f"Extraindo áudio e carregando IA...")

        # --- O TRUQUE PARA PEGAR O PROGRESSO DO TERMINAL ---
        original_tqdm = tqdm.tqdm
        
        def custom_tqdm(*args, **kwargs):
            pbar = ProgressHook(*args, **kwargs)
            pbar.progress_callback = progress_callback
            return pbar
        
        tqdm.tqdm = custom_tqdm
        
        try:
            # verbose=False evita que o Whisper polua o console,
            # mas o nosso Hook continua pegando os dados por baixo dos panos.
            result = self.model.transcribe(audio_path, verbose=False)
            return result
            
        finally:
            # Restaura o tqdm original para evitar conflitos futuros
            tqdm.tqdm = original_tqdm