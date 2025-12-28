import os
import msvcrt
import threading

class FileLocker:
    def __init__(self):
        self.locked_files = {}
        self.lock = threading.Lock()
    
    def lock_file(self, file_path):
        """Bloqueia um arquivo para evitar modificações externas"""
        if not os.path.exists(file_path):
            return None
        
        try:
            # Tentar abrir o arquivo em modo exclusivo
            file_handle = open(file_path, 'r+b')
            
            # Tentar travar o arquivo
            try:
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
            except IOError:
                file_handle.close()
                return None
            
            with self.lock:
                self.locked_files[file_path] = file_handle
            
            return file_path
            
        except Exception as e:
            print(f"Erro ao bloquear arquivo {file_path}: {str(e)}")
            return None
    
    def unlock_file(self, file_path):
        """Libera o bloqueio de um arquivo"""
        with self.lock:
            if file_path in self.locked_files:
                file_handle = self.locked_files[file_path]
                try:
                    # Liberar o lock
                    msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                    file_handle.close()
                except:
                    pass
                finally:
                    del self.locked_files[file_path]
    
    def unlock_all(self):
        """Libera todos os arquivos bloqueados"""
        with self.lock:
            for file_path in list(self.locked_files.keys()):
                self.unlock_file(file_path)