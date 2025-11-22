import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator, QLocale
from PySide6.QtGui import QIcon

from src.gui.main_window import MainWindow
from src.utils.config_manager import ConfigManager
from src.utils.language_manager import LanguageManager

def main():
    app = QApplication(sys.argv)
    
    # Configurar ícone ANTES de criar a janela
    app_icon = QIcon()
    if os.path.exists("assets/icons/app_icon.ico"):
        app_icon = QIcon("assets/icons/app_icon.ico")
    elif os.path.exists("assets/icons/app_icon.png"):
        app_icon = QIcon("assets/icons/app_icon.png")
    
    app.setWindowIcon(app_icon)
    app.setApplicationName("Amarelo Sincronizador de Legendas")
    app.setApplicationVersion("1.0.0")
    
    # Carregar configurações
    config = ConfigManager()
    
    # Gerenciador de idiomas
    language_manager = LanguageManager()
    current_lang = config.get_setting('language', 'system')
    
    if current_lang == 'system':
        system_lang = QLocale.system().name()
        current_lang = language_manager.get_supported_language(system_lang)
    
    language_manager.load_language(current_lang)
    
    # Aplicar traduções
    translator = QTranslator()
    if translator.load(language_manager.current_translation):
        app.installTranslator(translator)
    
    # Aplicar tema
    theme = config.get_setting('theme', 'light')
    if theme == 'dark':
        from src.gui.theme_manager import apply_dark_theme
        apply_dark_theme(app)
    
    # Criar e mostrar janela principal
    window = MainWindow(config, language_manager, app_icon)
    window.showMaximized()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()