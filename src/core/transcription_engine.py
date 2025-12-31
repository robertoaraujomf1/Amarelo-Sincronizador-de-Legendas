import whisper
import torch
import numpy as np
import os
# Alterado para PyQt6
from PyQt6.QtCore import QObject, pyqtSignal

class TranscriptionEngine(QObject):
    """Motor de transcrição usando OpenAI Whisper (IA)"""
    
    # Sinal para enviar a porcentagem de progresso (0.0 a 100.0)
    progress_signal = pyqtSignal(float)
    
    def __init__(self, model_size='base', device=None):
        super().__init__()
        
        # Seleção automática de hardware (GPU vs CPU)
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
            
        self.model_size = model_size
        self.model = None
        
    def load_model(self):
        """Carrega o modelo na memória apenas quando necessário"""
        if self.model is None:
            # Opções de tamanho: 'tiny', 'base', 'small', 'medium', 'large'
            self.model = whisper.load_model(self.model_size, device=self.device)
        return self.model
        
    def transcribe(self, audio_path, language=None):
        """
        Converte áudio em uma lista de segmentos com tempo e texto
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Arquivo de áudio não encontrado: {audio_path}")

        try:
            model = self.load_model()
            
            # Melhora a performance em GPUs NVIDIA
            use_fp16 = True if self.device == 'cuda' else False
            
            # Configurações do Whisper
            options = {
                'language': language,
                'task': 'transcribe',
                'fp16': use_fp16,
                'verbose': False
            }
            
            # Executa a transcrição (este processo é demorado)
            # O Whisper por padrão não emite progresso linha a linha facilmente,
            # por isso emitimos um sinal de "início" e "fim" aqui.
            self.progress_signal.emit(10.0)
            
            result = model.transcribe(audio_path, **options)
            
            # Processa o dicionário bruto do Whisper para o formato do nosso app
            segments = []
            total_segments = len(result['segments'])
            
            for i, segment in enumerate(result['segments']):
                segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'].strip(),
                    'confidence': segment.get('avg_logprob', 0.0)
                })
                
                # Atualiza o progresso baseado no processamento dos segmentos extraídos
                prog = 10.0 + (float(i + 1) / total_segments * 90.0)
                self.progress_signal.emit(prog)
            
            return segments
            
        except Exception as e:
            raise Exception(f"Falha técnica no Whisper: {str(e)}")
            
    def detect_language(self, audio_path):
        """Analisa os primeiros 30 segundos para detectar o idioma original"""
        try:
            model = self.load_model()
            
            # Carrega e ajusta o áudio para o formato do Whisper (log-Mel spectrogram)
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            
            mel = whisper.log_mel_spectrogram(audio).to(self.device)
            
            # Detecta o idioma
            _, probs = model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)
            
            return detected_lang, probs[detected_lang]
            
        except Exception as e:
            raise Exception(f"Erro ao detectar idioma: {str(e)}")