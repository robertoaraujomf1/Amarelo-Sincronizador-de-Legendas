from googletrans import Translator

class SubtitleTranslator:
    def __init__(self):
        self.translator = Translator()
        
    def translate_text(self, text, dest_language='pt'):
        """Traduz texto para o idioma de destino"""
        try:
            translation = self.translator.translate(text, dest=dest_language)
            return translation.text
        except Exception as e:
            print(f"Erro na tradução: {str(e)}")
            return text
    
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