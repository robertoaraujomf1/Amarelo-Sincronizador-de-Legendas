import whisper
import logging
import tqdm
import os

logger = logging.getLogger(__name__)

class ProgressHook(tqdm.tqdm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.progress_callback = None

    def update(self, n=1):
        displayed = super().update(n)
        if self.progress_callback and self.total:
            percentage = int((self.n / self.total) * 100)
            self.progress_callback(min(percentage, 100))
        return displayed

class TranscriptionEngine:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self._model = None
        # Pegar o modelo do config ou default 'base'
        self.model_size = "base"
        if hasattr(self.config, 'get'):
            self.model_size = self.config.get("transcription.model", "base")

    @property
    def model(self):
        if self._model is None:
            self._model = whisper.load_model(self.model_size)
        return self._model

    def transcribe(self, audio_path, progress_callback=None, preview_callback=None):
        if progress_callback:
            progress_callback(0) # Forçar 0% no início
            
        original_tqdm = tqdm.tqdm
        def custom_tqdm(*args, **kwargs):
            pbar = ProgressHook(*args, **kwargs)
            pbar.progress_callback = progress_callback
            return pbar
        
        tqdm.tqdm = custom_tqdm
        try:
            result = self.model.transcribe(audio_path, verbose=False)
            if progress_callback: progress_callback(100)
            return result
        finally:
            tqdm.tqdm = original_tqdm