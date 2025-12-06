from deep_translator import GoogleTranslator
from typing import Dict, Optional

class SubtitleTranslator:
    def __init__(self):
        pass
        
    def translate_text(self, text: str, dest_language: str = 'pt', src_language: str = 'auto') -> str:
        """Traduz texto para o idioma de destino"""
        try:
            # O deep_translator usa códigos de idioma simples (ex: 'pt' em vez de 'pt-BR')
            target_lang_code = dest_language.split('-')[0]
            source_lang_code = src_language.split('-')[0]
            
            translated_text = GoogleTranslator(source=source_lang_code, target=target_lang_code).translate(text)
            return translated_text if translated_text else text
        except Exception as e:
            print(f"   ⚠️ Erro na tradução: {str(e)}")
            return text
            
    def translate_transcription(self, transcription: Dict, target_language: str) -> Optional[Dict]:
        """Traduz todos os segmentos de uma transcrição."""
        if not transcription or 'segments' not in transcription:
            return None
            
        source_language = transcription.get('language', 'auto')
        
        # Agrupar textos para traduzir em lote (mais eficiente)
        texts_to_translate = [seg['text'] for seg in transcription['segments']]
        
        # O separador deve ser algo que não exista no texto
        separator = "\n<|segment|>\n"
        combined_text = separator.join(texts_to_translate)
        
        translated_combined_text = self.translate_text(combined_text, target_language, source_language)
        translated_segments = translated_combined_text.split(separator.strip())
        
        if len(translated_segments) == len(transcription['segments']):
            for i, seg in enumerate(transcription['segments']):
                seg['text'] = translated_segments[i].strip()
            transcription['language'] = target_language
            return transcription
        else:
            print("   ⚠️ Falha na tradução em lote, o número de segmentos não corresponde.")
            return None
    
    def get_language_code(self, language_name):
        """Converte nome do idioma para código"""
        language_map = {
            'pt_BR': 'pt',
            'pt_PT': 'pt',
            'en_US': 'en',
            'en_GB': 'en',
            'fr_FR': 'fr',
            'de_DE': 'de',
            'es_ES': 'es',
            'ja_JP': 'ja'
        }
        return language_map.get(language_name, 'pt')