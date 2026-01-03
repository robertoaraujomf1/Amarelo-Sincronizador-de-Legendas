import logging
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

class TranslationEngine:
    def __init__(self, config_manager=None):
        self.config = config_manager

    def translate_segments(self, segments, target_lang, progress_callback=None):
        if not target_lang or target_lang == "Original":
            return segments

        target_code = target_lang.lower().strip()
        
        try:
            translator = GoogleTranslator(source='auto', target=target_code)
        except Exception as e:
            logger.error(f"Erro ao carregar tradutor: {e}")
            return segments
        
        translated_segments = []
        total = len(segments)

        for i, seg in enumerate(segments):
            try:
                original_text = seg.get('text', '').strip()
                new_seg = seg.copy()

                if original_text:
                    # Tradução real via Google
                    new_seg['text'] = translator.translate(original_text)
                
                translated_segments.append(new_seg)

                # Atualiza o progresso via callback para o Workflow
                if progress_callback:
                    percent = int(((i + 1) / total) * 100)
                    progress_callback(percent)

            except Exception as e:
                logger.error(f"Erro no segmento {i}: {e}")
                translated_segments.append(seg)

        return translated_segments