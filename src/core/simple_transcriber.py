# src/core/simple_transcriber.py
import os
import subprocess
import json
import tempfile
from typing import Dict, Optional
import wave
import struct


class SimpleTranscriber:
    """Transcritor simples como fallback"""
    
    def __init__(self):
        self.ffmpeg_available = self._check_ffmpeg()
        
    def _check_ffmpeg(self) -> bool:
        """Verifica se FFmpeg está disponível"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=False)
            return True
        except:
            return False
    
    def extract_audio(self, video_path: str) -> Optional[str]:
        """Extrai áudio do vídeo"""
        try:
            temp_dir = tempfile.gettempdir()
            temp_audio = os.path.join(temp_dir, f"temp_audio_{os.getpid()}.wav")
            
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                '-y', temp_audio
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(temp_audio):
                return temp_audio
            return None
            
        except Exception as e:
            print(f"Erro ao extrair áudio: {e}")
            return None
    
    def transcribe(self, video_path: str) -> Optional[Dict]:
        """
        Transcreve áudio (mock para demonstração).
        Em produção, substitua por API real.
        """
        try:
            print(f"⚠️ TRANSCRIÇÃO MOCK: {os.path.basename(video_path)}")
            print("   Para transcrição real, instale:")
            print("   pip install openai-whisper torch torchaudio")
            
            # Gerar segmentos mock baseados no nome do arquivo
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            
            # Segmentos de exemplo
            segments = [
                {
                    'start': 0.0,
                    'end': 10.0,
                    'text': f"Vídeo: {base_name[:30]}..."
                },
                {
                    'start': 10.0,
                    'end': 20.0,
                    'text': "Instale Whisper para transcrição automática."
                },
                {
                    'start': 20.0,
                    'end': 30.0,
                    'text': "Comando: pip install openai-whisper"
                }
            ]
            
            return {
                'language': 'pt-BR',
                'segments': segments
            }
            
        except Exception as e:
            print(f"Erro no transcritor mock: {e}")
            return None