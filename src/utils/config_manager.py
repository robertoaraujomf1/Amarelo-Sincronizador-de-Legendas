import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConfigManager:
    """Gerenciador de configurações"""
    
    def __init__(self, config_file: str = None):
        if config_file is None:
            config_dir = os.path.join(os.path.expanduser('~'), '.amarelo_legendas')
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, 'config.json')
        
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configurações do arquivo"""
        default_config = {
            'general': {
                'output_dir': 'output',
                'language': 'pt-BR',
                'theme': 'dark'
            },
            'transcription': {
                'model': 'base',
                'device': 'auto',
                'language': 'auto'
            },
            'translation': {
                'enabled': False,
                'target_language': 'pt',
                'provider': 'google'
            },
            'font': {
                'name': 'Arial',
                'size': 20,
                'color': '#FFFFFF',
                'bold': False,
                'format_type': 'ass'  # 'ass' ou 'srt'
            },
            'sync': {
                'method': 'scene',
                'threshold': 0.5
            },
            'merge': {
                'enabled': False,
                'codec': 'libx264',
                'crf': 23
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self._merge_configs(default_config, user_config)
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
        
        return default_config
    
    def _merge_configs(self, default: Dict, user: Dict):
        """Mescla configurações padrão com do usuário"""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_configs(default[key], value)
            else:
                default[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtém valor de configuração"""
        keys = key.split('.')
        config = self.config
        
        for k in keys:
            if isinstance(config, dict) and k in config:
                config = config[k]
            else:
                return default
        
        return config
    
    def set(self, key: str, value: Any):
        """Define valor de configuração"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save()
    
    def save(self):
        """Salva configurações no arquivo"""
        try:
            config_dir = os.path.dirname(self.config_file)
            os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
    
    def get_font_config(self) -> Dict[str, Any]:
        """Obtém configurações de fonte"""
        return self.config.get('font', {})
    
    def get_translation_config(self) -> Dict[str, Any]:
        """Obtém configurações de tradução"""
        return self.config.get('translation', {})