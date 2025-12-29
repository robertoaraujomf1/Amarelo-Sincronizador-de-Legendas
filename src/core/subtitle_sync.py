import os
import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)

class SubtitleSynchronizer:
    """Sincroniza legendas com o vídeo"""
    
    def __init__(self):
        self.time_pattern = re.compile(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})')
    
    def load_subtitles(self, file_path: str) -> List[Dict]:
        """
        Carrega legendas de arquivo
        
        Args:
            file_path: Caminho do arquivo de legenda
            
        Returns:
            Lista de legendas
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.srt':
            return self._load_srt(file_path)
        elif ext in ['.ass', '.ssa']:
            return self._load_ass(file_path)
        elif ext == '.vtt':
            return self._load_vtt(file_path)
        else:
            raise ValueError(f"Formato de legenda não suportado: {ext}")
    
    def _load_srt(self, file_path: str) -> List[Dict]:
        """Carrega arquivo SRT"""
        subtitles = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Dividir por linhas em branco
        blocks = [b.strip() for b in content.split('\n\n') if b.strip()]
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) < 3:
                continue
            
            # Extrair tempos
            time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', lines[1])
            if not time_match:
                continue
            
            start_time = self._parse_time(time_match.group(1))
            end_time = self._parse_time(time_match.group(2))
            
            # Juntar texto (pode ter múltiplas linhas)
            text = '\n'.join(lines[2:])
            
            subtitles.append({
                'index': len(subtitles) + 1,
                'start': start_time,
                'end': end_time,
                'text': text,
                'original_text': text
            })
        
        return subtitles
    
    def _load_ass(self, file_path: str) -> List[Dict]:
        """Carrega arquivo ASS/SSA"""
        subtitles = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_events = False
        for line in lines:
            line = line.strip()
            
            if line.startswith('[Events]'):
                in_events = True
                continue
            
            if in_events and line.startswith('Dialogue:'):
                parts = line.split(',', 9)
                if len(parts) >= 10:
                    start_time = self._parse_ass_time(parts[1])
                    end_time = self._parse_ass_time(parts[2])
                    text = parts[9]
                    
                    # Remover tags de formatação
                    text = re.sub(r'\{[^}]*\}', '', text)
                    
                    subtitles.append({
                        'index': len(subtitles) + 1,
                        'start': start_time,
                        'end': end_time,
                        'text': text,
                        'original_text': text
                    })
        
        return subtitles
    
    def _load_vtt(self, file_path: str) -> List[Dict]:
        """Carrega arquivo WebVTT"""
        subtitles = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Pular cabeçalho e linhas vazias
            if line == 'WEBVTT' or not line:
                i += 1
                continue
            
            # Tentar encontrar linha de tempo
            time_match = re.match(r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})', line)
            if time_match:
                start_time = self._parse_time(time_match.group(1).replace('.', ','))
                end_time = self._parse_time(time_match.group(2).replace('.', ','))
                
                # Coletar texto
                text_lines = []
                i += 1
                while i < len(lines) and lines[i].strip():
                    text_lines.append(lines[i].strip())
                    i += 1
                
                text = ' '.join(text_lines)
                
                subtitles.append({
                    'index': len(subtitles) + 1,
                    'start': start_time,
                    'end': end_time,
                    'text': text,
                    'original_text': text
                })
            else:
                i += 1
        
        return subtitles
    
    def sync_subtitles(self, subtitles: List[Dict], video_info: Dict) -> List[Dict]:
        """
        Sincroniza legendas com o vídeo
        
        Args:
            subtitles: Lista de legendas
            video_info: Informações do vídeo
            
        Returns:
            Legendas sincronizadas
        """
        synced_subtitles = []
        
        # Obter informações do vídeo
        video_duration = video_info.get('duration', 0)
        scene_changes = video_info.get('scenes', [])
        
        if not subtitles or video_duration <= 0:
            return subtitles
        
        # Calcular deslocamento baseado na primeira cena
        if scene_changes:
            first_scene = scene_changes[0]
            first_subtitle = subtitles[0]['start']
            
            # Ajustar para que primeira legenda comece na primeira cena
            offset = first_scene - first_subtitle
            
            for sub in subtitles:
                new_start = max(0, sub['start'] + offset)
                new_end = min(video_duration, sub['end'] + offset)
                
                # Garantir que a legenda não seja muito curta
                if new_end - new_start < 0.5:  # Mínimo 0.5 segundos
                    new_end = new_start + 1.0
                
                synced_sub = sub.copy()
                synced_sub['start'] = new_start
                synced_sub['end'] = new_end
                synced_subtitles.append(synced_sub)
        else:
            # Sem detecção de cenas, manter tempos originais
            synced_subtitles = subtitles
        
        return synced_subtitles
    
    def _parse_time(self, time_str: str) -> float:
        """Converte string de tempo para segundos"""
        match = self.time_pattern.match(time_str.replace(',', '.'))
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            milliseconds = int(match.group(4))
            
            return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
        
        return 0.0
    
    def _parse_ass_time(self, time_str: str) -> float:
        """Converte tempo ASS para segundos"""
        parts = time_str.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_parts = parts[2].split('.')
            seconds = int(seconds_parts[0])
            centiseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            
            return hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0
        
        return 0.0