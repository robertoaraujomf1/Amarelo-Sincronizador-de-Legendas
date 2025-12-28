import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

class VideoAnalyzer:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def get_video_info(self, video_path):
        """Obtém informações técnicas do vídeo usando FFprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFprobe error: {result.stderr}")
            return json.loads(result.stdout)
        except FileNotFoundError:
            raise FileNotFoundError("ffprobe não encontrado. Verifique se o FFmpeg está instalado e no PATH do sistema.")
        except json.JSONDecodeError:
            raise ValueError(f"Não foi possível decodificar a saída do ffprobe para o vídeo: {video_path}")
    
    def get_audio_stream(self, video_path):
        """Identifica o stream de áudio principal"""
        info = self.get_video_info(video_path)
        
        audio_streams = []
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'audio':
                audio_streams.append(stream)
        
        # Retorna o primeiro stream de áudio ou None
        return audio_streams[0] if audio_streams else None
    
    def extract_audio_sample(self, video_path, output_path, duration=30):
        """Extrai uma amostra de áudio para análise"""
        try:
            cmd = [
                'ffmpeg', '-i', str(video_path),
                '-t', str(duration),
                '-ac', '1',
                '-ar', '16000',
                '-f', 'wav',
                '-y',
                str(output_path)
            ]
            subprocess.run(cmd, capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            return True
        except FileNotFoundError:
            raise FileNotFoundError("ffmpeg não encontrado. Verifique se o FFmpeg está instalado e no PATH do sistema.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Erro ao extrair amostra de áudio com FFmpeg: {e.stderr.decode('utf-8', errors='ignore')}")
    
    def detect_language(self, video_path, sample_duration=60):
        """Detecta o idioma do áudio do vídeo"""
        temp_audio = None
        try:
            # Criar arquivo temporário
            temp_audio = Path(self.temp_dir) / f"amarelo_audio_{os.getpid()}.wav"
            
            # Extrair amostra de áudio
            self.extract_audio_sample(video_path, temp_audio, duration=sample_duration)
            
            # Tentar usar Whisper para detecção
            try:
                import whisper
                
                # Carregar modelo tiny para detecção rápida
                model = whisper.load_model("tiny")
                
                # Carregar áudio
                audio = whisper.load_audio(str(temp_audio))
                audio = whisper.pad_or_trim(audio)
                
                # Detectar idioma
                mel = whisper.log_mel_spectrogram(audio).to(model.device)
                _, probs = model.detect_language(mel)
                detected_lang = max(probs, key=probs.get)
                
                # Mapear código do Whisper para códigos do app
                lang_map = {
                    'pt': 'pt_BR', 'en': 'en_US', 'es': 'es_ES',
                    'fr': 'fr_FR', 'de': 'de_DE', 'ja': 'ja_JP',
                    'it': 'it_IT', 'ru': 'ru_RU', 'zh': 'zh_CN',
                    'ko': 'ko_KR', 'ar': 'ar_SA', 'hi': 'hi_IN',
                    'nl': 'nl_NL', 'pl': 'pl_PL', 'tr': 'tr_TR'
                }
                
                return lang_map.get(detected_lang, 'en_US')
                
            except ImportError:
                print("Whisper não instalado. Usando detecção básica.")
                # Fallback: analisar metadados do áudio
                audio_stream = self.get_audio_stream(video_path)
                if audio_stream and 'tags' in audio_stream:
                    tags = audio_stream['tags']
                    if 'language' in tags:
                        lang_code = tags['language'].lower()
                        # Mapear códigos ISO 639-2 para códigos do app
                        iso_map = {
                            'por': 'pt_BR', 'eng': 'en_US', 'spa': 'es_ES',
                            'fre': 'fr_FR', 'ger': 'de_DE', 'jpn': 'ja_JP',
                            'ita': 'it_IT', 'rus': 'ru_RU', 'chi': 'zh_CN',
                            'kor': 'ko_KR', 'ara': 'ar_SA', 'hin': 'hi_IN',
                            'dut': 'nl_NL', 'pol': 'pl_PL', 'tur': 'tr_TR'
                        }
                        return iso_map.get(lang_code, 'en_US')
                
                # Fallback final: usar baseado no nome do arquivo/diretório
                return self._guess_language_from_path(video_path)
                
        except Exception as e:
            print(f"Erro na detecção de idioma: {e}")
            return self._guess_language_from_path(video_path)
        finally:
            # Garantir que o arquivo temporário seja sempre removido
            if temp_audio and temp_audio.exists():
                temp_audio.unlink()
    
    def _guess_language_from_path(self, video_path):
        """Tenta adivinhar o idioma baseado no caminho do arquivo"""
        path_str = str(video_path).lower()
        
        # Palavras-chave em diferentes idiomas
        language_keywords = {
            'pt_BR': ['brasil', 'brazil', 'br-', '.br', 'português', 'portugues', 'pt-br'],
            'en_US': ['english', 'eng', 'en-', '.en', 'us-', 'american'],
            'es_ES': ['español', 'espanol', 'esp', 'es-', '.es', 'spain', 'españa'],
            'fr_FR': ['french', 'français', 'francais', 'fr-', '.fr', 'france'],
            'de_DE': ['german', 'deutsch', 'de-', '.de', 'germany'],
            'ja_JP': ['japanese', 'japonês', 'japones', 'ja-', '.ja', 'japan', 'nihongo'],
            'it_IT': ['italian', 'italiano', 'it-', '.it', 'italy'],
            'ru_RU': ['russian', 'russo', 'ru-', '.ru', 'russia'],
            'zh_CN': ['chinese', 'chinês', 'chines', 'zh-', '.zh', 'china'],
            'ko_KR': ['korean', 'coreano', 'ko-', '.ko', 'korea']
        }
        
        for lang_code, keywords in language_keywords.items():
            for keyword in keywords:
                if keyword in path_str:
                    return lang_code
        
        # Fallback: inglês
        return 'en_US'
    
    def get_video_duration(self, video_path):
        """Obtém a duração total do vídeo em segundos"""
        try:
            info = self.get_video_info(video_path)
            duration = float(info.get('format', {}).get('duration', 0))
            return duration
        except (ValueError, KeyError, Exception): # Captura erros de conversão, chave ou análise
            return 0
    
    def get_video_resolution(self, video_path):
        """Obtém a resolução do vídeo (largura x altura)"""
        try:
            info = self.get_video_info(video_path)
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    width = stream.get('width', 0)
                    height = stream.get('height', 0)
                    return (width, height)
            return (0, 0)
        except (KeyError, Exception):
            return (0, 0)
    
    def get_audio_channels(self, video_path):
        """Obtém o número de canais de áudio"""
        try:
            audio_stream = self.get_audio_stream(video_path)
            if audio_stream:
                return int(audio_stream.get('channels', 2))
            return 2
        except (ValueError, KeyError, Exception):
            return 2