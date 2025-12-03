import json
import os
import locale

class LanguageManager:
    def __init__(self, config):
        self.config = config
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
        
        # Carregar idioma salvo ou detectar do sistema
        saved_language = config.get_setting('language', 'system')
        if saved_language == 'system':
            system_lang = self.detect_system_language()
            self.load_language(system_lang)
        else:
            self.load_language(saved_language)
    
    def detect_system_language(self):
        """Detecta o idioma do sistema operacional"""
        try:
            # Primeiro tenta locale do sistema
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                # Converte para formato do nosso sistema
                if system_locale.startswith('pt_BR'):
                    return 'pt_BR'
                elif system_locale.startswith('pt'):
                    return 'pt_PT'
                elif system_locale.startswith('en_GB'):
                    return 'en_GB'
                elif system_locale.startswith('en'):
                    return 'en_US'
                elif system_locale.startswith('fr'):
                    return 'fr_FR'
                elif system_locale.startswith('de'):
                    return 'de_DE'
                elif system_locale.startswith('es'):
                    return 'es_ES'
                elif system_locale.startswith('ja'):
                    return 'ja_JP'
        except:
            pass
        
        # Fallback para inglês US
        return 'en_US'
    
    def load_language(self, language_code):
        """Carrega o idioma especificado"""
        self.current_language = language_code
        
        if language_code == 'system':
            # Usar detecção automática
            language_code = self.detect_system_language()
        
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
    
    def get_available_languages(self):
        """Retorna a lista de idiomas disponíveis"""
        return self.supported_languages
    
    def set_language(self, language_code):
        """Define um novo idioma e salva nas configurações"""
        success = self.load_language(language_code)
        if success:
            self.config.set_setting('language', language_code)
        return success