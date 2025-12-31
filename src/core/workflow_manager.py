import os
import json
import tempfile
import subprocess
from datetime import timedelta
# Alterado para PyQt6
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

# Estes componentes devem estar implementados na pasta src/core/
from .transcription_engine import TranscriptionEngine
from .translator import Translator
from .subtitle_sync import SubtitleSync
from .subtitle_generator import SubtitleGenerator
from .video_analyzer import VideoAnalyzer
from .file_locker import FileLocker
from src.utils.validators import Validators

class WorkflowManager(QObject):
    """Gerencia o fluxo de trabalho completo (Orquestrador)"""
    
    # Sinais para comunicação com a GUI (Thread-safe)
    log_signal = pyqtSignal(str)
    subtitle_signal = pyqtSignal(dict)
    progress_signal = pyqtSignal(int)
    finished = pyqtSignal(list)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.stop_processing = False
        
        # Inicializar componentes de backend
        self.transcription_engine = TranscriptionEngine()
        self.translator = Translator()
        self.subtitle_sync = SubtitleSync()
        self.subtitle_generator = SubtitleGenerator()
        self.video_analyzer = VideoAnalyzer()
        self.validators = Validators()
        self.file_locker = FileLocker()
        
    @pyqtSlot()
    def process_all(self):
        """Método principal executado na worker thread"""
        results = []
        files_to_process = self.config.get('files', [])
        total_files = len(files_to_process)
        
        if total_files == 0:
            self.log_signal.emit("Nenhum arquivo para processar.")
            self.finished.emit([])
            return

        for idx, file_info in enumerate(files_to_process):
            if self.stop_processing:
                self.log_signal.emit("⚠️ Processamento interrompido pelo usuário.")
                break
                
            try:
                self.log_signal.emit(f"--- Processando {idx+1}/{total_files} ---")
                result = self.process_file(file_info)
                results.append(result)
                
                # Atualizar progresso da barra (0-100)
                progress = int(((idx + 1) / total_files) * 100)
                self.progress_signal.emit(progress)
                
            except Exception as e:
                error_msg = f"Erro em {os.path.basename(file_info['video_path'])}: {str(e)}"
                self.log_signal.emit(f"❌ {error_msg}")
                results.append({
                    'video': file_info['video_path'],
                    'success': False,
                    'error': str(e)
                })
        
        self.finished.emit(results)
        
    def process_file(self, file_info):
        """Fluxo lógico para um único arquivo"""
        video_path = file_info['video_path']
        subtitle_path = file_info['subtitle_path']
        has_subtitle = file_info['has_subtitle']
        video_name = os.path.basename(video_path)

        # Prevenção de concorrência
        if self.file_locker.is_locked(video_path):
            raise Exception(f"Arquivo já em uso.")
            
        self.file_locker.lock_file(video_path)
        
        try:
            # 1. Análise Técnica
            self.log_signal.emit(f"Analisando metadados de: {video_name}")
            video_info = self.video_analyzer.analyze(video_path)
            
            # 2. Decisão de Fluxo
            # CENÁRIO A: Tradução de legenda existente
            if has_subtitle and self.config['translate']:
                self.log_signal.emit("Traduzindo legenda SRT existente...")
                result = self.process_with_subtitle_and_translation(video_path, subtitle_path, video_info)
                
            # CENÁRIO B: Sincronização de legenda existente (sem tradução)
            elif has_subtitle and not self.config['translate']:
                self.log_signal.emit("Sincronizando legenda local...")
                result = self.process_with_subtitle_only(video_path, subtitle_path, video_info)
                
            # CENÁRIO C: Transcrição via IA (Whisper)
            else:
                self.log_signal.emit("Gerando transcrição via IA...")
                result = self.process_without_subtitle(video_path, video_info)
            
            # 3. Geração do Arquivo Final (.srt)
            subtitle_output = self.generate_subtitle_output(result, video_path, self.config['font_settings'])
            
            # 4. Hardcode Subtitles (Opcional - Merge no vídeo)
            if self.config['merge']:
                self.log_signal.emit("Iniciando renderização do vídeo com legenda (Hardsub)...")
                output_path = self.merge_subtitle_with_video(video_path, subtitle_output, self.config['font_settings'])
            else:
                output_path = subtitle_output
                
            return {
                'video': video_path,
                'success': True,
                'output': output_path
            }
            
        finally:
            self.file_locker.unlock_file(video_path)

    def process_with_subtitle_and_translation(self, video_path, subtitle_path, video_info):
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
            
        synced = self.subtitle_sync.synchronize(original_content, video_info)
        
        target_lang = self.config.get('target_language', 'pt-BR')
        translated = self.translator.translate_batch(synced, target_lang)
        
        # Emite sinal para a aba de "Pré-visualização" na UI
        for item in translated:
            self.subtitle_signal.emit({
                'start': self.format_time(item['start']),
                'end': self.format_time(item['end']),
                'original': item.get('original_text', ''),
                'text': item['text']
            })
            
        return {'type': 'translated', 'subtitles': translated}

    def process_without_subtitle(self, video_path, video_info):
        audio_path = self.extract_audio(video_path)
        try:
            transcription = self.transcription_engine.transcribe(audio_path)
            
            if self.config['translate']:
                target_lang = self.config.get('target_language', 'pt-BR')
                data = self.translator.translate_batch(transcription, target_lang)
                res_type = 'transcribed_translated'
            else:
                data = transcription
                res_type = 'transcribed'

            for item in data:
                self.subtitle_signal.emit({
                    'start': self.format_time(item['start']),
                    'end': self.format_time(item['end']),
                    'text': item['text']
                })
            return {'type': res_type, 'subtitles': data}
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)

    def extract_audio(self, video_path):
        temp_dir = tempfile.gettempdir()
        audio_output = os.path.join(temp_dir, f"temp_audio_{os.getpid()}.wav")
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-ac', '1', '-ar', '16000', '-vn', '-y',
            audio_output
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return audio_output

    def generate_subtitle_output(self, result, video_path, font_settings):
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        lang_suffix = self.config.get('target_language', 'out').split('-')[0]
        output_path = os.path.join(output_dir, f"{base_name}_{lang_suffix}.srt")
        
        self.subtitle_generator.generate(result['subtitles'], output_path, font_settings)
        return output_path

    def merge_subtitle_with_video(self, video_path, subtitle_path, font_settings):
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join("output", f"{base_name}_legendado.mp4")
        
        # Escapar caminho da legenda para o filtro do FFmpeg (importante para Windows)
        sub_filter_path = subtitle_path.replace("\\", "/").replace(":", "\\:")
        
        color = font_settings['color'].name().replace("#", "&H")
        # Inverter RGB para BGR (formato que o FFmpeg/ASS usa: AABBGGRR)
        # Simplificado para Amarelo padrão se der erro: &H00FFFF
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', f"subtitles='{sub_filter_path}':force_style='FontSize={font_settings['size']},Bold={int(font_settings['bold'])}'",
            '-c:a', 'copy', '-y', output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    def format_time(self, seconds):
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int(td.microseconds / 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"