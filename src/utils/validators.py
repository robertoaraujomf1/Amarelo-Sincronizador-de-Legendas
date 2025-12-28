import os

class Validators:
    @staticmethod
    def is_video_file(file_path):
        """Verifica se o arquivo é um vídeo suportado"""
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
        _, ext = os.path.splitext(file_path)
        return ext.lower() in video_extensions and os.path.isfile(file_path)
    
    @staticmethod
    def is_subtitle_file(file_path):
        """Verifica se o arquivo é uma legenda suportada"""
        subtitle_extensions = ['.srt', '.vtt', '.ass', '.ssa']
        _, ext = os.path.splitext(file_path)
        return ext.lower() in subtitle_extensions and os.path.isfile(file_path)
    
    @staticmethod
    def is_directory(path):
        """Verifica se o caminho é um diretório válido"""
        return os.path.exists(path) and os.path.isdir(path)
    
    @staticmethod
    def validate_hex_color(color):
        """Valida se a string é uma cor HEX válida"""
        if not color.startswith('#'):
            return False
        
        color = color[1:]
        return len(color) in (3, 6) and all(c in '0123456789ABCDEFabcdef' for c in color)