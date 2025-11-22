import pysrt
from datetime import timedelta

class SubtitleGenerator:
    def __init__(self):
        pass
    
    def create_subtitle_from_transcription(self, transcription, video_duration, output_path, language='pt-BR'):
        """Cria arquivo de legenda a partir da transcrição"""
        try:
            subs = pysrt.SubRipFile()
            
            # Dividir transcrição em frases
            sentences = self.split_into_sentences(transcription)
            
            # Calcular duração por frase
            if sentences:
                time_per_sentence = video_duration / len(sentences)
                
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        start_time = i * time_per_sentence
                        end_time = (i + 1) * time_per_sentence
                        
                        # Criar item de legenda
                        sub_item = pysrt.SubRipItem(
                            index=i + 1,
                            start=self.seconds_to_subrip_time(start_time),
                            end=self.seconds_to_subrip_time(end_time),
                            text=sentence.strip()
                        )
                        subs.append(sub_item)
            
            # Salvar arquivo
            subs.save(output_path, encoding='utf-8')
            return True
            
        except Exception as e:
            print(f"Erro ao criar legenda: {str(e)}")
            return False
    
    def split_into_sentences(self, text):
        """Divide texto em sentenças"""
        # Divisão simples por pontuação
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def seconds_to_subrip_time(self, seconds):
        """Converte segundos para formato SubRipTime"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds - int(seconds)) * 1000)
        
        return pysrt.SubRipTime(hours, minutes, secs, millisecs)