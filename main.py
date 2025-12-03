import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.gui.main_window import MainWindow
from src.utils.config_manager import ConfigManager
from src.utils.language_manager import LanguageManager
from src.gui.theme_manager import apply_dark_theme

def main():
    app = QApplication(sys.argv)
    
    # Configurar ícone do aplicativo
    app_icon = QIcon("assets/icons/app_icon.ico")
    
    # Inicializar gerenciadores
    config = ConfigManager()
    language_manager = LanguageManager(config)  # CORRIGIDO: passa o config
    
    # Carregar tema salvo
    theme = config.get_setting('theme', 'light')
    if theme == 'dark':
        apply_dark_theme(app)
    
    # Criar janela principal
    window = MainWindow(config, language_manager, app_icon)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()