import sys
import os

# Garante que a pasta 'src' esteja no path para imports internos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.gui.main_window import MainWindow
from src.utils.config_manager import ConfigManager


def main():
    # 1. Cria a aplicação base
    app = QApplication(sys.argv)
    
    # 2. Inicializa o Gerenciador de Configurações
    # Isso carrega o nome "Amarelo Subs" e as preferências do usuário
    config = ConfigManager()
    app.setApplicationName(config.get('app_name', 'Amarelo Subs'))
    app.setApplicationVersion(config.get('version', '1.0.0'))

    # 3. Configura o Ícone Global do Aplicativo
    icon_path = os.path.join('assets', 'icons', 'app_icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))


    # 5. Inicializa e exibe a Janela Principal
    # Passamos o config_manager para que a janela saiba as preferências
    window = MainWindow(config_manager=config)
    window.show()

    # 6. Executa o loop de eventos
    sys.exit(app.exec())

if __name__ == "__main__":
    # Tratamento simples para evitar crash em ambientes sem display
    try:
        main()
    except Exception as e:
        print(f"Erro crítico ao iniciar o Amarelo Subs: {e}")
        input("Pressione Enter para fechar...")