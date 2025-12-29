import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTranslator
from PySide6.QtGui import QIcon

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.gui.main_window import MainWindow
from src.utils.config_manager import config_manager
from src.utils.language_manager import language_manager
from src.utils.dependency_installer import DependencyInstaller
from src.gui.theme_manager import ThemeManager

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Função principal para iniciar a aplicação"""
    try:
        # Instalar dependências se necessário
        installer = DependencyInstaller()
        installer.install_dependencies()
        
        # Criar aplicação Qt
        app = QApplication(sys.argv)
        app.setAttribute(Qt.AA_EnableHighDpiScaling)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps)
        
        # Configurar ícone da aplicação
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icons', 'app_icon.ico')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        # Inicializar configurações (ORDEM CORRETA!)
        config_manager.initialize()
        
        # Inicializar gerenciador de idiomas
        language_manager.initialize(config_manager)
        
        # Configurar tema
        theme_manager = ThemeManager(app, config_manager)
        theme_manager.apply_theme()
        
        # Criar e mostrar janela principal
        window = MainWindow(config_manager)
        window.show()
        
        # Executar aplicação
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {str(e)}")
        raise

if __name__ == "__main__":
    main()