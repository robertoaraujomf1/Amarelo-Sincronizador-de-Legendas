import logging
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

class TranslationEngine:
    def __init__(self, config_manager=None):
        self.config = config_manager
        # Removido o lang_map antigo, pois agora a MainWindow já envia o código (pt, en, etc)
        # Se você quiser manter suporte aos dois formatos (nome longo e código), usamos este:
        self.supported_codes = ["pt", "en", "es", "fr", "it", "de"]

    def translate_segments(self, segments, target_lang):
        """
        Traduz uma lista de segmentos mantendo a estrutura do Whisper.
        target_lang agora recebe diretamente o código (ex: 'pt') vindo do Workflow.
        """
        if not target_lang or target_lang == "Original":
            return segments

        # O código vindo da MainWindow (via Workflow) já é 'pt', 'en', etc.
        # Mas vamos garantir que ele seja uma string limpa.
        target_code = target_lang.lower().strip()

        try:
            translator = GoogleTranslator(source='auto', target=target_code)
        except Exception as e:
            logger.error(f"Erro ao inicializar tradutor para {target_code}: {e}")
            return segments
        
        translated_segments = []
        logger.info(f"Iniciando tradução real para o código: {target_code}")

        for seg in segments:
            try:
                original_text = seg.get('text', '').strip()
                
                # Pula tradução se o texto for vazio ou apenas números/símbolos
                if not original_text:
                    translated_segments.append(seg)
                    continue

                # Traduz o texto do segmento
                text_translated = translator.translate(original_text)
                
                # Cria uma cópia do segmento com o novo texto
                new_seg = seg.copy()
                new_seg['text'] = text_translated if text_translated else original_text
                translated_segments.append(new_seg)
                
            except Exception as e:
                logger.error(f"Erro ao traduzir segmento: {e}")
                translated_segments.append(seg) # Mantém original em caso de erro

        return translated_segments