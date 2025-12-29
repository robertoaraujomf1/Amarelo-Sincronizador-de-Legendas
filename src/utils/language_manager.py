import json
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class LanguageManager:
    """Gerenciador de internacionalização"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Evitar múltiplas inicializações
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.config_manager = None  # Será configurado depois
        self.current_language = None
        self.translations = {}
        
    def initialize(self, config_manager):
        """Inicializa com o config_manager (deve ser chamado após criação)"""
        self.config_manager = config_manager
        self.load_language()
    
    def load_language(self, language_code: Optional[str] = None):
        """Carrega as traduções para o idioma especificado"""
        try:
            if not self.config_manager:
                logger.warning("ConfigManager não inicializado. Usando padrão.")
                language_code = language_code or 'pt_BR'
            else:
                language_code = language_code or self.config_manager.get('general.language', 'pt_BR')
            
            # Caminho para arquivos de idioma
            locales_dir = os.path.join(
                os.path.dirname(__file__), 
                '..', 'locales'
            )
            
            # Tentar carregar idioma específico
            lang_file = os.path.join(locales_dir, f"{language_code}.json")
            
            if os.path.exists(lang_file):
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                self.current_language = language_code
                logger.info(f"Idioma carregado: {language_code}")
            else:
                # Fallback para inglês
                fallback_file = os.path.join(locales_dir, "en_US.json")
                if os.path.exists(fallback_file):
                    with open(fallback_file, 'r', encoding='utf-8') as f:
                        self.translations = json.load(f)
                    self.current_language = 'en_US'
                    logger.warning(f"Idioma {language_code} não encontrado. Usando fallback en_US.")
                else:
                    self.translations = {}
                    logger.error("Arquivo de idioma fallback não encontrado.")
                    
        except Exception as e:
            logger.error(f"Erro ao carregar idioma: {e}")
            self.translations = {}
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """Obtém uma tradução"""
        return self.translations.get(key, default or key)
    
    def get_current_language(self) -> str:
        """Retorna o idioma atual"""
        return self.current_language or 'pt_BR'

# Instância global (não inicializa ConfigManager aqui)
language_manager = LanguageManager()