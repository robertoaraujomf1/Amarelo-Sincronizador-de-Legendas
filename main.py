# main.py
import sys
import os
from pathlib import Path

# Adicionar o diretório src ao path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from src.gui.main_window import MainWindow
from src.utils.config_manager import ConfigManager
from src.utils.language_manager import LanguageManager

def main():
    # Inicializar aplicação
    app = QApplication(sys.argv)
    app.setApplicationName("Amarelo Sincronizador de Legendas")
    
    # Carregar configurações
    config = ConfigManager()
    
    # Carregar gerenciador de idiomas
    language_manager = LanguageManager(config)
    
    # Carregar ícone
    app_icon = QIcon()
    icon_path = "assets/icons/app_icon.ico"
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
    
    # Criar janela principal
    window = MainWindow(config, language_manager, app_icon)
    window.show()
    
    # Executar aplicação
    sys.exit(app.exec())

if __name__ == "__main__":
    main()