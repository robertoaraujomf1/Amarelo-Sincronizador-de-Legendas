from datetime import timedelta
import re
from typing import List, Dict


class SubtitleGenerator:
    def __init__(self):
        pass

    def _format_time(self, seconds: float) -> str:
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        millis = int((seconds - total_seconds) * 1000)

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    def _parse_time(self, time_str: str) -> float:
        """Converte string de tempo SRT (HH:MM:SS,mmm) para segundos"""
        time_pattern = r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
        match = re.match(time_pattern, time_str)
        if not match:
            return 0.0
        
        hours, minutes, seconds, millis = map(int, match.groups())
        return hours * 3600 + minutes * 60 + seconds + millis / 1000.0

    def parse_srt(self, srt_content: str) -> List[Dict[str, any]]:
        """
        Parse SRT content into list of subtitle dictionaries.
        Returns: [{start, end, text}, ...]
        """
        subtitles = []
        blocks = re.split(r'\n\s*\n', srt_content.strip())
        
        for block in blocks:
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            if len(lines) < 3:
                continue
            
            # Skip index line (first line)
            time_line = lines[1]
            text_lines = lines[2:]
            
            # Parse time line (e.g., "00:00:01,234 --> 00:00:03,456")
            time_match = re.match(r'(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})', time_line)
            if not time_match:
                continue
            
            start_time = self._parse_time(time_match.group(1))
            end_time = self._parse_time(time_match.group(2))
            text = ' '.join(text_lines)
            
            subtitles.append({
                "start": start_time,
                "end": end_time,
                "text": text
            })
        
        return subtitles

    def generate_from_segments(self, segments: List[Dict]) -> str:
        """
        segments: [{start, end, text}]
        """
        lines = []

        for idx, seg in enumerate(segments, start=1):
            start = self._format_time(seg["start"])
            end = self._format_time(seg["end"])
            text = seg["text"]

            lines.append(str(idx))
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")

        return "\n".join(lines).strip() + "\n"

    def save(self, srt_content: str, output_path):
        """Salva o conteúdo SRT em um arquivo"""
        from pathlib import Path
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
