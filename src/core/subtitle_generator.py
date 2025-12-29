import os
import logging
from typing import List, Dict, Any, Optional
from datetime import timedelta
import re

logger = logging.getLogger(__name__)

class SubtitleGenerator:
    """Gera arquivos de legenda formatados"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.time_pattern = re.compile(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})')
    
    def parse_srt(self, srt_content: str) -> List[Dict]:
        """Parse do conteúdo SRT para lista de legendas"""
        subtitles = []
        blocks = [b.strip() for b in srt_content.split('\n\n') if b.strip()]
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                try:
                    index = int(lines[0].strip())
                    
                    # Extrair tempos
                    time_match = re.match(
                        r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3}) --> (\d{2}):(\d{2}):(\d{2})[,.](\d{3})', 
                        lines[1]
                    )
                    
                    if time_match:
                        start_time = self._parse_srt_time(
                            f"{time_match.group(1)}:{time_match.group(2)}:{time_match.group(3)},{time_match.group(4)}"
                        )
                        end_time = self._parse_srt_time(
                            f"{time_match.group(5)}:{time_match.group(6)}:{time_match.group(7)},{time_match.group(8)}"
                        )
                        
                        # Juntar texto (pode ter múltiplas linhas)
                        text = '\n'.join(lines[2:])
                        
                        subtitles.append({
                            "index": index,
                            "start": start_time,
                            "end": end_time,
                            "text": text,
                            "original_text": text
                        })
                except (ValueError, IndexError) as e:
                    logger.warning(f"Erro ao parsear bloco SRT: {e}")
                    continue
        
        return subtitles
    
    def generate_from_segments(self, segments: List[Dict]) -> str:
        """Gera conteúdo SRT a partir de segmentos"""
        srt_content = ""
        
        for seg in segments:
            # Converter segundos para formato SRT
            start_str = self._format_timedelta_srt(seg.get("start", 0))
            end_str = self._format_timedelta_srt(seg.get("end", 0))
            
            srt_content += f"{seg.get('index', 1)}\n"
            srt_content += f"{start_str} --> {end_str}\n"
            srt_content += f"{seg.get('text', '')}\n\n"
        
        return srt_content
    
    def apply_formatting(self, subtitles: List[Dict], font_config: Dict) -> List[Dict]:
        """
        Aplica formatação às legendas
        
        Args:
            subtitles: Lista de legendas
            font_config: Configurações de fonte (tamanho, cor, negrito)
            
        Returns:
            Legendas com formatação aplicada
        """
        formatted_subs = []
        
        for sub in subtitles:
            formatted_sub = sub.copy()
            text = sub.get('text', '')
            
            # Aplicar formatação baseada no formato escolhido
            format_type = font_config.get('format_type', 'ass')
            
            if format_type == 'ass':
                formatted_text = self._apply_ass_formatting(text, font_config)
            elif format_type == 'srt':
                formatted_text = self._apply_srt_formatting(text, font_config)
            else:
                formatted_text = text
            
            formatted_sub['formatted_text'] = formatted_text
            formatted_sub['font_config'] = font_config
            formatted_subs.append(formatted_sub)
        
        return formatted_subs
    
    def _apply_ass_formatting(self, text: str, font_config: Dict) -> str:
        """Aplica formatação no formato ASS/SSA"""
        tags = []
        
        # Cor da fonte
        if 'color' in font_config:
            color = font_config['color']
            # Converter para formato BGR usado no ASS
            if color.startswith('#'):
                color = color[1:]
                if len(color) == 6:
                    # RGB para BGR
                    bgr = color[4:6] + color[2:4] + color[0:2]
                    tags.append(f"\\c&H{bgr}&")
        
        # Tamanho da fonte
        if 'size' in font_config:
            size = font_config['size']
            tags.append(f"\\fs{size}")
        
        # Negrito
        if font_config.get('bold', False):
            tags.append("\\b1")
        
        if tags:
            return f"{{\\{'\\'.join(tags)}}}{text}{{\\r}}"
        
        return text
    
    def _apply_srt_formatting(self, text: str, font_config: Dict) -> str:
        """Aplica formatação básica para SRT (HTML)"""
        formatted = text
        
        if font_config.get('bold', False):
            formatted = f"<b>{formatted}</b>"
        
        # SRT não suporta cor e tamanho via HTML padrão
        return formatted
    
    def generate_subtitle_files(self, subtitles: List[Dict], video_path: str) -> Dict[str, str]:
        """
        Gera arquivos de legenda em diferentes formatos
        
        Args:
            subtitles: Legendas formatadas
            video_path: Caminho do vídeo original
            
        Returns:
            Dicionário com caminhos dos arquivos gerados
        """
        output_files = {}
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # Obter diretório de saída da configuração ou usar padrão
        output_dir = self.config.get('output_dir', 'output') if isinstance(self.config, dict) else 'output'
        if hasattr(self.config, 'get'):
            output_dir = self.config.get('output_dir', 'output')
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Gerar SRT
        srt_path = os.path.join(output_dir, f"{base_name}.srt")
        self._generate_srt(srt_path, subtitles)
        output_files['srt'] = srt_path
        
        # Gerar ASS (com formatação completa)
        ass_path = os.path.join(output_dir, f"{base_name}.ass")
        self._generate_ass(ass_path, subtitles)
        output_files['ass'] = ass_path
        
        return output_files
    
    def _generate_srt(self, file_path: str, subtitles: List[Dict]):
        """Gera arquivo SRT"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for i, sub in enumerate(subtitles, 1):
                start = self._format_timedelta_srt(sub.get('start', 0))
                end = self._format_timedelta_srt(sub.get('end', 0))
                
                # Usar texto formatado se disponível, senão texto normal
                text = sub.get('formatted_text', sub.get('text', ''))
                
                f.write(f"{i}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")
    
    def _generate_ass(self, file_path: str, subtitles: List[Dict]):
        """Gera arquivo ASS com formatação"""
        if not subtitles:
            return
        
        # Obter configuração de fonte das legendas
        font_config = subtitles[0].get('font_config', {}) if subtitles else {}
        
        header = self._generate_ass_header(font_config)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(header)
            
            for sub in subtitles:
                start = self._format_timedelta_ass(sub.get('start', 0))
                end = self._format_timedelta_ass(sub.get('end', 0))
                
                # Usar texto formatado se disponível, senão texto normal
                text = sub.get('formatted_text', sub.get('text', ''))
                
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")
    
    def _generate_ass_header(self, font_config: Dict) -> str:
        """Gera cabeçalho do arquivo ASS"""
        font_name = font_config.get('name', 'Arial')
        font_size = font_config.get('size', 20)
        font_color = font_config.get('color', '#FFFFFF')
        
        # Converter cor para formato ASS
        if font_color.startswith('#'):
            color = font_color[1:]
            if len(color) == 6:
                bgr = color[4:6] + color[2:4] + color[0:2]
                ass_color = f"&H{bgr}&"
            else:
                ass_color = "&H00FFFFFF&"
        else:
            ass_color = "&H00FFFFFF&"
        
        bold = -1 if font_config.get('bold', False) else 0
        
        header = f"""[Script Info]
Title: Amarelo Legendas
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{ass_color},&H000000FF,&H00000000,&H00000000,{bold},0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        return header
    
    def _parse_srt_time(self, time_str: str) -> float:
        """Converte string de tempo SRT para segundos"""
        return self._parse_time(time_str.replace('.', ','))
    
    def _parse_time(self, time_str: str) -> float:
        """Converte string de tempo para segundos"""
        match = self.time_pattern.match(time_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            milliseconds = int(match.group(4))
            
            return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
        
        return 0.0
    
    def _format_timedelta_srt(self, seconds: float) -> str:
        """Formata segundos para SRT (HH:MM:SS,mmm)"""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = int((td.microseconds // 1000))
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def _format_timedelta_ass(self, seconds: float) -> str:
        """Formata segundos para ASS (H:MM:SS.cc)"""
        td = timedelta(seconds=seconds)
        total_seconds = td.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        centiseconds = int((td.microseconds // 10000))
        
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"
    
    def generate_subtitles_from_transcription(self, transcription: Dict, video_info: Dict = None) -> List[Dict]:
        """
        Gera legendas a partir de uma transcrição
        
        Args:
            transcription: Resultado da transcrição com segmentos
            video_info: Informações do vídeo (opcional)
            
        Returns:
            Lista de legendas
        """
        subtitles = []
        segments = transcription.get('segments', [])
        
        for i, segment in enumerate(segments, 1):
            subtitles.append({
                'index': i,
                'start': segment.get('start', 0),
                'end': segment.get('end', 0),
                'text': segment.get('text', ''),
                'confidence': segment.get('confidence', 1.0)
            })
        
        return subtitles
    
    def save_subtitles(self, subtitles: List[Dict], output_path: str, format: str = 'srt'):
        """
        Salva legendas em um arquivo
        
        Args:
            subtitles: Lista de legendas
            output_path: Caminho do arquivo de saída
            format: Formato do arquivo ('srt' ou 'ass')
        """
        if format.lower() == 'srt':
            self._generate_srt(output_path, subtitles)
        elif format.lower() in ['ass', 'ssa']:
            self._generate_ass(output_path, subtitles)
        else:
            raise ValueError(f"Formato não suportado: {format}")