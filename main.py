import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.gui.main_window import MainWindow
from src.utils.config_manager import ConfigManager

def resource_path(relative_path):
    """ 
    Garante que o caminho dos ícones funcione tanto em desenvolvimento 
    quanto no executável (.exe) gerado pelo PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    # 1. Ajustes de DPI (Alta Resolução)
    # Isso evita que a interface fique "embaçada" em monitores 4K ou escalas de 125%/150%
    if hasattr(Qt, 'ApplicationAttribute'):
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    # 2. Criar a instância do App
    app = QApplication(sys.argv)
    app.setApplicationName("Amarelo Subs")

    # 3. Inicializar o Gerenciador de Configurações
    config = ConfigManager()

    # 4. Criar a Janela Principal
    # Note: O window.show() foi removido daqui porque o showMaximized() 
    # já é tratado dentro do __init__ da MainWindow para garantir o modo tela cheia.
    window = MainWindow(config)
    
    # Se por algum motivo o sistema operacional ignorar o comando interno,
    # esta linha abaixo reforça a exibição:
    if not window.isVisible():
        window.show()

    # 5. Executar o loop do programa
    sys.exit(app.exec())

if __name__ == "__main__":
    main()