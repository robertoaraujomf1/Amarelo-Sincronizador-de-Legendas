import os
import logging
import time
from typing import Set

logger = logging.getLogger(__name__)

class FileLocker:
    """Gerencia bloqueio de arquivos para evitar processamento duplicado"""
    
    def __init__(self):
        self.locked_files: Set[str] = set()
    
    def lock_file(self, file_path: str) -> bool:
        """
        Tenta bloquear um arquivo para processamento.
        
        Args:
            file_path: Caminho do arquivo a ser bloqueado
            
        Returns:
            True se o arquivo foi bloqueado, False se já estava bloqueado
        """
        if file_path in self.locked_files:
            logger.warning(f"Arquivo já está bloqueado: {file_path}")
            return False
        
        self.locked_files.add(file_path)
        logger.debug(f"Arquivo bloqueado: {file_path}")
        return True
    
    def unlock_file(self, file_path: str) -> bool:
        """
        Libera o bloqueio de um arquivo.
        
        Args:
            file_path: Caminho do arquivo a ser liberado
            
        Returns:
            True se o arquivo foi liberado, False se não estava bloqueado
        """
        if file_path in self.locked_files:
            self.locked_files.remove(file_path)
            logger.debug(f"Arquivo liberado: {file_path}")
            return True
        
        logger.warning(f"Arquivo não estava bloqueado: {file_path}")
        return False
    
    def is_locked(self, file_path: str) -> bool:
        """Verifica se um arquivo está bloqueado"""
        return file_path in self.locked_files
    
    def clear_all_locks(self):
        """Libera todos os bloqueios"""
        self.locked_files.clear()
        logger.debug("Todos os bloqueios foram liberados")