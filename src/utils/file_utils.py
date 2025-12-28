import os
import shutil

class FileUtils:
    @staticmethod
    def safe_move(src, dst):
        """Move um arquivo de forma segura, criando diretórios se necessário"""
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            return True
        except Exception as e:
            print(f"Erro ao mover arquivo {src} para {dst}: {str(e)}")
            return False
    
    @staticmethod
    def safe_copy(src, dst):
        """Copia um arquivo de forma segura, criando diretórios se necessário"""
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            print(f"Erro ao copiar arquivo {src} para {dst}: {str(e)}")
            return False
    
    @staticmethod
    def get_file_size(file_path):
        """Obtém o tamanho do arquivo em bytes"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    @staticmethod
    def format_file_size(size_bytes):
        """Formata o tamanho do arquivo para string legível"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"