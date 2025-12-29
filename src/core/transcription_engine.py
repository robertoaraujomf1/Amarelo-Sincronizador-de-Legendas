import os
import subprocess
from typing import Optional, List, Tuple, Callable, Dict, Any
from faster_whisper import WhisperModel


SUPPORTED_LANGUAGES = [
    "de", "en", "es", "fr", "ja", "pt", "ko"
]


class TranscriptionEngine:
    def __init__(self, gpu_info: dict):
        self.gpu_info = gpu_info
        self.model = self._load_model()

    def _load_model(self):
        device = "cpu"
        compute_type = "int8"

        if self.gpu_info.get("available"):
            device = "cuda"
            compute_type = "float16"

        try:
            return WhisperModel(
                "large-v3",
                device=device,
                compute_type=compute_type
            )
        except Exception as e:
            # Fallback para modelo menor se o large-v3 não estiver disponível
            print(f"⚠️ Erro ao carregar modelo large-v3: {e}. Usando base.")
            return WhisperModel(
                "base",
                device=device,
                compute_type=compute_type
            )

    def extract_audio(self, video_path: str, wav_path: str):
        """
        Extrai áudio do vídeo usando ffmpeg
        """
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            wav_path
        ]
        try:
            subprocess.run(
                cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"Erro ao extrair áudio do vídeo: {e}")

    def transcribe(self, video_path: str, segment_callback: Optional[Callable[[float, float, str], None]] = None,
                   progress_callback: Optional[Callable[[str, float, float, str], None]] = None):
        """
        Transcreve áudio do vídeo com callbacks opcionais para progresso.
        
        Retorna:
        - idioma detectado
        - lista de segmentos (start, end, text)
        """
        if progress_callback:
            progress_callback("Iniciando extração de áudio...", 0, 100, "audio_extraction")
        
        temp_audio = video_path + ".wav"
        
        try:
            # Extrai áudio
            self.extract_audio(video_path, temp_audio)
            
            if progress_callback:
                progress_callback("Áudio extraído. Iniciando transcrição...", 30, 100, "transcription")
            
            # Configura parâmetros de transcrição
            beam_size = 5
            vad_filter = True
            
            # Detecta duração do áudio para estimativa de progresso
            import wave
            with wave.open(temp_audio, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
            
            # Inicia transcrição
            segments, info = self.model.transcribe(
                temp_audio,
                beam_size=beam_size,
                vad_filter=vad_filter,
                language=None,  # Detecta automaticamente
                task="transcribe"
            )
            
            if progress_callback:
                progress_callback(f"Idioma detectado: {info.language}", 50, 100, "transcription")
            
            result_segments = []
            total_segments = 0
            processed_segments = 0
            
            # Primeira passagem para contar segmentos (para progresso)
            segments_list = list(segments)
            total_segments = len(segments_list)
            
            if progress_callback:
                progress_callback(f"Processando {total_segments} segmentos...", 60, 100, "transcription")
            
            # Processa cada segmento
            for i, segment in enumerate(segments_list):
                segment_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                }
                result_segments.append(segment_data)
                
                # Chama callback de segmento para preview
                if segment_callback:
                    segment_callback(segment.start, segment.end, segment.text.strip())
                
                # Chama callback de progresso
                if progress_callback:
                    progress_percent = 60 + (i / total_segments * 30)  # 60% a 90%
                    progress_callback(
                        f"Transcrevendo segmento {i+1}/{total_segments}: {segment.text[:50]}...",
                        int(progress_percent),
                        100,
                        "transcription"
                    )
                
                processed_segments += 1
            
            if progress_callback:
                progress_callback("Transcrição concluída!", 100, 100, "transcription")
            
            return info.language, result_segments
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Erro na transcrição: {str(e)}", 0, 100, "error")
            raise Exception(f"Erro na transcrição: {e}")
            
        finally:
            # Limpa arquivo temporário
            if os.path.exists(temp_audio):
                try:
                    os.remove(temp_audio)
                except:
                    pass

    def transcribe_with_progress(self, video_path: str, 
                                 segment_callback: Optional[Callable[[float, float, str], None]] = None,
                                 progress_callback: Optional[Callable[[str, float, float, str], None]] = None,
                                 status_callback: Optional[Callable[[str, str], None]] = None):
        """
        Versão alternativa com callbacks mais detalhados.
        
        Args:
            video_path: Caminho do vídeo
            segment_callback: Chamado para cada segmento (start, end, text)
            progress_callback: Chamado para progresso (message, current, total, stage)
            status_callback: Chamado para mudança de status (status, details)
        """
        if status_callback:
            status_callback("extracting_audio", "Extraindo áudio do vídeo...")
        
        temp_audio = video_path + ".wav"
        
        try:
            # Extrai áudio
            self.extract_audio(video_path, temp_audio)
            
            if status_callback:
                status_callback("loading_model", "Carregando modelo de transcrição...")
            
            if status_callback:
                status_callback("transcribing", "Transcrevendo áudio...")
            
            # Transcreve
            segments, info = self.model.transcribe(
                temp_audio,
                beam_size=5,
                vad_filter=True
            )
            
            result_segments = []
            
            # Converte para lista para poder contar
            segments_list = list(segments)
            total_segments = len(segments_list)
            
            for i, segment in enumerate(segments_list):
                segment_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                }
                result_segments.append(segment_data)
                
                # Callback de segmento
                if segment_callback:
                    segment_callback(segment.start, segment.end, segment.text.strip())
                
                # Callback de progresso
                if progress_callback:
                    progress_percent = (i + 1) / total_segments * 100
                    progress_callback(
                        f"Segmento {i+1}/{total_segments}: {segment.text[:30]}...",
                        progress_percent,
                        100,
                        "transcription"
                    )
            
            if status_callback:
                status_callback("completed", f"Transcrição concluída! Idioma: {info.language}")
            
            return info.language, result_segments
            
        finally:
            if os.path.exists(temp_audio):
                os.remove(temp_audio)

    def get_supported_languages(self) -> List[str]:
        """Retorna lista de idiomas suportados"""
        return SUPPORTED_LANGUAGES

    def validate_language(self, language_code: str) -> bool:
        """Valida se um código de idioma é suportado"""
        return language_code in SUPPORTED_LANGUAGES

    def estimate_transcription_time(self, video_path: str) -> float:
        """
        Estima o tempo necessário para transcrição baseado na duração do vídeo.
        Retorna estimativa em segundos.
        """
        try:
            # Usa ffprobe para obter duração
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            duration = float(result.stdout.strip())
            
            # Estimativa: 0.3x tempo real para GPU, 3x para CPU
            if self.gpu_info.get("available"):
                return duration * 0.3
            else:
                return duration * 3.0
                
        except Exception:
            # Fallback: assume 30 minutos para cálculo
            return 1800  # 30 minutos