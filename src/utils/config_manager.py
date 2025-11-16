import json
import os

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """Carrega as configurações do arquivo"""
        default_config = {
            "language": "system",
            "theme": "light",
            "font_family": "Arial",
            "font_size": 16,
            "font_color": "#FFFFFF",
            "recent_folders": []
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Garantir que todas as chaves padrão existam
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                    return loaded_config
        except Exception as e:
            print(f"Erro ao carregar configurações: {str(e)}")
        
        return default_config.copy()
    
    def save_config(self):
        """Salva as configurações no arquivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar configurações: {str(e)}")
            return False
    
    def get_setting(self, key, default=None):
        """Obtém uma configuração"""
        return self.config.get(key, default)
    
    def set_setting(self, key, value):
        """Define uma configuração"""
        self.config[key] = value
        return self.save_config()
    
    def get_recent_folders(self):
        """Obtém a lista de pastas recentes"""
        return self.config.get('recent_folders', [])
    
    def add_recent_folder(self, folder_path):
        """Adiciona uma pasta à lista de recentes"""
        recent_folders = self.get_recent_folders()
        
        if folder_path in recent_folders:
            recent_folders.remove(folder_path)
        
        recent_folders.insert(0, folder_path)
        recent_folders = recent_folders[:10]  # Manter apenas as 10 mais recentes
        
        self.config['recent_folders'] = recent_folders
        return self.save_config()