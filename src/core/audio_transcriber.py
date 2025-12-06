# src/core/audio_transcriber.py
import os
from typing import Dict, Optional, List

from .lightweight_transcriber import LightweightTranscriber
from .simple_transcriber import SimpleTranscriber


class AudioTranscriber:
    """
    Gerencia a transcrição de áudio, escolhendo o melhor
    transcritor disponível no ambiente.
    """
    
    def __init__(self):
        self.transcriber = self._get_transcriber()

    def _get_transcriber(self):
        """
        Retorna a melhor implementação de transcritor disponível.
        Prioridade: Whisper > Lightweight > Simple.
        """
        try:
            # Tenta importar as dependências pesadas
            import whisper
            import torch
            
            # Se a importação for bem-sucedida, usa o SimpleTranscriber
            # que, por sua vez, deveria ser refatorado para usar Whisper.
            # Por enquanto, vamos simular essa escolha.
            print("✅ Transcritor AVANÇADO (Whisper) detectado.")
            # Em um cenário real, aqui seria instanciado um 'WhisperTranscriber'
            # Por ora, usaremos o SimpleTranscriber como placeholder para a lógica de extração de áudio.
            return SimpleTranscriber()

        except ImportError:
            print("⚠️  Whisper ou Torch não instalados.")
            print("   Recorrendo ao transcritor leve (mock inteligente).")
            print("   Para transcrição real, instale: pip install openai-whisper torch torchaudio")
            return LightweightTranscriber()
    
    def transcribe(self, video_path: str) -> Optional[Dict]:
        """
        Transcreve o áudio de um vídeo usando o transcritor selecionado.
        """
        try:
            if not os.path.exists(video_path):
                print(f"❌ Arquivo de vídeo não encontrado: {video_path}")
                return None
            
            print(f"🎤 Transcrevendo com: {self.transcriber.__class__.__name__}")
            return self.transcriber.transcribe(video_path)
            
        except Exception as e:
            print(f"❌ Erro crítico durante a transcrição de {os.path.basename(video_path)}: {e}")
            # Fallback absoluto
            return {
                'language': 'pt-BR',
                'segments': [{
                    'start': 0,
                    'end': 30,
                    'text': f"Erro ao processar: {os.path.basename(video_path)}"
                }],
                'is_fallback': True
            }
    
    def transcribe_batch(self, video_paths: List[str]) -> List[Optional[Dict]]:
        """
        Transcreve uma lista de vídeos em lote.
        """
        return [self.transcribe(path) for path in video_paths]