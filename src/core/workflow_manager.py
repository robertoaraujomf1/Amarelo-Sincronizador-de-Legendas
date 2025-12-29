from __future__ import annotations  # Para forward references

import os
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
import subprocess

from .file_matcher import FileMatcher
from .video_analyzer import VideoAnalyzer
from .transcription_engine import TranscriptionEngine
from .translator import Translator  # Agora deve importar corretamente
from .subtitle_generator import SubtitleGenerator
from .subtitle_sync import SubtitleSynchronizer
from .gpu_detector import GPUDetector
from .file_locker import FileLocker

logger = logging.getLogger(__name__)

@dataclass
class WorkflowState:
    """Estado do fluxo de trabalho"""
    current_step: str = ""
    progress: int = 0
    total_steps: int = 0
    current_file: str = ""
    status_message: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    preview_subtitles: List[Dict] = field(default_factory=list)  # Legendas para pré-visualização

class WorkflowManager:
    """Gerencia o fluxo completo de processamento de legendas"""
    
    def __init__(self, config):
        self.config = config
        self.state = WorkflowState()
        self.file_locker = FileLocker()
        
        # Inicializar componentes
        self.file_matcher = FileMatcher()
        self.video_analyzer = VideoAnalyzer()
        self.transcription_engine = TranscriptionEngine(config)
        self.translator = Translator(config)
        self.subtitle_generator = SubtitleGenerator(config)
        self.subtitle_sync = SubtitleSynchronizer()
        self.gpu_detector = GPUDetector()
        
        # Callback para pré-visualização
        self.preview_callback = None
        
    def set_preview_callback(self, callback):
        """Define callback para atualizar pré-visualização"""
        self.preview_callback = callback
    
    def _update_preview(self, subtitles: List[Dict], stage: str):
        """Atualiza pré-visualização das legendas"""
        if self.preview_callback:
            self.preview_callback(subtitles, stage)
        self.state.preview_subtitles = subtitles
    
    def process_files(self, video_paths: List[str], subtitle_paths: Optional[List[str]] = None, 
                     translate: bool = False, merge_files: bool = False) -> Dict[str, Any]:
        """
        Processa arquivos de vídeo e legendas
        
        Args:
            video_paths: Lista de caminhos de vídeo
            subtitle_paths: Lista opcional de caminhos de legendas
            translate: Se deve traduzir legendas/transcrição
            merge_files: Se deve mesclar legenda no vídeo
            
        Returns:
            Dicionário com resultados do processamento
        """
        try:
            results = {}
            
            # Validar entradas
            valid_videos = self._validate_videos(video_paths)
            valid_subtitles = self._validate_subtitles(subtitle_paths) if subtitle_paths else []
            
            if not valid_videos:
                raise ValueError("Nenhum arquivo de vídeo válido encontrado")
            
            # Emparelhar arquivos
            matched_pairs = self.file_matcher.match_files(valid_videos, valid_subtitles)
            
            # Processar cada par
            for i, (video_path, subtitle_path) in enumerate(matched_pairs):
                self.state.current_file = os.path.basename(video_path)
                
                try:
                    # Bloquear arquivo para processamento
                    if not self.file_locker.lock_file(video_path):
                        logger.warning(f"Arquivo {video_path} já está em processamento")
                        continue
                    
                    # Analisar vídeo
                    self.state.status_message = f"Analisando vídeo: {os.path.basename(video_path)}"
                    video_info = self.video_analyzer.analyze(video_path)
                    
                    # CASO 1: Existe arquivo de legenda
                    if subtitle_path:
                        self.state.status_message = "Carregando legenda existente..."
                        
                        # Carregar legenda do arquivo
                        subtitles = self.subtitle_sync.load_subtitles(subtitle_path)
                        self._update_preview(subtitles, "Legenda original carregada")
                        
                        # Se usuário quer traduzir
                        if translate:
                            self.state.status_message = "Traduzindo legenda..."
                            
                            # Detectar idioma original
                            source_lang = self._detect_subtitle_language(subtitles)
                            target_lang = self.config.get('translation', {}).get('target_language', 'pt')
                            
                            # Traduzir
                            translated_subtitles = self.translator.translate_subtitles(
                                subtitles, source_lang, target_lang
                            )
                            self._update_preview(translated_subtitles, "Legenda traduzida")
                            
                            # Sincronizar após tradução
                            self.state.status_message = "Sincronizando legenda traduzida..."
                            synced_subtitles = self.subtitle_sync.sync_subtitles(
                                translated_subtitles, video_info
                            )
                            subtitles = synced_subtitles
                        else:
                            # Apenas sincronizar
                            self.state.status_message = "Sincronizando legenda..."
                            synced_subtitles = self.subtitle_sync.sync_subtitles(
                                subtitles, video_info
                            )
                            subtitles = synced_subtitles
                        
                        self._update_preview(subtitles, "Legenda sincronizada")
                    
                    # CASO 2: Não existe arquivo de legenda
                    else:
                        self.state.status_message = "Transcrevendo áudio do vídeo..."
                        
                        # Transcrever áudio
                        transcription = self.transcription_engine.transcribe(video_path, video_info)
                        
                        # Converter transcrição para formato de legenda
                        subtitles = self._transcription_to_subtitles(transcription)
                        self._update_preview(subtitles, "Transcrição concluída")
                        
                        # Se usuário quer traduzir
                        if translate:
                            self.state.status_message = "Traduzindo transcrição..."
                            
                            source_lang = transcription.get('language', 'en')
                            target_lang = self.config.get('translation', {}).get('target_language', 'pt')
                            
                            translated_subtitles = self.translator.translate_subtitles(
                                subtitles, source_lang, target_lang
                            )
                            subtitles = translated_subtitles
                            self._update_preview(subtitles, "Tradução concluída")
                        
                        # Sincronizar
                        self.state.status_message = "Sincronizando legendas geradas..."
                        synced_subtitles = self.subtitle_sync.sync_subtitles(
                            subtitles, video_info
                        )
                        subtitles = synced_subtitles
                        self._update_preview(subtitles, "Legendas sincronizadas")
                    
                    # Gerar arquivos de legenda
                    self.state.status_message = "Gerando arquivos de legenda..."
                    
                    # Aplicar formatação configurada
                    font_config = self.config.get('font', {})
                    formatted_subtitles = self.subtitle_generator.apply_formatting(
                        subtitles, font_config
                    )
                    
                    # Gerar arquivos
                    subtitle_files = self.subtitle_generator.generate_subtitle_files(
                        formatted_subtitles, video_path
                    )
                    
                    # Se usuário quer mesclar arquivos
                    if merge_files:
                        self.state.status_message = "Mesclando legenda com vídeo..."
                        
                        for format_name, subtitle_path in subtitle_files.items():
                            if format_name in ['srt', 'ass']:  # Apenas formatos suportados
                                merged_path = self._merge_video_subtitle(
                                    video_path, subtitle_path, format_name
                                )
                                subtitle_files[f'merged_{format_name}'] = merged_path
                    
                    results[video_path] = {
                        'status': 'completed',
                        'subtitle_files': subtitle_files,
                        'subtitles': formatted_subtitles,
                        'video_info': video_info
                    }
                    
                    # Desbloquear arquivo
                    self.file_locker.unlock_file(video_path)
                    
                except Exception as e:
                    logger.error(f"Erro ao processar {video_path}: {str(e)}")
                    self.state.errors.append(f"{os.path.basename(video_path)}: {str(e)}")
                    self.file_locker.unlock_file(video_path)
            
            return {
                'success': len(self.state.errors) == 0,
                'results': results,
                'errors': self.state.errors,
                'warnings': self.state.warnings
            }
            
        except Exception as e:
            logger.error(f"Erro no fluxo de trabalho: {str(e)}")
            raise
    
    def _validate_videos(self, video_paths: List[str]) -> List[str]:
        """Valida arquivos de vídeo"""
        valid_videos = []
        for path in video_paths:
            if os.path.exists(path) and path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv')):
                valid_videos.append(path)
            else:
                self.state.warnings.append(f"Arquivo inválido ou não suportado: {path}")
        return valid_videos
    
    def _validate_subtitles(self, subtitle_paths: List[str]) -> List[str]:
        """Valida arquivos de legenda"""
        valid_subtitles = []
        for path in subtitle_paths:
            if os.path.exists(path) and path.lower().endswith(('.srt', '.ass', '.ssa', '.vtt', '.sub')):
                valid_subtitles.append(path)
            else:
                self.state.warnings.append(f"Arquivo de legenda inválido: {path}")
        return valid_subtitles
    
    def _transcription_to_subtitles(self, transcription: Dict) -> List[Dict]:
        """Converte resultado de transcrição para formato de legenda"""
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
    
    def _detect_subtitle_language(self, subtitles: List[Dict]) -> str:
        """Detecta idioma das legendas"""
        if not subtitles:
            return 'en'
            
        # Extrair texto das primeiras legendas
        texts = []
        for sub in subtitles[:10]:
            text = sub.get('text', '')
            if text.strip():
                texts.append(text)
        
        if not texts:
            return 'en'
            
        combined_text = ' '.join(texts)
        
        # Usar tradutor para detectar idioma
        try:
            detected_lang = self.translator.detect_language(combined_text)
            return detected_lang
        except Exception as e:
            logger.warning(f"Erro ao detectar idioma: {e}")
            return 'en'  # Default para inglês
    
    def _merge_video_subtitle(self, video_path: str, subtitle_path: str, format_name: str) -> str:
        """Mescla legenda com vídeo usando ffmpeg"""
        base_name = os.path.splitext(video_path)[0]
        output_path = f"{base_name}_with_subs.mp4"
        
        # Determinar filtro baseado no formato
        if format_name in ['ass', 'ssa']:
            filter_complex = f"ass='{subtitle_path}'"
        else:  # srt
            filter_complex = f"subtitles='{subtitle_path}'"
        
        # Comando ffmpeg para mesclar
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', filter_complex,
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-y',
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
            logger.info(f"Vídeo mesclado com sucesso: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao mesclar vídeo: {e.stderr}")
            raise Exception(f"Falha ao mesclar vídeo: {e.stderr}")
    
    def cancel(self):
        """Cancela o processamento em andamento"""
        logger.info("Processamento cancelado pelo usuário")
        self.state.status_message = "Processamento cancelado"