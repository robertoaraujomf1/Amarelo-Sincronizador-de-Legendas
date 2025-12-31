import subprocess
import sys
import importlib

class DependencyInstaller:
    """Instala dependências automaticamente"""
    
    def __init__(self):
        self.required_packages = [
            'PyQt5',
            'torch',
            'torchaudio',
            'openai-whisper',
            'translators',
            'googletrans',
            'requests',
            'moviepy',
            'pydub',
            'opencv-python',
            'numpy',
            'python-dotenv',
            'pysrt',
            'chardet'
        ]
        
    def install_required_packages(self):
        """Instala pacotes ausentes"""
        for package in self.required_packages:
            try:
                importlib.import_module(self._get_module_name(package))
                print(f"✓ {package} já está instalado")
            except ImportError:
                print(f"Instalando {package}...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    print(f"✓ {package} instalado com sucesso")
                except subprocess.CalledProcessError:
                    print(f"✗ Falha ao instalar {package}")
                    
    def _get_module_name(self, package):
        """Obtém o nome do módulo para importação"""
        name_map = {
            'openai-whisper': 'whisper',
            'opencv-python': 'cv2',
            'python-dotenv': 'dotenv'
        }
        return name_map.get(package, package.split('==')[0].split('>=')[0])