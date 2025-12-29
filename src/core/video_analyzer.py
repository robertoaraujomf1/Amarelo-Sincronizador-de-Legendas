import os
import subprocess
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class VideoAnalyzer:
    """Analisa arquivos de vídeo para extrair informações"""
    
    def __init__(self):
        pass
    
    def analyze(self, video_path: str) -> Dict[str, Any]:
        """
        Analisa um arquivo de vídeo usando ffprobe.
        
        Args:
            video_path: Caminho do arquivo de vídeo
            
        Returns:
            Dicionário com informações do vídeo
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {video_path}")
        
        try:
            # Comando para extrair informações do vídeo
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Erro ao analisar vídeo: {result.stderr}")
                raise Exception(f"Falha ao analisar vídeo: {result.stderr}")
            
            video_info = json.loads(result.stdout)
            
            # Extrair informações relevantes
            return self._extract_video_info(video_info, video_path)
            
        except Exception as e:
            logger.error(f"Erro ao analisar vídeo {video_path}: {e}")
            raise
    
    def _extract_video_info(self, ffprobe_output: Dict, video_path: str) -> Dict[str, Any]:
        """Extrai informações relevantes do output do ffprobe"""
        info = {
            'path': video_path,
            'filename': os.path.basename(video_path),
            'duration': 0,
            'width': 0,
            'height': 0,
            'fps': 0,
            'audio_codec': None,
            'video_codec': None,
            'bitrate': 0,
            'size': 0,
            'scenes': []  # Para detecção de cenas (será preenchido depois)
        }
        
        # Informações do formato
        if 'format' in ffprobe_output:
            format_info = ffprobe_output['format']
            info['duration'] = float(format_info.get('duration', 0))
            info['bitrate'] = int(format_info.get('bit_rate', 0))
            info['size'] = int(format_info.get('size', 0))
        
        # Informações dos streams
        video_stream = None
        audio_stream = None
        
        for stream in ffprobe_output.get('streams', []):
            if stream['codec_type'] == 'video' and video_stream is None:
                video_stream = stream
            elif stream['codec_type'] == 'audio' and audio_stream is None:
                audio_stream = stream
        
        # Informações do vídeo
        if video_stream:
            info['width'] = int(video_stream.get('width', 0))
            info['height'] = int(video_stream.get('height', 0))
            info['video_codec'] = video_stream.get('codec_name', 'unknown')
            
            # Calcular FPS
            fps_str = video_stream.get('avg_frame_rate', '0/0')
            if fps_str and '/' in fps_str:
                num, den = fps_str.split('/')
                if float(den) > 0:
                    info['fps'] = float(num) / float(den)
        
        # Informações do áudio
        if audio_stream:
            info['audio_codec'] = audio_stream.get('codec_name', 'unknown')
        
        # Detectar cenas (simplificado - em produção, usar algoritmo próprio)
        info['scenes'] = self._detect_scenes(info['duration'])
        
        logger.info(f"Vídeo analisado: {info['filename']}, Duração: {info['duration']}s")
        return info
    
    def _detect_scenes(self, duration: float) -> List[float]:
        """
        Detecta mudanças de cena no vídeo.
        Implementação simplificada - em produção, usar análise de frames.
        """
        scenes = []
        
        # Gera cenas a cada 10 segundos (simplificado)
        if duration > 0:
            scene_interval = 10.0  # segundos
            current_time = 0
            
            while current_time < duration:
                scenes.append(current_time)
                current_time += scene_interval
            
            # Garantir que a última cena seja o final do vídeo
            if scenes[-1] < duration:
                scenes.append(duration)
        
        return scenes