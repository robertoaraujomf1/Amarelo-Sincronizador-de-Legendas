import os
import re

class FileMatcher:
    def __init__(self):
        self.video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
        self.subtitle_extensions = ['.srt', '.vtt', '.ass', '.ssa']
    
    def find_pairs(self, directory):
        """Encontra pares de vídeo e legenda no diretório"""
        if not os.path.exists(directory):
            return []
        
        # Listar arquivos
        video_files = []
        subtitle_files = []
        
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                name, ext = os.path.splitext(file)
                if ext.lower() in self.video_extensions:
                    video_files.append((name, file_path))
                elif ext.lower() in self.subtitle_extensions:
                    subtitle_files.append((name, file_path))
        
        # Encontrar pares
        pairs = []
        for video_name, video_path in video_files:
            for subtitle_name, subtitle_path in subtitle_files:
                if self.names_match(video_name, subtitle_name):
                    pairs.append((video_path, subtitle_path))
                    break
        
        return pairs
    
    def names_match(self, video_name, subtitle_name):
        """Verifica se os nomes do vídeo e legenda coincidem"""
        # Remover informações comuns de qualidade, codec, etc.
        video_clean = self.clean_filename(video_name)
        subtitle_clean = self.clean_filename(subtitle_name)
        
        # Verificar se um contém o outro
        return (video_clean in subtitle_clean or 
                subtitle_clean in video_clean or
                video_clean == subtitle_clean)
    
    def clean_filename(self, filename):
        """Remove informações extras do nome do arquivo"""
        # Padrões comuns para remover
        patterns = [
            r'[\.\-_]?[0-9]{3,4}p',  # Resolução (720p, 1080p)
            r'[\.\-_]?x[0-9]{3,4}',   # Resolução alternativa
            r'[\.\-_]?[Hh][Dd]',      # HD
            r'[\.\-_]?[Bb][Rr][Rr]?[Ii]?[Pp]?',  # BRRip, BDRip, etc.
            r'[\.\-_]?[Ww][Ee][Bb]',  # WEB
            r'[\.\-_]?[Dd][Vv][Dd]',  # DVD
            r'[\.\-_]?[Xx]?[Vv][Ii]?[Dd]',  # XVID, DIVX
            r'[\.\-_]?[Hh]\.?[0-9]{3,4}',  # H264, H265
            r'[\.\-_]?[Aa][Aa][Cc]',  # AAC
            r'[\.\-_]?[0-9]ch',       # Canais de áudio
            r'[\.\-_]?[Ss][0-9]{1,2}[Ee][0-9]{1,2}',  # S01E01
            r'\[.*?\]',               # Qualquer coisa entre colchetes
            r'\(.*?\)',               # Qualquer coisa entre parênteses
        ]
        
        cleaned = filename
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remover espaços extras e caracteres especiais no início/fim
        cleaned = cleaned.strip(' .-_')
        
        return cleaned.lower()