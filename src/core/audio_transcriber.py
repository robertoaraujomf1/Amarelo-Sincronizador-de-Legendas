import speech_recognition as sr
from pydub import AudioSegment
import os
import tempfile

class AudioTranscriber:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    def extract_audio_from_video(self, video_path, audio_output_path):
        """Extrai áudio do vídeo"""
        try:
            audio = AudioSegment.from_file(video_path)
            audio.export(audio_output_path, format="wav")
            return True
        except Exception as e:
            print(f"Erro ao extrair áudio: {str(e)}")
            return False
    
    def transcribe_audio(self, audio_path, language='pt-BR'):
        """Transcreve áudio para texto"""
        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data, language=language)
                return text
        except Exception as e:
            print(f"Erro na transcrição: {str(e)}")
            return ""
    
    def transcribe_video(self, video_path, language='pt-BR'):
        """Transcreve áudio de vídeo diretamente"""
        try:
            # Criar arquivo temporário para áudio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            # Extrair áudio do vídeo
            if not self.extract_audio_from_video(video_path, temp_audio_path):
                return ""
            
            # Transcrever áudio
            transcription = self.transcribe_audio(temp_audio_path, language)
            
            # Limpar arquivo temporário
            try:
                os.unlink(temp_audio_path)
            except:
                pass
            
            return transcription
            
        except Exception as e:
            print(f"Erro na transcrição do vídeo: {str(e)}")
            return ""