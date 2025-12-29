"""
Módulo para verificar e instalar dependências automaticamente
"""
import sys
import subprocess
import importlib.util
import logging

logger = logging.getLogger(__name__)

class DependencyInstaller:
    """Instala dependências necessárias para o aplicativo"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def _is_package_installed(package_name: str) -> bool:
        """Verifica se um pacote Python está instalado"""
        try:
            spec = importlib.util.find_spec(package_name)
            return spec is not None
        except Exception:
            return False
    
    @staticmethod
    def _install_package(package_name: str, progress_callback=None) -> bool:
        """Instala um pacote Python usando pip"""
        try:
            if progress_callback:
                progress_callback(f"Instalando {package_name}...")
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package_name, "--quiet"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,  # 5 minutos
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.error(f"Erro ao instalar {package_name}: {e}")
            return False
    
    def install_dependencies(self, progress_callback=None):
        """
        Garante que todas as dependências necessárias estão instaladas.
        """
        required_packages = {
            "faster-whisper": "faster_whisper",
            "openai": "openai",
            "PySide6": "PySide6",
            "requests": "requests",
            "ffmpeg-python": "ffmpeg_python",
            "Pillow": "PIL"
        }
        
        missing_packages = []
        
        # Verificar quais pacotes estão faltando
        for pip_name, import_name in required_packages.items():
            if not self._is_package_installed(import_name):
                missing_packages.append(pip_name)
        
        if not missing_packages:
            logger.info("Todas as dependências já estão instaladas.")
            return True
        
        if progress_callback:
            progress_callback(f"Instalando {len(missing_packages)} dependência(s)...")
        
        logger.info(f"Instalando {len(missing_packages)} pacotes: {', '.join(missing_packages)}")
        
        failed_packages = []
        for package in missing_packages:
            if not self._install_package(package, progress_callback):
                failed_packages.append(package)
        
        if failed_packages:
            error_msg = f"Não foi possível instalar: {', '.join(failed_packages)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info("Todas as dependências foram instaladas com sucesso.")
        return True

# Função de compatibilidade para uso externo
def ensure_dependencies(progress_callback=None):
    """
    Função de conveniência para garantir dependências.
    Retorna (sucesso, mensagem_erro)
    """
    installer = DependencyInstaller()
    try:
        installer.install_dependencies(progress_callback)
        return True, None
    except Exception as e:
        return False, str(e)