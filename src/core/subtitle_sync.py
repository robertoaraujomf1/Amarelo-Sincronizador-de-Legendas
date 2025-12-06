# src/core/subtitle_sync.py
import os
import json
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
import re
from pathlib import Path

from .video_analyzer import VideoAnalyzer
from .file_matcher import FileMatcher
from .file_locker import FileLocker
from .subtitle_editor import SubtitleEditor
from .audio_transcriber import AudioTranscriber
from .subtitle_generator import SubtitleGenerator
from .translator import SubtitleTranslator


class SubtitleSyncEngine:
    def __init__(self):
        self.video_analyzer = VideoAnalyzer()
        self.file_matcher = FileMatcher()
        self.file_locker = FileLocker()
        self.subtitle_editor = SubtitleEditor()
        self.audio_transcriber = AudioTranscriber()
        self.subtitle_generator = SubtitleGenerator()
        self.translator = SubtitleTranslator()
        
    def find_video_subtitle_pairs(self, directory: str) -> List[Tuple[str, str | None]]:
        """Encontra pares de vídeo e legenda usando FileMatcher."""
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.m4v', '.webm', '.3gp']
        subtitle_extensions = ['.srt', '.ass', '.ssa', '.vtt', '.sub', '.txt']
        
        all_files = list(Path(directory).rglob('*'))
        
        videos = [str(p) for p in all_files if p.suffix.lower() in video_extensions]
        subtitles = {str(p) for p in all_files if p.suffix.lower() in subtitle_extensions}
        
        pairs = []
        for video_path in videos:
            base_name = Path(video_path).stem
            found_sub = next((s for s in subtitles if Path(s).stem == base_name), None)
            pairs.append((video_path, found_sub))
            if found_sub:
                subtitles.remove(found_sub)
                
        return pairs
    
    def analyze_and_sync(self, video_path: str, subtitle_path: Optional[str], 
                        settings: Dict[str, Any]) -> bool:
        """
        Analisa e sincroniza legendas.
        
        Args:
            video_path: Caminho do arquivo de vídeo
            subtitle_path: Caminho do arquivo de legenda (None se não existir)
            settings: Configurações de legenda
            
        Returns:
            bool: True se bem sucedido, False caso contrário
        """
        try:
            print(f"\n{'='*60}")
            print(f"🎬 Processando: {os.path.basename(video_path)}")
            print(f"📄 Legenda: {os.path.basename(subtitle_path) if subtitle_path else 'Nenhuma (será gerada)'}")
            
            # 1. Analisar vídeo para obter metadados
            print("📊 1. Analisando vídeo...")
            video_info = self.video_analyzer.analyze(video_path)
            if not video_info:
                print("❌ Erro: Não foi possível analisar o vídeo.")
                return False
            
            print(f"   ✅ Duração: {video_info.get('duration', 0):.2f}s, Resolução: {video_info.get('width', 0)}x{video_info.get('height', 0)}")
            
            # 2. Se houver legenda, verificar sincronização
            if subtitle_path and os.path.exists(subtitle_path):
                print("🔍 2. Verificando legenda existente...")
                
                # Ler legenda existente
                subtitle_content = self.subtitle_editor.read_subtitle(subtitle_path)
                if not subtitle_content:
                    print("⚠️ Não foi possível ler a legenda, gerando uma nova...")
                    return self._generate_new_subtitle(video_path, video_info, settings)
                
                # Verificar se precisa de sincronização
                needs_sync = self._needs_synchronization(subtitle_content, video_info)
                
                if needs_sync:
                    print("⚙️ 3. Sincronizando legenda...")
                    # Sincronizar legenda
                    synced_content = self._synchronize_subtitle(subtitle_content, video_info)
                    
                    # Salvar legenda sincronizada
                    output_path = self._get_output_path(video_path, subtitle_path, settings)
                    print(f"💾 Salvando legenda sincronizada em: {output_path}")
                    success = self.subtitle_editor.save_subtitle(synced_content, output_path, settings)
                    
                    if success:
                        print("✅ Legenda sincronizada salva com sucesso!")
                        return True
                    else:
                        print("❌ Erro ao salvar legenda sincronizada.")
                        return False
                else:
                    print("✅ 3. Legenda já está sincronizada.")
                    return True
                
            else:
                # 3. Se não houver legenda, transcrever áudio e gerar legenda
                print("🎤 2. Nenhuma legenda encontrada. Gerando nova...")
                return self._generate_new_subtitle(video_path, video_info, settings)
                    
        except Exception as e:
            print(f"❌ Erro crítico em analyze_and_sync: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_new_subtitle(self, video_path: str, video_info: Dict, settings: Dict) -> bool:
        """Gera uma nova legenda a partir do áudio do vídeo."""
        target_language = settings.get('target_language', 'pt-BR')
        
        print("🎤 3. Transcrevendo áudio...")
        transcription = self.audio_transcriber.transcribe(video_path)
        if not transcription or not transcription.get('segments'):
            print("❌ Erro: Não foi possível transcrever o áudio.")
            return False
        
        print(f"   ✅ Transcrição concluída: {len(transcription['segments'])} segmentos.")
        
        detected_language = transcription.get('language', 'pt-BR')
        print(f"   🌐 Idioma detectado: {detected_language}")
        
        if detected_language.split('-')[0] != target_language.split('-')[0]:
            print(f"🌍 4. Traduzindo de {detected_language} para {target_language}...")
            transcription = self.translator.translate_transcription(transcription, target_language)
            if not transcription:
                print("   ⚠️ Falha na tradução. Usando texto original.")
        
        print("📝 5. Gerando conteúdo da legenda...")
        subtitle_content = self.subtitle_generator.generate(transcription, video_info, settings)
        if not subtitle_content or not subtitle_content.get('segments'):
            print("❌ Erro ao gerar conteúdo da legenda.")
            return False
            
        output_path = self._get_output_path(video_path, None, settings)
        print(f"💾 6. Salvando legenda em: {output_path}")
        success = self.subtitle_editor.save_subtitle(subtitle_content, output_path, settings)
        
        if success:
            print("✅ Legenda gerada salva com sucesso!")
        else:
            print("❌ Erro ao salvar legenda gerada.")
            
        return success

    def _needs_synchronization(self, subtitle_content: Dict, video_info: Dict) -> bool:
        """
        Verifica se a legenda precisa de sincronização.
        """
        try:
            # Verificar se a legenda cobre toda a duração do vídeo
            video_duration = video_info.get('duration', 0)
            
            if not subtitle_content.get('segments'):
                print("   ⚠️ Legenda vazia, precisa gerar do zero.")
                return True
            
            segments = subtitle_content['segments']
            first_start = self._time_to_seconds(segments[0]['start'])
            last_end = self._time_to_seconds(segments[-1]['end'])
            subtitle_duration = last_end - first_start
            
            duration_ratio = subtitle_duration / video_duration if video_duration > 0 else 0
            
            print(f"   📊 Análise de sinc: Duração Legenda={subtitle_duration:.2f}s, Duração Vídeo={video_duration:.2f}s, Proporção={duration_ratio:.2f}")

            # Se a duração da legenda for muito diferente da duração do vídeo (ex: mais de 5% de diferença)
            if not (0.95 < duration_ratio < 1.05):
                print(f"   ⚠️ Duração da legenda ({subtitle_duration:.2f}s) é muito diferente da do vídeo ({video_duration:.2f}s).")
                return True
            
            # Se o final da legenda está muito longe do final do vídeo
            if abs(video_duration - last_end) > max(10, video_duration * 0.05): # 10s ou 5%
                print(f"   ⚠️ Final da legenda ({last_end:.2f}s) está desalinhado com o final do vídeo ({video_duration:.2f}s).")
                return True

            print("   ✅ Legenda parece estar bem sincronizada.")
            return False
            
        except Exception as e:
            print(f"   ❌ Erro em _needs_synchronization: {str(e)}")
            return True
    
    def _synchronize_subtitle(self, subtitle_content: Dict, video_info: Dict) -> Dict:
        """
        Sincroniza legenda com base na análise do vídeo.
        """
        try:
            video_duration = video_info.get('duration', 0)
            segments = subtitle_content.get('segments', [])
            
            if not segments or video_duration <= 0:
                print("   ⚠️ Impossível sincronizar: sem segmentos ou duração de vídeo.")
                return subtitle_content
            
            # Encontrar duração total da legenda atual
            first_start = self._time_to_seconds(segments[0]['start'])
            last_end = self._time_to_seconds(segments[-1]['end'])
            subtitle_duration = last_end - first_start
            
            if subtitle_duration <= 0:
                print("   ⚠️ Duração da legenda é zero ou negativa. Não é possível sincronizar.")
                return subtitle_content
            
            # Calcular fator de ajuste
            # Ajusta a duração da legenda para corresponder à duração do vídeo, menos o tempo inicial.
            target_duration = video_duration - first_start
            adjustment_factor = target_duration / subtitle_duration if subtitle_duration > 0 else 1
            
            print(f"   📐 Fator de ajuste: {adjustment_factor:.4f} (Duração alvo: {target_duration:.2f}s)")

            # Ajustar todos os tempos
            new_segments = []
            for segment in segments:
                start_seconds = self._time_to_seconds(segment['start'])
                end_seconds = self._time_to_seconds(segment['end'])
                
                # Nova lógica: desloca, escala e desloca de volta
                new_start = ((start_seconds - first_start) * adjustment_factor) + first_start
                new_end = ((end_seconds - first_start) * adjustment_factor) + first_start
                
                segment['start'] = self._seconds_to_time(max(0, new_start))
                segment['end'] = self._seconds_to_time(max(0, new_end))
                new_segments.append(segment)
            
            subtitle_content['segments'] = new_segments
            return subtitle_content
            
        except Exception as e:
            print(f"   ❌ Erro em _synchronize_subtitle: {str(e)}")
            return subtitle_content
    
    def _get_output_path(self, video_path: str, subtitle_path: Optional[str], 
                        settings: Dict[str, Any]) -> str:
        """
        Determina o caminho de saída para a legenda.
        """
        output_mode = settings.get('output_mode', 'same_folder')  # 'same_folder' ou 'output_folder'
        
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        if output_mode == 'output_folder':
            # Usar pasta de saída configurada
            output_dir = settings.get('output_folder', 'output')
            if not os.path.isabs(output_dir):
                # Relativo ao diretório do projeto
                project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                output_dir = os.path.join(project_dir, output_dir)
            
            # Criar pasta se não existir
            os.makedirs(output_dir, exist_ok=True)
        else:
            # Mesma pasta do vídeo
            output_dir = video_dir
        
        # Determinar extensão e sufixo
        suffix = settings.get('output_suffix', '_synced')
        if subtitle_path and os.path.exists(subtitle_path):
            ext = os.path.splitext(subtitle_path)[1]
            if ext.lower() not in ['.srt', '.vtt', '.ass']:
                ext = '.srt'
        else:
            ext = '.srt'  # Padrão
        
        # Evitar sobrescrever o original se estiver na mesma pasta
        output_filename = f"{video_name}{suffix}{ext}"
        output_path = os.path.join(output_dir, output_filename)

        # Se o arquivo de destino já existe, adiciona um número
        counter = 1
        while os.path.exists(output_path):
            output_filename = f"{video_name}{suffix}_{counter}{ext}"
            output_path = os.path.join(output_dir, output_filename)
            counter += 1
            
        return output_path
    
    def _time_to_seconds(self, time_str: str) -> float:
        """Converte string de tempo (HH:MM:SS,ms) para segundos."""
        try:
            if ',' in time_str:
                time_str, milliseconds = time_str.split(',')
                milliseconds = float('0.' + milliseconds)
            elif '.' in time_str:
                parts = time_str.split('.')
                time_str = parts[0]
                milliseconds = float('0.' + parts[1])
            else:
                milliseconds = 0
            
            parts = time_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = parts
                total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + milliseconds
            elif len(parts) == 2:
                minutes, seconds = parts
                total_seconds = int(minutes) * 60 + int(seconds) + milliseconds
            else:
                total_seconds = float(time_str) + milliseconds
            return total_seconds
        except Exception as e:
            print(f"⚠️ Erro ao converter tempo '{time_str}': {e}")
            return 0.0
    
    def _seconds_to_time(self, seconds: float) -> str:
        """Converte segundos para string de tempo (HH:MM:SS,ms)."""
        td = timedelta(seconds=max(0, seconds))
        dt = datetime(1, 1, 1) + td
        return f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d},{dt.microsecond // 1000:03d}"