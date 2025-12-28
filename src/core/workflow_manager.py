from pathlib import Path
from typing import Optional
import time

from src.core.file_matcher import match_videos_and_subtitles
from src.core.video_analyzer import VideoAnalyzer
from src.core.subtitle_generator import SubtitleGenerator
from src.core.subtitle_sync import SubtitleSynchronizer
from src.core.translator import SubtitleTranslator
from src.utils.config_manager import ConfigManager


class WorkflowManager:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.video_analyzer = VideoAnalyzer()
        self.subtitle_generator = SubtitleGenerator()
        self.subtitle_synchronizer = SubtitleSynchronizer(config=config)
        self.translator = SubtitleTranslator()

    def process_directory(
        self,
        directory: Path,
        target_language: Optional[str] = None,
        translate_existing: bool = False,
        progress_callback: Optional[callable] = None,
        preview_callback: Optional[callable] = None,
        ask_continue_callback: Optional[callable] = None,
        merge_with_video: bool = False,
        subtitle_format: Optional[dict] = None,
        stage_started_callback: Optional[callable] = None,
        stage_progress_callback: Optional[callable] = None,
        stage_completed_callback: Optional[callable] = None
    ):
        # Emitir estágio inicial
        if stage_started_callback:
            stage_started_callback("directory_analysis", None)
        
        if progress_callback:
            progress_callback(
                "🔍 Analisando diretório e procurando arquivos de vídeo...",
                0, 0, "directory_analysis"
            )
        
        pairs = match_videos_and_subtitles(directory)
        total = len(pairs)

        if total == 0:
            if progress_callback:
                progress_callback(
                    "⚠️ Nenhum arquivo de vídeo encontrado no diretório selecionado.",
                    0, 0, "directory_analysis"
                )
            return
        
        if stage_completed_callback:
            stage_completed_callback("directory_analysis")
        
        if progress_callback:
            progress_callback(
                f"✅ Encontrados {total} arquivo(s) de vídeo para processar.",
                0, total, "file_processing"
            )

        for index, pair in enumerate(pairs, start=1):
            video_path = pair["video"]
            subtitle_path = pair.get("subtitle")

            # Emitir estágio de processamento de arquivo
            if stage_started_callback:
                stage_started_callback("file_processing", str(video_path))
            
            if progress_callback:
                if subtitle_path:
                    progress_callback(
                        f"📄 Arquivo {index}/{total}: {video_path.name} (com legenda existente)",
                        index,
                        total,
                        "file_processing"
                    )
                else:
                    progress_callback(
                        f"📄 Arquivo {index}/{total}: {video_path.name} (sem legenda - será gerada)",
                        index,
                        total,
                        "file_processing"
                    )

            try:
                result = self._process_single_video(
                    video_path,
                    subtitle_path,
                    target_language,
                    translate_existing,
                    progress_callback,
                    preview_callback,
                    stage_started_callback,
                    stage_progress_callback,
                    stage_completed_callback,
                    merge_with_video,
                    subtitle_format
                )
                
                # Emitir conclusão do arquivo
                if stage_completed_callback:
                    stage_completed_callback("file_processing")
                
                # Pergunta se deseja continuar
                if ask_continue_callback:
                    if not ask_continue_callback(video_path.name):
                        if progress_callback:
                            progress_callback("Processamento cancelado pelo usuário.", index, total, "cancelled")
                        break
                        
            except Exception as e:
                if progress_callback:
                    import traceback
                    error_msg = f"Erro ao processar {video_path.name}:\n{str(e)}"
                    progress_callback(error_msg, index, total, "error")
                # Emitir falha no estágio
                if stage_completed_callback:
                    stage_completed_callback("file_processing")

    def _is_subtitle_file_empty(self, subtitle_path: Path) -> bool:
        """Verifica se o arquivo de legenda está vazio ou contém apenas espaços"""
        if not subtitle_path.exists():
            return True
        try:
            with open(subtitle_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return True
                parsed = self.subtitle_generator.parse_srt(content)
                return len(parsed) == 0
        except Exception:
            return True

    def _process_single_video(
        self,
        video_path: Path,
        subtitle_path: Optional[Path],
        target_language: Optional[str],
        translate_existing: bool,
        progress_callback: Optional[callable] = None,
        preview_callback: Optional[callable] = None,
        stage_started_callback: Optional[callable] = None,
        stage_progress_callback: Optional[callable] = None,
        stage_completed_callback: Optional[callable] = None,
        merge_with_video: bool = False,
        subtitle_format: Optional[dict] = None
    ):
        audio_language = self.video_analyzer.detect_language(video_path)
        
        # CASO 1: Não existe legenda ou está vazia
        if subtitle_path is None or self._is_subtitle_file_empty(subtitle_path):
            if stage_started_callback:
                stage_started_callback("transcription", str(video_path))
            
            if progress_callback:
                progress_callback(
                    f"🎤 Transcrevendo áudio de {video_path.name}...",
                    0, 0, "transcription"
                )
            
            # Transcrever áudio
            from src.core.transcription_engine import TranscriptionEngine
            
            gpu_info = {
                "available": self.config.get_runtime_value("gpu_available", False),
                "name": self.config.get_runtime_value("gpu_name"),
                "backend": self.config.get_runtime_value("gpu_backend")
            }
            
            # Transcrever com callback de preview
            def transcription_segment_callback(segment_start, segment_end, text):
                if preview_callback:
                    timestamp = f"{self._format_timestamp(segment_start)} --> {self._format_timestamp(segment_end)}"
                    preview_text = f"{timestamp}\n{text}\n\n"
                    preview_callback(preview_text)
            
            engine = TranscriptionEngine(gpu_info)
            _, segments = engine.transcribe(
                str(video_path),
                segment_callback=transcription_segment_callback if preview_callback else None
            )
            
            # Gerar legendas SRT
            subtitles_srt = self.subtitle_generator.generate_from_segments(segments)
            
            if stage_completed_callback:
                stage_completed_callback("transcription")
            
            # Traduzir se solicitado
            if translate_existing and target_language:
                if stage_started_callback:
                    stage_started_callback("translation", str(video_path))
                
                if progress_callback:
                    progress_callback(
                        f"🌍 Traduzindo legendas de {video_path.name} para {target_language}...",
                        0, 0, "translation"
                    )
                
                # Traduzir com callback de preview
                subtitles_srt = self._translate_with_preview(
                    subtitles_srt,
                    audio_language,
                    target_language,
                    preview_callback
                )
                
                if stage_completed_callback:
                    stage_completed_callback("translation")
            
            # Sincronizar legendas
            if stage_started_callback:
                stage_started_callback("synchronization", str(video_path))
            
            if progress_callback:
                progress_callback(
                    f"⏱️ Sincronizando legendas de {video_path.name}...",
                    0, 0, "synchronization"
                )
            
            # Sincronizar com callback de preview
            subtitles_srt = self._sync_with_preview(
                video_path,
                subtitles_srt,
                preview_callback
            )
            
            if stage_completed_callback:
                stage_completed_callback("synchronization")
        
        # CASO 2: Já existe legenda
        else:
            # Primeiro sincronizar
            if stage_started_callback:
                stage_started_callback("synchronization", str(video_path))
            
            if progress_callback:
                progress_callback(
                    f"⏱️ Sincronizando legenda existente de {video_path.name}...",
                    0, 0, "synchronization"
                )
            
            # Sincronizar com callback de preview
            subtitles_srt = self._sync_with_preview(
                video_path,
                subtitle_path,
                preview_callback
            )
            
            if stage_completed_callback:
                stage_completed_callback("synchronization")
            
            # Traduzir se solicitado
            if translate_existing and target_language:
                if stage_started_callback:
                    stage_started_callback("translation", str(video_path))
                
                if progress_callback:
                    progress_callback(
                        f"🌍 Traduzindo legenda existente de {video_path.name} para {target_language}...",
                        0, 0, "translation"
                    )
                
                # Traduzir com callback de preview
                subtitles_srt = self._translate_with_preview(
                    subtitles_srt,
                    audio_language,
                    target_language,
                    preview_callback
                )
                
                if stage_completed_callback:
                    stage_completed_callback("translation")
        
        # Aplicar formatação
        if subtitle_format:
            if stage_started_callback:
                stage_started_callback("formatting", str(video_path))
            
            if progress_callback:
                progress_callback(
                    f"🎨 Aplicando formatação às legendas de {video_path.name}...",
                    0, 0, "formatting"
                )
            
            subtitles_srt = self._apply_subtitle_format_properly(
                subtitles_srt,
                subtitle_format
            )
            
            if preview_callback:
                preview_callback(subtitles_srt)
            
            if stage_completed_callback:
                stage_completed_callback("formatting")
        
        # Salvar arquivo
        if stage_started_callback:
            stage_started_callback("saving", str(video_path))
        
        if progress_callback:
            progress_callback(
                f"💾 Salvando legendas de {video_path.name}...",
                0, 0, "saving"
            )
        
        output_path = self._resolve_output_path(
            video_path, 
            target_language if translate_existing else None,
            subtitle_format
        )
        self.subtitle_generator.save(subtitles_srt, output_path)
        
        if stage_completed_callback:
            stage_completed_callback("saving")
        
        if progress_callback:
            progress_callback(
                f"✅ Legendas salvas: {output_path.name}",
                0, 0, "completed"
            )
        
        # Mesclar com vídeo se solicitado
        if merge_with_video:
            if stage_started_callback:
                stage_started_callback("merging", str(video_path))
            
            if progress_callback:
                progress_callback(
                    f"🎥 Mesclando legenda ao vídeo {video_path.name}...",
                    0, 0, "merging"
                )
            
            merged_path = self._merge_subtitle_with_video(
                video_path, 
                output_path, 
                subtitle_format
            )
            
            if stage_completed_callback:
                stage_completed_callback("merging")
            
            if progress_callback:
                progress_callback(
                    f"✅ Vídeo com legenda mesclada salvo: {merged_path.name}",
                    0, 0, "completed"
                )
        
        return output_path

    def _translate_with_preview(self, subtitles_srt, source_lang, target_lang, preview_callback):
        """Traduz legendas com preview em tempo real"""
        # Parse SRT
        subtitles = self.subtitle_generator.parse_srt(subtitles_srt)
        
        # Traduzir cada legenda
        translated_subtitles = []
        for i, sub in enumerate(subtitles):
            start_time, end_time, text = sub
            
            # Traduzir texto
            translated_text = self.translator.translate_text(
                text, 
                source_lang, 
                target_lang
            )
            
            translated_subtitles.append((start_time, end_time, translated_text))
            
            # Emitir preview
            if preview_callback:
                timestamp = f"{self._format_timestamp(start_time)} --> {self._format_timestamp(end_time)}"
                preview_text = f"{timestamp}\n{translated_text}\n\n"
                preview_callback(preview_text)
        
        # Gerar SRT traduzido
        return self.subtitle_generator.generate_srt(translated_subtitles)

    def _sync_with_preview(self, video_path, subtitle_input, preview_callback):
        """Sincroniza legendas com preview em tempo real"""
        if isinstance(subtitle_input, Path):
            # Se for um Path, carrega o arquivo
            with open(subtitle_input, 'r', encoding='utf-8') as f:
                subtitles_srt = f.read()
        else:
            # Se for string SRT
            subtitles_srt = subtitle_input
        
        # Sincronizar
        synced_srt = self.subtitle_synchronizer.synchronize(
            video_path,
            subtitle_input if isinstance(subtitle_input, Path) else None
        )
        
        # Emitir preview
        if preview_callback:
            preview_callback(synced_srt)
        
        return synced_srt

    def _apply_subtitle_format_properly(self, srt_content: str, format_options: dict) -> str:
        """Aplica formatação às legendas (converte para ASS se necessário)"""
        size = format_options.get("size", 20)
        color = format_options.get("color", "#FFFFFF")
        bold = format_options.get("bold", False)
        
        # Verifica se precisa de formatação visual
        needs_visual_format = (size != 20 or color != "#FFFFFF" or bold)
        
        if not needs_visual_format:
            return srt_content  # Mantém SRT
        
        # Parse SRT
        subtitles = self.subtitle_generator.parse_srt(srt_content)
        
        # Converte cor hex para formato ASS (BGR)
        color_hex = color.lstrip('#')
        ass_color = "&HFFFFFF&"  # Default branco
        if len(color_hex) == 6:
            r, g, b = color_hex[0:2], color_hex[2:4], color_hex[4:6]
            ass_color = f"&H{b}{g}{r}&"  # Formato BGR
        
        # Cria conteúdo ASS formatado
        ass_content = f"""[Script Info]
Title: Legenda formatada
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{size},{ass_color},&H000000FF,&H00000000,&H00000000,{1 if bold else 0},0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # Adiciona cada evento
        for start_time, end_time, text in subtitles:
            start_ass = self._convert_time_to_ass(start_time)
            end_ass = self._convert_time_to_ass(end_time)
            ass_content += f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}\n"
        
        return ass_content

    def _format_timestamp(self, seconds: float) -> str:
        """Formata segundos para timestamp SRT (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _convert_time_to_ass(self, seconds: float) -> str:
        """Converte segundos para formato ASS (H:MM:SS.cc)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds - int(seconds)) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    def _resolve_output_path(self, video_path: Path, language: Optional[str], format_dict: Optional[dict] = None) -> Path:
        # Determina extensão baseada na formatação
        extension = ".srt"
        if format_dict:
            size = format_dict.get("size", 20)
            color = format_dict.get("color", "#FFFFFF")
            bold = format_dict.get("bold", False)
            
            # Se tem formatação visual, usa ASS
            if size != 20 or color != "#FFFFFF" or bold:
                extension = ".ass"
        
        base_name = video_path.stem
        
        if language:
            base_name = f"{base_name}.{language}"
        
        # Suporta tanto 'output_mode' quanto 'save_mode' para compatibilidade
        mode = self.config.get("output_mode") or self.config.get("save_mode", "overwrite")
        
        if mode == "overwrite":
            return video_path.with_suffix(extension)
        
        if mode == "alternate_name":
            return video_path.with_name(f"{base_name}{extension}")
        
        if mode == "output_folder":
            output_dir = Path(self.config.get("output_directory"))
            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir / f"{base_name}{extension}"
        
        return video_path.with_suffix(extension)
    
    def _merge_subtitle_with_video(self, video_path: Path, subtitle_path: Path, 
                                   subtitle_format: Optional[dict] = None) -> Path:
        """Mescla a legenda diretamente no vídeo usando ffmpeg"""
        import subprocess
        import sys
        
        output_path = video_path.with_name(f"{video_path.stem}_com_legenda{video_path.suffix}")
        
        # Verifica se a legenda é ASS ou SRT
        is_ass = subtitle_path.suffix.lower() == '.ass'
        
        if is_ass:
            # Para ASS, usa o filtro subtitles normalmente
            subtitle_filter = f"subtitles='{subtitle_path}'"
        else:
            # Para SRT, converte para ASS temporariamente com formatação
            temp_ass_path = video_path.with_name(f"{video_path.stem}_temp.ass")
            
            # Lê o conteúdo SRT
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            # Aplica formatação (se fornecida) ou usa padrão
            if subtitle_format:
                formatted_content = self._apply_subtitle_format_properly(srt_content, subtitle_format)
            else:
                # Formatação padrão para SRT
                formatted_content = self._apply_subtitle_format_properly(srt_content, {
                    "size": 20,
                    "color": "#FFFFFF",
                    "bold": False
                })
            
            # Salva arquivo ASS temporário
            with open(temp_ass_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            subtitle_filter = f"subtitles='{temp_ass_path}'"
        
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vf", subtitle_filter,
            "-c:v", "libx264",
            "-c:a", "copy",
            "-y",
            str(output_path)
        ]
        
        try:
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            # Limpa arquivo temporário se existir
            if not is_ass and 'temp_ass_path' in locals():
                temp_ass_path.unlink(missing_ok=True)
            return output_path
        except subprocess.CalledProcessError as e:
            # Limpa arquivo temporário em caso de erro
            if not is_ass and 'temp_ass_path' in locals():
                temp_ass_path.unlink(missing_ok=True)
            raise Exception(f"Erro ao mesclar legenda ao vídeo: {e}")