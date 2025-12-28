"""
Gerenciador de idiomas para internacionalização da aplicação
"""

import json
from pathlib import Path
from typing import Dict, Optional

from src.utils.config_manager import ConfigManager


class LanguageManager:
    """Gerencia traduções e idiomas da aplicação"""
    
    _instance = None
    _translations = None
    _current_language = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._translations is None:
            self.config_manager = ConfigManager()
            self.config_manager.load()
            self._translations = {}
            self._load_all_translations()
            self.set_language(self.config_manager.get('language', 'pt_BR'))
    
    def _load_all_translations(self):
        """Carrega todas as traduções disponíveis"""
        locales_dir = Path(__file__).parent.parent / 'locales'
        
        if not locales_dir.exists():
            print(f"Diretório de traduções não encontrado: {locales_dir}")
            return
        
        for lang_file in locales_dir.glob('*.json'):
            lang_code = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self._translations[lang_code] = json.load(f)
            except Exception as e:
                print(f"Erro ao carregar tradução {lang_code}: {e}")
    
    def set_language(self, language_code: str):
        """Define o idioma atual"""
        if language_code in self._translations:
            self._current_language = language_code
            self.config_manager.set('language', language_code)
        else:
            # Fallback para inglês US
            if 'en_US' in self._translations:
                self._current_language = 'en_US'
            else:
                self._current_language = list(self._translations.keys())[0] if self._translations else None
    
    def get_text(self, key: str, default: str = None) -> str:
        """Obtém o texto traduzido para a chave especificada"""
        if not self._current_language or self._current_language not in self._translations:
            return default or key
        
        translations = self._translations[self._current_language]
        
        # Tentar obter a tradução
        if key in translations:
            return translations[key]
        
        # Fallback para inglês US se disponível
        if self._current_language != 'en_US' and 'en_US' in self._translations:
            en_translations = self._translations['en_US']
            if key in en_translations:
                return en_translations[key]
        
        # Fallback para a própria chave
        return default or key
    
    def get_language_name(self, language_code: str) -> str:
        """Obtém o nome do idioma no próprio idioma"""
        lang_names = {
            'pt_BR': 'Português (Brasil)',
            'en_US': 'English (US)',
            'es_ES': 'Español (España)',
            'fr_FR': 'Français (France)',
            'de_DE': 'Deutsch (Deutschland)',
            'ja_JP': '日本語 (日本)',
            'pt_PT': 'Português (Portugal)',
            'it_IT': 'Italiano (Italia)',
            'ru_RU': 'Русский (Россия)',
            'zh_CN': '中文 (中国)',
            'ko_KR': '한국어 (한국)',
            'same': self.get_text('same_as_video') or 'Mesmo idioma do vídeo'
        }
        
        return lang_names.get(language_code, language_code)
    
    def get_available_languages(self) -> Dict[str, str]:
        """Retorna dicionário de idiomas disponíveis (código -> nome)"""
        available = {}
        
        for lang_code in self._translations.keys():
            if lang_code == 'en_GB':  # Pular inglês britânico, usar US como padrão
                continue
            available[lang_code] = self.get_language_name(lang_code)
        
        # Garantir que os principais idiomas estejam presentes
        main_languages = {
            'pt_BR': 'Português (Brasil)',
            'en_US': 'English (US)',
            'es_ES': 'Español (España)',
            'fr_FR': 'Français (France)',
            'de_DE': 'Deutsch (Deutschland)',
            'ja_JP': '日本語 (日本)'
        }
        
        for lang_code, lang_name in main_languages.items():
            if lang_code not in available:
                available[lang_code] = lang_name
        
        return dict(sorted(available.items()))
    
    def get_current_language(self) -> str:
        """Retorna o código do idioma atual"""
        return self._current_language or 'pt_BR'
    
    def format_text(self, key: str, *args) -> str:
        """Obtém texto traduzido e aplica formatação com argumentos"""
        text = self.get_text(key, key)
        
        try:
            return text.format(*args)
        except:
            return text


# Instância global para uso conveniente
language_manager = LanguageManager()
