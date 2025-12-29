import os
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class FileMatcher:
    """Emparelha arquivos de vídeo com legendas baseado no nome"""
    
    def __init__(self):
        pass
    
    def match_files(self, video_paths: List[str], subtitle_paths: List[str]) -> List[Tuple[str, Optional[str]]]:
        """
        Emparelha vídeos com legendas baseado no nome do arquivo.
        
        Args:
            video_paths: Lista de caminhos de vídeo
            subtitle_paths: Lista de caminhos de legenda
            
        Returns:
            Lista de tuplas (video_path, subtitle_path ou None)
        """
        matched_pairs = []
        
        # Para cada vídeo, tenta encontrar uma legenda correspondente
        for video_path in video_paths:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            matched_subtitle = None
            
            # Procura por legendas com o mesmo nome base
            for subtitle_path in subtitle_paths:
                subtitle_name = os.path.splitext(os.path.basename(subtitle_path))[0]
                
                # Comparação simples de nomes
                if video_name == subtitle_name:
                    matched_subtitle = subtitle_path
                    break
            
            matched_pairs.append((video_path, matched_subtitle))
        
        logger.info(f"Emparelhados {len(matched_pairs)} vídeos com legendas")
        return matched_pairs