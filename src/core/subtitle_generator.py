class SubtitleGenerator:
    def __init__(self, config_manager=None):
        self.config = config_manager

    def format_timestamp(self, seconds):
        """Converte segundos para o formato SRT: HH:MM:SS,mmm"""
        td_hours = int(seconds // 3600)
        td_mins = int((seconds % 3600) // 60)
        td_secs = int(seconds % 60)
        td_msecs = int((seconds - int(seconds)) * 1000)
        return f"{td_hours:02d}:{td_mins:02d}:{td_secs:02d},{td_msecs:03d}"

    def generate(self, segments, output_path):
        """Gera o arquivo .srt a partir dos segmentos do Whisper"""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for i, segment in enumerate(segments, start=1):
                    start = self.format_timestamp(segment['start'])
                    end = self.format_timestamp(segment['end'])
                    text = segment['text'].strip()
                    
                    f.write(f"{i}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")
            return True
        except Exception as e:
            print(f"Erro ao gerar SRT: {e}")
            return False