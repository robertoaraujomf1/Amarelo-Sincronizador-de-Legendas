from pathlib import Path
from typing import Optional

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
        subtitle_format: Optional[dict] = None
    ):
        if progress_callback:
            progress_callback(
                "🔍 Analisando diretório e procurando arquivos de vídeo...",
                0, 0
            )
        
        pairs = match_videos_and_subtitles(directory)
        total = len(pairs)

        if total == 0:
            if progress_callback:
                progress_callback(
                    "⚠️ Nenhum arquivo de vídeo encontrado no diretório selecionado.",
                    0, 0
                )
            return
        
        if progress_callback:
            progress_callback(
                f"✅ Encontrados {total} arquivo(s) de vídeo para processar.",
                0, total
            )

        for index, pair in enumerate(pairs, start=1):
            video_path = pair["video"]
            subtitle_path = pair.get("subtitle")

            if progress_callback:
                if subtitle_path:
                    progress_callback(
                        f"📄 Arquivo {index}/{total}: {video_path.name} (com legenda existente)",
                        index,
                        total
                    )
                else:
                    progress_callback(
                        f"📄 Arquivo {index}/{total}: {video_path.name} (sem legenda - será gerada)",
                        index,
                        total
                    )

            try:
                result = self._process_single_video(
                    video_path,
                    subtitle_path,
                    target_language,
                    translate_existing,
                    progress_callback,
                    preview_callback,
                    merge_with_video,
                    subtitle_format
                )
                
                # Pergunta se deseja continuar (a menos que apply_to_all seja True)
                # Nota: apply_to_all é passado via Worker, não via WorkflowManager
                if ask_continue_callback:
                    if not ask_continue_callback(video_path.name):
                        if progress_callback:
                            progress_callback("Processamento cancelado pelo usuário.", index, total)
                        break
                        
            except Exception as e:
                if progress_callback:
                    import traceback
                    error_msg = f"Erro ao processar {video_path.name}:\n{str(e)}"
                    progress_callback(error_msg, index, total)

    def _is_subtitle_file_empty(self, subtitle_path: Path) -> bool:
        """Verifica se o arquivo de legenda está vazio ou contém apenas espaços"""
        if not subtitle_path.exists():
            return True
        try:
            with open(subtitle_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                # Verifica se está vazio ou se o parse não retorna legendas
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
        merge_with_video: bool = False,
        subtitle_format: Optional[dict] = None
    ):
        audio_language = self.video_analyzer.detect_language(video_path)

        # Se não há arquivo de legenda OU se o arquivo existe mas está vazio, gera novas legendas
        if subtitle_path is None or self._is_subtitle_file_empty(subtitle_path):
            if progress_callback:
                progress_callback(
                    f"Gerando legendas para {video_path.name}...",
                    0, 0
                )
            
            # Gera novas legendas
            from src.core.transcription_engine import TranscriptionEngine
            
            gpu_info = {
                "available": self.config.get_runtime_value("gpu_available", False),
                "name": self.config.get_runtime_value("gpu_name"),
                "backend": self.config.get_runtime_value("gpu_backend")
            }
            
            if progress_callback:
                progress_callback(
                    f"Transcrevendo áudio de {video_path.name}...",
                    0, 0
                )
            
            engine = TranscriptionEngine(gpu_info)
            _, segments = engine.transcribe(str(video_path))
            
            subtitles_srt = self.subtitle_generator.generate_from_segments(segments)

            if target_language and target_language != audio_language:
                if progress_callback:
                    progress_callback(
                        f"Traduzindo legendas de {video_path.name} para {target_language}...",
                        0, 0
                    )
                subtitles_srt = self.translator.translate(
                    subtitles_srt,
                    audio_language,
                    target_language
                )
            
            # Aplica formatação se especificada
            if subtitle_format:
                subtitles_srt = self._apply_subtitle_format(subtitles_srt, subtitle_format)
            
            # Atualiza pré-visualização
            if preview_callback:
                preview_callback(subtitles_srt)

            output_path = self._resolve_output_path(video_path, target_language)
            self.subtitle_generator.save(subtitles_srt, output_path)
            
            if progress_callback:
                progress_callback(
                    f"Legendas salvas: {output_path.name}",
                    0, 0
                )
            
            # Mescla com vídeo se solicitado
            if merge_with_video:
                if progress_callback:
                    progress_callback(
                        f"Mesclando legenda ao vídeo {video_path.name}...",
                        0, 0
                    )
                merged_path = self._merge_subtitle_with_video(video_path, output_path, subtitle_format)
                if progress_callback:
                    progress_callback(
                        f"Vídeo com legenda mesclada salvo: {merged_path.name}",
                        0, 0
                    )
            
            return output_path

        # Sincroniza legendas existentes
        if progress_callback:
            progress_callback(
                f"Sincronizando legendas de {video_path.name}...",
                0, 0
            )
        
        synced_subtitles = self.subtitle_synchronizer.synchronize(
            video_path,
            subtitle_path
        )

        if translate_existing and target_language:
            if progress_callback:
                progress_callback(
                    f"Traduzindo legendas de {video_path.name} para {target_language}...",
                    0, 0
                )
            synced_subtitles = self.translator.translate(
                synced_subtitles,
                audio_language,
                target_language
            )

        # Aplica formatação se especificada
        if subtitle_format:
            synced_subtitles = self._apply_subtitle_format(synced_subtitles, subtitle_format)
        
        # Atualiza pré-visualização
        if preview_callback:
            preview_callback(synced_subtitles)
        
        output_path = self._resolve_output_path(video_path, target_language)
        self.subtitle_generator.save(synced_subtitles, output_path)
        
        if progress_callback:
            progress_callback(
                f"Legendas salvas: {output_path.name}",
                0, 0
            )
        
        # Mescla com vídeo se solicitado
        if merge_with_video:
            if progress_callback:
                progress_callback(
                    f"Mesclando legenda ao vídeo {video_path.name}...",
                    0, 0
                )
            merged_path = self._merge_subtitle_with_video(video_path, output_path, subtitle_format)
            if progress_callback:
                progress_callback(
                    f"Vídeo com legenda mesclada salvo: {merged_path.name}",
                    0, 0
                )
        
        return output_path

    def _resolve_output_path(self, video_path: Path, language: Optional[str]) -> Path:
        # Suporta tanto 'output_mode' quanto 'save_mode' para compatibilidade
        mode = self.config.get("output_mode") or self.config.get("save_mode", "overwrite")
        base_name = video_path.stem
        extension = ".srt"

        if language:
            base_name = f"{base_name}.{language}"

        if mode == "overwrite":
            return video_path.with_suffix(extension)

        if mode == "alternate_name":
            return video_path.with_name(f"{base_name}{extension}")

        if mode == "output_folder":
            output_dir = Path(self.config.get("output_directory"))
            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir / f"{base_name}{extension}"

        return video_path.with_suffix(extension)
    
    def _apply_subtitle_format(self, srt_content: str, format_options: dict) -> str:
        """Aplica formatação às legendas (tamanho, cor, negrito)"""
        # Para SRT simples, não podemos aplicar formatação visual diretamente
        # Mas podemos criar um ASS/SSA com formatação ou retornar o SRT original
        # Por enquanto, retorna o SRT original (formatação visual requer ASS/SSA)
        return srt_content
    
    def _merge_subtitle_with_video(self, video_path: Path, subtitle_path: Path, 
                                   subtitle_format: Optional[dict] = None) -> Path:
        """Mescla a legenda diretamente no vídeo usando ffmpeg"""
        import subprocess
        import sys
        
        output_path = video_path.with_name(f"{video_path.stem}_com_legenda{video_path.suffix}")
        
        # Cria filtro de legenda com formatação
        subtitle_filter = f"subtitles='{subtitle_path}'"
        
        if subtitle_format:
            size = subtitle_format.get("size", 20)
            color = subtitle_format.get("color", "#FFFFFF")
            bold = subtitle_format.get("bold", False)
            
            # Converte cor hex para formato de legenda
            # ffmpeg usa formato: force_style='FontSize=20,PrimaryColour=&HFFFFFF&'
            style_parts = [f"FontSize={size}"]
            
            # Converte cor hex para formato ASS (BGR)
            color_hex = color.lstrip('#')
            if len(color_hex) == 6:
                r, g, b = color_hex[0:2], color_hex[2:4], color_hex[4:6]
                ass_color = f"&H{b}{g}{r}&"  # BGR format
                style_parts.append(f"PrimaryColour={ass_color}")
            
            if bold:
                style_parts.append("Bold=1")
            
            style = ",".join(style_parts)
            subtitle_filter += f":force_style='{style}'"
        
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
            return output_path
        except subprocess.CalledProcessError as e:
            raise Exception(f"Erro ao mesclar legenda ao vídeo: {e}")
