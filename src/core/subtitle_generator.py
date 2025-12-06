# src/core/subtitle_generator.py
from datetime import datetime, timedelta
from typing import Dict, Any
class SubtitleGenerator:
    """
    Gera o conteúdo da legenda a partir de uma transcrição.
    """

    def __init__(self):
        pass

    def generate(self, transcription: Dict, video_info: Dict, settings: Dict) -> Dict:
        """
        Converte uma transcrição em um formato de legenda estruturado.

        Args:
            transcription (Dict): O resultado da transcrição do áudio.
                                  Deve conter 'language' e 'segments'.
            video_info (Dict): Metadados do vídeo (não utilizado nesta versão,
                               mas pode ser útil para lógicas futuras).
            settings (Dict): Configurações de legenda (não utilizado nesta versão).

        Returns:
            Dict: Um dicionário estruturado representando a legenda,
                  pronto para ser salvo pelo SubtitleEditor.
        """
        if not transcription or 'segments' not in transcription:
            print("❌ Erro: Dados de transcrição inválidos para gerar legenda.")
            return {'language': 'pt-BR', 'segments': []}

        # A estrutura da transcrição já é muito parecida com o que precisamos.
        # Esta classe pode, no futuro, incluir lógicas mais complexas, como:
        # - Agrupar segmentos curtos.
        # - Dividir segmentos longos.
        # - Adicionar informações de estilo com base nas configurações.
        # - Limitar o número de caracteres por linha.

        # Por enquanto, apenas repassamos a estrutura.
        subtitle_content = {
            'language': transcription.get('language', 'pt-BR'),
            'segments': self._format_segments(transcription.get('segments', []))
        }

        return subtitle_content

    def _format_segments(self, segments: list) -> list:
        """
        Formata os segmentos da transcrição para o formato de legenda.
        """
        formatted_segments = []
        for i, seg in enumerate(segments):
            # Garante que as chaves essenciais existam
            if 'start' in seg and 'end' in seg and 'text' in seg:
                formatted_segments.append({
                    'index': i + 1,
                    'start': self._seconds_to_time(seg['start']),
                    'end': self._seconds_to_time(seg['end']),
                    'text': str(seg['text']).strip()
                })
        return formatted_segments

    def _seconds_to_time(self, seconds: float) -> str:
        """Converte segundos para string de tempo (HH:MM:SS,ms)."""
        if not isinstance(seconds, (int, float)) or seconds < 0:
            seconds = 0
        try:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs_float = seconds % 60
            secs = int(secs_float)
            milliseconds = int((secs_float - secs) * 1000)
            
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
        except Exception as e:
            print(f"⚠️ Erro ao converter segundos '{seconds}': {e}")
            return "00:00:00,000"