"""
Módulo para verificar e instalar dependências automaticamente
"""
import sys
import subprocess
import importlib.util


def is_package_installed(package_name: str) -> bool:
    """Verifica se um pacote Python está instalado"""
    try:
        spec = importlib.util.find_spec(package_name)
        return spec is not None
    except Exception:
        return False


def install_package(package_name: str, progress_callback=None) -> bool:
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
        print(f"Erro ao instalar {package_name}: {e}")
        return False


def ensure_dependencies(progress_callback=None):
    """
    Garante que todas as dependências necessárias estão instaladas.
    Retorna (sucesso, mensagem_erro)
    """
    required_packages = {
        "faster-whisper": "faster_whisper",
        "openai": "openai",
        "PySide6": "PySide6",
    }
    
    missing_packages = []
    
    for pip_name, import_name in required_packages.items():
        if not is_package_installed(import_name):
            missing_packages.append(pip_name)
    
    if not missing_packages:
        return True, None
    
    if progress_callback:
        progress_callback(f"Instalando {len(missing_packages)} dependência(s)...")
    
    failed_packages = []
    for package in missing_packages:
        if not install_package(package, progress_callback):
            failed_packages.append(package)
    
    if failed_packages:
        return False, f"Não foi possível instalar: {', '.join(failed_packages)}"
    
    return True, None

