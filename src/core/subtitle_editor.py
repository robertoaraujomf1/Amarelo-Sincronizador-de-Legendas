import pysrt
import re
from datetime import timedelta
from typing import Dict, Optional, Any
import os

class SubtitleEditor:
    def __init__(self):
        self.max_lines = 2
        self.max_chars_per_line = 42  # Baseado em telas padrão

    def read_subtitle(self, file_path: str) -> Optional[Dict]:
        """Lê um arquivo de legenda e o converte para um formato de dicionário."""
        try:
            subs = pysrt.open(file_path, encoding='utf-8')
            segments = []
            for i, sub in enumerate(subs):
                segments.append({
                    'index': i + 1,
                    'start': str(sub.start),
                    'end': str(sub.end),
                    'text': sub.text
                })
            
            return {'language': 'unknown', 'segments': segments}
        except Exception as e:
            print(f"❌ Erro ao ler legenda '{file_path}': {e}")
            return None

    def save_subtitle(self, subtitle_content: Dict, output_path: str, settings: Dict[str, Any]) -> bool:
        """Salva o conteúdo da legenda em um arquivo .srt."""
        try:
            if not subtitle_content or 'segments' not in subtitle_content:
                print("⚠️ Conteúdo de legenda inválido para salvar.")
                return False
            
            valid_segments = [s for s in subtitle_content['segments'] if s.get('text', '').strip()]
            if not valid_segments:
                print("⚠️ Nenhum segmento para salvar. Arquivo não será criado.")
                return False

            subs = pysrt.SubRipFile()
            for seg in valid_segments:
                try:
                    start_time = pysrt.SubRipTime.from_string(seg['start'])
                    end_time = pysrt.SubRipTime.from_string(seg['end'])
                    
                    sub = pysrt.SubRipItem(
                        index=seg['index'],
                        start=start_time,
                        end=end_time,
                        text=seg['text']
                    )
                    subs.append(sub)
                except Exception as e:
                    print(f"⚠️ Ignorando segmento inválido: {seg}. Erro: {e}")

            subs.save(output_path, encoding='utf-8')
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar legenda em '{output_path}': {e}")
            return False
    
    def apply_formatting(self, subs, subtitle_settings, video_info):
        """Aplica formatação às legendas"""
        formatted_subs = pysrt.SubRipFile()
        
        for sub in subs:
            # Formatar texto
            formatted_text = self.format_subtitle_text(
                sub.text, 
                subtitle_settings, 
                video_info
            )
            
            # Criar nova legenda com texto formatado
            new_sub = pysrt.SubRipItem(
                index=sub.index,
                start=sub.start,
                end=sub.end,
                text=formatted_text
            )
            
            formatted_subs.append(new_sub)
        
        return formatted_subs
    
    def format_subtitle_text(self, text, settings, video_info):
        """Formata o texto da legenda de acordo com as configurações"""
        # Limpar tags HTML existentes
        clean_text = self.clean_html_tags(text)
        
        # Quebrar texto em linhas se necessário
        lines = self.break_text_into_lines(clean_text, settings['font_size'], video_info['width'])
        
        # Aplicar formatação ASS
        formatted_lines = []
        for line in lines:
            formatted_line = self.apply_ass_formatting(line, settings)
            formatted_lines.append(formatted_line)
        
        return '\\N'.join(formatted_lines)
    
    def clean_html_tags(self, text):
        """Remove tags HTML do texto"""
        # Remover tags simples
        text = re.sub(r'<[^>]+>', '', text)
        
        # Substituir entidades HTML
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        return text.strip()
    
    def break_text_into_lines(self, text, font_size, screen_width):
        """Quebra o texto em linhas que cabem na tela"""
        words = text.split()
        lines = []
        current_line = []
        
        # Calcular largura máxima baseada no tamanho da fonte e resolução
        max_chars = self.calculate_max_chars(font_size, screen_width)
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if len(test_line) <= max_chars:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                
                # Limitar número de linhas
                if len(lines) >= self.max_lines:
                    break
        
        if current_line and len(lines) < self.max_lines:
            lines.append(' '.join(current_line))
        
        # Se excedeu o número máximo de linhas, truncar
        if len(lines) > self.max_lines:
            lines = lines[:self.max_lines]
            # Adicionar "..." na última linha se truncado
            last_line = lines[-1]
            if len(last_line) > 3:
                lines[-1] = last_line[:-3] + '...'
            else:
                lines[-1] = '...'
        
        return lines
    
    def calculate_max_chars(self, font_size, screen_width):
        """Calcula o número máximo de caracteres por linha"""
        # Estimativa base: caracteres por linha baseado na resolução e tamanho da fonte
        base_width = 1920  # Resolução base
        base_chars = 42    # Caracteres na resolução base
        
        # Ajustar baseado na resolução real
        width_ratio = screen_width / base_width
        adjusted_chars = int(base_chars * width_ratio)
        
        # Ajustar baseado no tamanho da fonte
        font_ratio = 16 / font_size  # Tamanho de fonte base: 16
        final_chars = int(adjusted_chars * font_ratio)
        
        return max(20, min(60, final_chars))  # Limites razoáveis
    
    def apply_ass_formatting(self, text, settings):
        """Aplica formatação ASS à linha de texto"""
        font_name = settings['font_family']
        font_size = settings['font_size']
        font_color = self.rgb_to_bgr(settings['font_color'])
        
        # Formatação ASS para centralizar na parte inferior
        ass_format = (
            f"{{\\an8\\fn{font_name}\\fs{font_size}\\c&H{font_color}&\\pos({0},{0})}}"
        )
        
        return f"{ass_format}{text}"
    
    def rgb_to_bgr(self, hex_color):
        """Converte cor HEX RGB para BGR (formato ASS)"""
        hex_color = hex_color.lstrip('#')
        
        if len(hex_color) == 6:
            r = hex_color[0:2]
            g = hex_color[2:4]
            b = hex_color[4:6]
        else:
            r = g = b = 'FF'
        
        return f"{b}{g}{r}"