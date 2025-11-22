import os
import pysrt
import chardet
from datetime import timedelta
import tempfile
import shutil

from .video_analyzer import VideoAnalyzer
from .file_matcher import FileMatcher
from .file_locker import FileLocker
from .subtitle_editor import SubtitleEditor
from .audio_transcriber import AudioTranscriber
from .translator import SubtitleTranslator
from .subtitle_generator import SubtitleGenerator

class SubtitleSyncEngine:
    def __init__(self):
        self.video_analyzer = VideoAnalyzer()
        self.file_matcher = FileMatcher()
        self.file_locker = FileLocker()
        self.subtitle_editor = SubtitleEditor()
        self.audio_transcriber = AudioTranscriber()
        self.translator = SubtitleTranslator()
        self.subtitle_generator = SubtitleGenerator()
        
        self.supported_video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
        self.supported_subtitle_extensions = ['.srt', '.vtt', '.ass', '.ssa']
    
    def find_video_subtitle_pairs(self, directory):
        """Encontra pares de vídeo e legenda no diretório"""
        return self.file_matcher.find_pairs(directory)
    
    def create_missing_subtitles(self, directory, target_language='pt_BR'):
        """Cria legendas faltantes através de transcrição e tradução"""
        try:
            # Encontrar vídeos sem legendas
            video_files = []
            subtitle_files = []
            
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    name, ext = os.path.splitext(file)
                    if ext.lower() in self.supported_video_extensions:
                        video_files.append((name, file_path))
                    elif ext.lower() in self.supported_subtitle_extensions:
                        subtitle_files.append((name, file_path))
            
            # Encontrar vídeos sem legendas correspondentes
            videos_without_subs = []
            for video_name, video_path in video_files:
                has_subtitle = False
                for subtitle_name, subtitle_path in subtitle_files:
                    if self.file_matcher.names_match(video_name, subtitle_name):
                        has_subtitle = True
                        break
                if not has_subtitle:
                    videos_without_subs.append((video_name, video_path))
            
            created_count = 0
            for video_name, video_path in videos_without_subs:
                # Analisar vídeo para obter duração
                video_info = self.video_analyzer.analyze_video(video_path)
                if not video_info:
                    continue
                
                # Transcrever áudio
                language_code = self.translator.get_language_code(target_language)
                transcription = self.audio_transcriber.transcribe_video(video_path, f"{language_code}-{language_code.upper()}")
                
                if transcription:
                    # Criar nome do arquivo de legenda
                    subtitle_path = os.path.join(directory, f"{video_name}.{language_code}.srt")
                    
                    # Gerar legenda
                    if self.subtitle_generator.create_subtitle_from_transcription(
                        transcription, video_info['duration'], subtitle_path, target_language
                    ):
                        created_count += 1
            
            return created_count
            
        except Exception as e:
            print(f"Erro ao criar legendas faltantes: {str(e)}")
            return 0
    
    def analyze_and_sync(self, video_path, subtitle_path, subtitle_settings):
        """Analisa e sincroniza um par vídeo-legenda"""
        try:
            # Bloquear arquivos
            video_lock = self.file_locker.lock_file(video_path)
            subtitle_lock = self.file_locker.lock_file(subtitle_path)
            
            if not video_lock or not subtitle_lock:
                return False
            
            try:
                # Detectar encoding da legenda
                encoding = self.detect_encoding(subtitle_path)
                
                # Carregar legenda
                subs = pysrt.open(subtitle_path, encoding=encoding)
                
                # Analisar vídeo
                video_info = self.video_analyzer.analyze_video(video_path)
                
                if not video_info:
                    return False
                
                # Verificar sincronização
                sync_issues = self.check_synchronization(subs, video_info)
                
                if sync_issues:
                    # Aplicar correções
                    corrected_subs = self.apply_sync_corrections(subs, sync_issues)
                    
                    # Aplicar formatação
                    formatted_subs = self.subtitle_editor.apply_formatting(
                        corrected_subs, subtitle_settings, video_info
                    )
                    
                    # Tentar salvar no local original
                    try:
                        formatted_subs.save(subtitle_path, encoding=encoding)
                        return True
                    except Exception:
                        # Se não for possível, salvar em pasta de saída
                        output_dir = os.path.join(os.path.dirname(video_path), "legendas_corrigidas")
                        os.makedirs(output_dir, exist_ok=True)
                        
                        output_path = os.path.join(output_dir, os.path.basename(subtitle_path))
                        formatted_subs.save(output_path, encoding=encoding)
                        return True
                
                return True  # Já estava sincronizado
                
            finally:
                # Liberar bloqueios
                if video_lock:
                    self.file_locker.unlock_file(video_lock)
                if subtitle_lock:
                    self.file_locker.unlock_file(subtitle_lock)
                    
        except Exception as e:
            print(f"Erro ao sincronizar {video_path}: {str(e)}")
            return False
    
    def detect_encoding(self, file_path):
        """Detecta o encoding do arquivo de legenda"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                return result['encoding'] or 'utf-8'
        except:
            return 'utf-8'
    
    def check_synchronization(self, subs, video_info):
        """Verifica problemas de sincronização"""
        issues = []
        
        if not subs:
            return issues
        
        # Verificar se as legendas estão dentro da duração do vídeo
        video_duration = video_info['duration']
        
        for i, sub in enumerate(subs):
            # Verificar se a legenda começa antes do vídeo
            if sub.start.ordinal < 0:
                issues.append({
                    'type': 'start_before_video',
                    'index': i,
                    'subtitle': sub
                })
            
            # Verificar se a legenda termina depois do vídeo
            if sub.end.ordinal > video_duration * 1000:  # Converter para milissegundos
                issues.append({
                    'type': 'end_after_video',
                    'index': i,
                    'subtitle': sub
                })
            
            # Verificar intervalos muito curtos ou longos
            sub_duration = (sub.end - sub.start).ordinal / 1000.0  # Em segundos
            if sub_duration < 1.0:
                issues.append({
                    'type': 'too_short',
                    'index': i,
                    'subtitle': sub
                })
            elif sub_duration > 10.0:
                issues.append({
                    'type': 'too_long',
                    'index': i,
                    'subtitle': sub
                })
        
        return issues
    
    def apply_sync_corrections(self, subs, issues):
        """Aplica correções de sincronização"""
        for issue in issues:
            idx = issue['index']
            sub = issue['subtitle']
            
            if issue['type'] == 'start_before_video':
                # Ajustar para começar no início do vídeo
                subs[idx].start = pysrt.SubRipTime(0, 0, 0, 0)
                if (sub.end - sub.start).ordinal < 1000:  # Menos de 1 segundo
                    subs[idx].end = pysrt.SubRipTime(0, 0, 3, 0)  # 3 segundos
                    
            elif issue['type'] == 'end_after_video':
                # Ajustar para terminar no final do vídeo
                # Esta correção seria mais complexa e requereria a duração exata
                pass
                
            elif issue['type'] == 'too_short':
                # Extender duração se for muito curta
                new_end = sub.start + timedelta(seconds=3)
                subs[idx].end = pysrt.SubRipTime(
                    hours=new_end.hours,
                    minutes=new_end.minutes,
                    seconds=new_end.seconds,
                    milliseconds=new_end.milliseconds
                )
                
            elif issue['type'] == 'too_long':
                # Reduzir duração se for muito longa
                new_end = sub.start + timedelta(seconds=8)
                subs[idx].end = pysrt.SubRipTime(
                    hours=new_end.hours,
                    minutes=new_end.minutes,
                    seconds=new_end.seconds,
                    milliseconds=new_end.milliseconds
                )
        
        return subs