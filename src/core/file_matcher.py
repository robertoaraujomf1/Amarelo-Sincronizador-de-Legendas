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
        
        pairs = []
        for video_name, video_path in video_files:
            for subtitle_name, subtitle_path in subtitle_files:
                if self.names_match(video_name, subtitle_name):
                    pairs.append((video_path, subtitle_path))
                    break
        
        return pairs
    
    def names_match(self, video_name, subtitle_name):
        video_clean = self.clean_filename(video_name)
        subtitle_clean = self.clean_filename(subtitle_name)
        
        return (
            video_clean in subtitle_clean or
            subtitle_clean in video_clean or
            video_clean == subtitle_clean
        )
    
    def clean_filename(self, filename):
        patterns = [
            r'[\.\-_]?[0-9]{3,4}p',
            r'[\.\-_]?x[0-9]{3,4}',
            r'[\.\-_]?[Hh][Dd]',
            r'[\.\-_]?[Bb][Rr][Rr]?[Ii]?[Pp]?',
            r'[\.\-_]?[Ww][Ee][Bb]',
            r'[\.\-_]?[Dd][Vv][Dd]',
            r'[\.\-_]?[Xx]?[Vv][Ii]?[Dd]',
            r'[\.\-_]?[Hh]\.?[0-9]{3,4}',
            r'[\.\-_]?[Aa][Aa][Cc]',
            r'[\.\-_]?[0-9]ch',
            r'[\.\-_]?[Ss][0-9]{1,2}[Ee][0-9]{1,2}',
            r'\[.*?\]',
            r'\(.*?\)',
        ]
        
        cleaned = filename
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip(' .-_').lower()


# 🔹 FUNÇÃO DE FACHADA PARA O WORKFLOW
def match_videos_and_subtitles(directory):
    """
    Interface funcional para o WorkflowManager.
    Retorna lista de dicionários com chaves 'video' e 'subtitle' (opcional).
    """
    from pathlib import Path
    matcher = FileMatcher()
    directory_path = Path(directory)
    pairs = matcher.find_pairs(str(directory_path))
    
    # Converte tuplas para dicionários e normaliza caminhos
    result = []
    matched_video_paths = set()
    
    for video_path, subtitle_path in pairs:
        video_path_obj = Path(video_path).resolve()
        result.append({
            "video": video_path_obj,
            "subtitle": Path(subtitle_path).resolve() if subtitle_path else None
        })
        matched_video_paths.add(video_path_obj)
    
    # Adiciona vídeos sem legendas correspondentes
    for file_path in directory_path.iterdir():
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext in matcher.video_extensions:
                video_path_obj = file_path.resolve()
                if video_path_obj not in matched_video_paths:
                    result.append({
                        "video": video_path_obj,
                        "subtitle": None
                    })
    
    return result
