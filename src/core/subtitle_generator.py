import os
from datetime import timedelta

class SubtitleGenerator:
    """Gerador de arquivos de legenda formatados"""
    
    def generate(self, subtitles, output_path, font_settings=None):
        """
        Gera arquivo de legenda formatado.
        
        Args:
            subtitles: Lista de dicionários com 'start', 'end', 'text'
            output_path: Caminho do arquivo de saída
            font_settings: Dicionário com configurações de fonte
        """
        if font_settings is None:
            font_settings = {'size': 20, 'color': '#FFFFFF', 'bold': False}
        
        # Determinar formato baseado na extensão
        ext = os.path.splitext(output_path)[1].lower()
        
        if ext == '.srt':
            self._generate_srt(subtitles, output_path)
        elif ext in ['.ass', '.ssa']:
            self._generate_ass(subtitles, output_path, font_settings)
        elif ext == '.vtt':
            self._generate_vtt(subtitles, output_path)
        else:
            # Padrão para SRT
            self._generate_srt(subtitles, output_path)
            
    def _generate_srt(self, subtitles, output_path):
        """Gera arquivo SRT"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, sub in enumerate(subtitles, 1):
                start_time = self._format_srt_time(sub['start'])
                end_time = self._format_srt_time(sub['end'])
                text = sub['text']
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
                
    def _generate_ass(self, subtitles, output_path, font_settings):
        """Gera arquivo ASS com formatação"""
        with open(output_path, 'w', encoding='utf-8') as f:
            # Cabeçalho ASS
            f.write("[Script Info]\n")
            f.write("ScriptType: v4.00+\n")
            f.write("PlayResX: 384\n")
            f.write("PlayResY: 288\n")
            f.write("\n")
            
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                   "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
                   "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                   "Alignment, MarginL, MarginR, MarginV, Encoding\n")
            
            # Definir estilo baseado nas configurações
            font_name = "Arial"
            font_size = font_settings['size']
            font_color = self._color_to_bgr(font_settings['color'])
            bold = -1 if font_settings['bold'] else 0
            
            f.write(f"Style: Default,{font_name},{font_size},&H{font_color},&HFFFFFF,"
                   f"&H000000,&H000000,{bold},0,0,0,100,100,0,0,1,2,2,2,10,10,10,1\n")
            f.write("\n")
            
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
                   "Effect, Text\n")
            
            # Eventos (legendas)
            for sub in subtitles:
                start_time = self._format_ass_time(sub['start'])
                end_time = self._format_ass_time(sub['end'])
                text = sub['text'].replace('\n', '\\N')
                
                f.write(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n")
                
    def _generate_vtt(self, subtitles, output_path):
        """Gera arquivo WebVTT"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            for i, sub in enumerate(subtitles, 1):
                start_time = self._format_vtt_time(sub['start'])
                end_time = self._format_vtt_time(sub['end'])
                text = sub['text']
                
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
                
    def _format_srt_time(self, seconds):
        """Formata tempo para SRT"""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        seconds = td.seconds % 60
        milliseconds = td.microseconds // 1000
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
        
    def _format_ass_time(self, seconds):
        """Formata tempo para ASS"""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        seconds_total = td.seconds % 60 + td.microseconds / 1000000
        
        return f"{hours}:{minutes:02d}:{seconds_total:05.2f}"
        
    def _format_vtt_time(self, seconds):
        """Formata tempo para WebVTT"""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        seconds_total = td.seconds % 60 + td.microseconds / 1000000
        
        return f"{hours:02d}:{minutes:02d}:{seconds_total:06.3f}"
        
    def _color_to_bgr(self, color):
        """Converte cor Qt para BGR hexadecimal"""
        if hasattr(color, 'name'):
            hex_color = color.name()[1:]  # Remove '#'
        else:
            hex_color = str(color).replace('#', '')
            
        # Converter RGB para BGR
        if len(hex_color) == 6:
            r = hex_color[0:2]
            g = hex_color[2:4]
            b = hex_color[4:6]
            return f"{b}{g}{r}"
        else:
            return "FFFFFF"