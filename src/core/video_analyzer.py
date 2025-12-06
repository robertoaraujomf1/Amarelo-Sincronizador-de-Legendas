# src/core/video_analyzer.py
import os
import time
from typing import Dict, Optional
import struct


class VideoAnalyzer:
    def __init__(self):
        self.has_moviepy = self._check_moviepy()
        self.has_imageio = self._check_imageio()
        
    def _check_moviepy(self) -> bool:
        """Verifica se moviepy está disponível"""
        try:
            from moviepy.editor import VideoFileClip
            return True
        except ImportError:
            print("⚠️ moviepy não disponível. Algumas funcionalidades serão limitadas.")
            return False
    
    def _check_imageio(self) -> bool:
        """Verifica se imageio com ffmpeg está disponível"""
        try:
            import imageio
            import imageio.plugins.ffmpeg
            return True
        except ImportError:
            print("⚠️ imageio[ffmpeg] não disponível.")
            return False
    
    def analyze(self, video_path: str) -> Optional[Dict]:
        """
        Analisa um arquivo de vídeo usando métodos Python puros.
        """
        if not os.path.exists(video_path):
            print(f"❌ Arquivo não encontrado: {video_path}")
            return None
        
        try:
            file_size = os.path.getsize(video_path)
            file_ext = os.path.splitext(video_path)[1].lower()
            
            # Tentar com moviepy primeiro (mais confiável)
            if self.has_moviepy:
                try:
                    return self._analyze_with_moviepy(video_path)
                except Exception as e:
                    print(f"⚠️ moviepy falhou: {e}")
            
            # Tentar com imageio
            if self.has_imageio:
                try:
                    return self._analyze_with_imageio(video_path)
                except Exception as e:
                    print(f"⚠️ imageio falhou: {e}")
            
            # Fallback: estimativa básica
            print(f"⚠️ Usando estimativa básica para: {os.path.basename(video_path)}")
            return self._estimate_video_info(video_path, file_size, file_ext)
            
        except Exception as e:
            print(f"❌ Erro ao analisar vídeo: {e}")
            return self._create_basic_video_info(video_path)
    
    def _analyze_with_moviepy(self, video_path: str) -> Optional[Dict]:
        """Analisa vídeo usando moviepy"""
        try:
            from moviepy.editor import VideoFileClip
            
            # Usar with para garantir que o arquivo seja fechado
            clip = VideoFileClip(video_path)
            try:
                info = {
                    'duration': clip.duration,
                    'width': clip.size[0],
                    'height': clip.size[1],
                    'fps': clip.fps,
                    'has_audio': clip.audio is not None,
                    'file_size': os.path.getsize(video_path),
                    'analyzed_with': 'moviepy'
                }
                
                # Tentar obter codec se possível
                try:
                    import subprocess
                    result = subprocess.run(
                        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                         '-show_entries', 'stream=codec_name', '-of', 
                         'default=noprint_wrappers=1:nokey=1', video_path],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        info['codec'] = result.stdout.strip()
                    else:
                        info['codec'] = 'unknown'
                except:
                    info['codec'] = 'unknown'
                
                return info
            finally:
                clip.close()
                
        except Exception as e:
            print(f"❌ Erro no moviepy: {e}")
            raise
    
    def _analyze_with_imageio(self, video_path: str) -> Optional[Dict]:
        """Analisa vídeo usando imageio"""
        try:
            import imageio
            
            reader = imageio.get_reader(video_path)
            metadata = reader.get_meta_data()
            
            info = {
                'duration': metadata.get('duration', 0),
                'width': metadata.get('size', (0, 0))[0],
                'height': metadata.get('size', (0, 0))[1],
                'fps': metadata.get('fps', 0),
                'file_size': os.path.getsize(video_path),
                'analyzed_with': 'imageio',
                'codec': metadata.get('codec', 'unknown'),
                'has_audio': True  # imageio não fornece esta info facilmente
            }
            
            reader.close()
            return info
            
        except Exception as e:
            print(f"❌ Erro no imageio: {e}")
            raise
    
    def _estimate_video_info(self, video_path: str, file_size: int, file_ext: str) -> Dict:
        """Estimativa básica baseada no tamanho e extensão do arquivo"""
        # Estimativas baseadas em extensões comuns
        duration_estimates = {
            '.mp4': 1800,  # 30 minutos típico
            '.avi': 1800,
            '.mkv': 1800,
            '.mov': 1800,
            '.wmv': 1800,
            '.flv': 600,   # 10 minutos típico
            '.m4v': 1800,
            '.webm': 600,
        }
        
        # Estimativa de duração baseada em tamanho (2MB por minuto em 720p)
        estimated_duration = file_size / (2 * 1024 * 1024) * 60  # minutos
        estimated_duration = min(estimated_duration, duration_estimates.get(file_ext, 1800))
        
        return {
            'duration': estimated_duration,
            'width': 1280,
            'height': 720,
            'fps': 30,
            'has_audio': True,
            'file_size': file_size,
            'analyzed_with': 'estimation',
            'codec': 'unknown',
            'is_estimated': True
        }
    
    def _create_basic_video_info(self, video_path: str) -> Dict:
        """Cria informações básicas mínimas"""
        file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
        
        return {
            'duration': 30,  # 30 segundos padrão
            'width': 1920,
            'height': 1080,
            'fps': 30,
            'has_audio': True,
            'file_size': file_size,
            'analyzed_with': 'fallback',
            'codec': 'unknown',
            'is_fallback': True
        }