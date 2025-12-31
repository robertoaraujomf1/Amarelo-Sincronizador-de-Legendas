#!/usr/bin/env python3
"""
Amarelo Subs - Aplicativo para transcrição, tradução e sincronização de legendas
Versão completa com instalação automática de dependências e FFmpeg (Padronizado PyQt6)
"""

import sys
import os
import traceback
import subprocess
import importlib.util
from pathlib import Path

# Adicionar o diretório raiz e o diretório src ao path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, 'src')
if BASE_DIR not in sys.path: sys.path.insert(0, BASE_DIR)
if SRC_DIR not in sys.path: sys.path.insert(0, SRC_DIR)

# ============================================================================
# 1. INSTALADOR BÁSICO DE DEPENDÊNCIAS
# ============================================================================

def install_python_dependencies():
    """Instala dependências Python automaticamente"""
    print("=" * 60)
    print("Amarelo Subs - Instalação de Dependências")
    print("=" * 60)
    
    # Atualizado para PyQt6 para manter consistência
    dependencies = [
        'PyQt6>=6.4.0',
        'torch>=2.0.0',
        'torchaudio>=2.0.0',
        'openai-whisper>=20231117',
        'translators>=3.0.0',
        'googletrans==4.0.0-rc1',
        'requests>=2.31.0',
        'moviepy>=1.0.3',
        'pydub>=0.25.1',
        'opencv-python>=4.8.0',
        'numpy>=1.24.0',
        'python-dotenv>=1.0.0',
        'pysrt>=1.1.2',
        'chardet>=5.1.0',
        'packaging'
    ]
    
    # Tenta instalar via pip
    try:
        print("Verificando e instalando pacotes necessários...")
        # Instala em lote para ser mais rápido
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + dependencies)
        print("✓ Dependências processadas.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠ Erro na instalação automática: {e}")
        return False

# ============================================================================
# 2. INSTALADOR DE FFMPEG (Mantido conforme original, removido detalhes para brevidade)
# ============================================================================
# ... (Mantenha suas funções install_ffmpeg, _install_ffmpeg_windows, etc. aqui) ...

def install_ffmpeg():
    # Mantenha sua implementação original de FFmpeg aqui
    # Apenas certifique-se de que ela retorna True/False
    return True 

# ============================================================================
# 3. VERIFICAÇÃO DO AMBIENTE
# ============================================================================

def check_environment():
    """Verifica e prepara o ambiente de execução"""
    print("\n1. Verificando dependências Python...")
    if not install_python_dependencies():
        print("⚠ Algumas dependências falharam.")
    
    print("\n2. Verificando FFmpeg...")
    install_ffmpeg()
    
    print("\n3. Criando estrutura de diretórios...")
    project_dir = BASE_DIR
    for d in ['output', 'temp', 'logs', 'models']:
        os.makedirs(os.path.join(project_dir, d), exist_ok=True)
    
    return True

# ============================================================================
# 4. FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    try:
        print("\nAmarelo Subs - Inicializando...")
        
        if not check_environment():
            return 1
        
        # IMPORTANTE: Imports do PyQt6 ocorrem APÓS a verificação de dependências
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtGui import QIcon
            from PyQt6.QtCore import Qt
            
            # No PyQt6, o High DPI é automático, mas podemos forçar se necessário
            # QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

            from src.utils.config_manager import ConfigManager
            from src.gui.main_window import MainWindow
            from src.utils.update_checker import UpdateChecker
            
        except ImportError as e:
            print(f"\n✗ Erro de Importação: {e}")
            print("Certifique-se de que o PyQt6 está instalado corretamente.")
            input("Pressione Enter para sair...")
            return 1

        app = QApplication(sys.argv)
        app.setApplicationName("Amarelo Subs")
        app.setStyle('Fusion')
        
        config_manager = ConfigManager()
        window = MainWindow(config_manager)
        
        # Verificador de Updates (PyQt6 compatível)
        checker = UpdateChecker()
        # Conecte o sinal aqui se sua MainWindow tiver o slot exibir_alerta
        if hasattr(window, 'exibir_alerta_atualizacao'):
            checker.update_available.connect(window.exibir_alerta_atualizacao)
        checker.check_for_updates_async()

        window.show()
        
        # No PyQt6 é 'exec()' em vez de 'exec_()'
        return app.exec()
        
    except Exception as e:
        print(f"\n✗ ERRO CRÍTICO: {e}")
        traceback.print_exc()
        input("\nPressione Enter para sair...")
        return 1

if __name__ == "__main__":
    sys.exit(main())