import json
import os
from PyQt6.QtCore import QTranslator, QLibraryInfo

class LanguageManager:
    def __init__(self):
        self.locales_dir = "src/locales"
        self.current_language = "system"
        self.current_translation = None
        self.translations = {}
        
        self.supported_languages = {
            'pt_BR': 'Português (Brasil)',
            'pt_PT': 'Português (Portugal)',
            'en_US': 'English (US)',
            'en_GB': 'English (UK)',
            'fr_FR': 'Français',
            'de_DE': 'Deutsch',
            'es_ES': 'Español',
            'ja_JP': '日本語'
        }
    
    def load_language(self, language_code):
        """Carrega o idioma especificado"""
        self.current_language = language_code
        
        if language_code == 'system':
            return True
        
        try:
            translation_file = os.path.join(self.locales_dir, f"{language_code}.json")
            if os.path.exists(translation_file):
                with open(translation_file, 'r', encoding='utf-8') as f:
                    self.translations[language_code] = json.load(f)
                self.current_translation = translation_file
                return True
        except Exception as e:
            print(f"Erro ao carregar idioma {language_code}: {str(e)}")
        
        return False
    
    def get_translation(self, key, default=None):
        """Obtém a tradução para a chave especificada"""
        if (self.current_language in self.translations and 
            key in self.translations[self.current_language]):
            return self.translations[self.current_language][key]
        return default if default is not None else key
    
    def get_supported_language(self, system_language):
        """Obtém o idioma suportado mais próximo do idioma do sistema"""
        # Mapear idiomas do sistema para os suportados
        language_mapping = {
            'pt_BR': 'pt_BR',
            'pt_PT': 'pt_PT',
            'pt': 'pt_BR',
            'en_US': 'en_US',
            'en_GB': 'en_GB',
            'en': 'en_US',
            'fr_FR': 'fr_FR',
            'fr': 'fr_FR',
            'de_DE': 'de_DE',
            'de': 'de_DE',
            'es_ES': 'es_ES',
            'es': 'es_ES',
            'ja_JP': 'ja_JP',
            'ja': 'ja_JP'
        }
        
        return language_mapping.get(system_language, 'en_US')
    
    def get_available_languages(self):
        """Retorna a lista de idiomas disponíveis"""
        return self.supported_languages