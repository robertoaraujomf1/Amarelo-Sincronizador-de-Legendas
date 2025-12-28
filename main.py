import sys
import os
import traceback
import warnings

# Suprime o aviso do huggingface_hub sobre symlinks
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*huggingface_hub.*symlinks.*")

from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog, QLabel
from PySide6.QtGui import QIcon
from PySide6.QtCore import QFile, QTextStream, Qt


# =========================
# SETUP PATHS
# =========================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.core.gpu_detector import detect_gpu
from src.gui.main_window import MainWindow
from src.utils.config_manager import ConfigManager
from src.utils.ffmpeg_installer import ensure_ffmpeg_installed, is_ffmpeg_installed
from src.utils.dependency_installer import ensure_dependencies
# =========================
# UI HELPERS
# =========================
def load_styles(app: QApplication):
    """Carrega o tema escuro para toda a aplicação"""
    styles_dir = os.path.join(ROOT_DIR, "assets", "styles")
    qss_file = "dark_theme.qss"  # Usando apenas o tema escuro
    
    qss_path = os.path.join(styles_dir, qss_file)
    if os.path.exists(qss_path):
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                style = f.read()
                app.setStyleSheet(style)
                print(f"✅ Tema escuro carregado: {qss_path}")
        except Exception as e:
            print(f"❌ Erro ao carregar tema: {e}")
    else:
        print(f"⚠️  Arquivo de tema não encontrado: {qss_path}")

    


def set_app_icon(app: QApplication):
    icon_path = os.path.join(ROOT_DIR, "assets", "icons", "app_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))


def show_fatal_error(message: str, details: str = ""):
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("Erro fatal")
    msg.setText(message)

    if details:
        msg.setDetailedText(details)

    msg.exec()
    sys.exit(1)


# =========================
# MAIN
# =========================
def check_and_install_ffmpeg(app: QApplication, config: ConfigManager) -> bool:
    """Verifica e instala FFmpeg se necessário. Retorna True se estiver disponível."""
    if is_ffmpeg_installed(config):
        return True
    
    # Cria diálogo de progresso melhorado
    dialog = QProgressDialog("Verificando FFmpeg...", None, 0, 0)
    dialog.setWindowTitle("Instalação do FFmpeg")
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.setCancelButton(None)  # Não permite cancelar
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.setAutoReset(False)
    dialog.setMinimumWidth(400)
    dialog.show()
    
    # Força processamento de eventos
    app.processEvents()
    
    def update_progress(message: str):
        """Atualiza o progresso e processa eventos da UI"""
        dialog.setLabelText(message)
        app.processEvents()
        # Pequeno delay para garantir que a UI atualize
        import time
        time.sleep(0.01)
    
    try:
        # Tenta instalar (passa app para processar eventos e o config)
        success, error_msg = ensure_ffmpeg_installed(update_progress, app, config)
    except Exception as e:
        import traceback
        traceback.print_exc()
        success = False
        error_msg = f"Erro durante instalação: {str(e)}"
    finally:
        dialog.close()
        app.processEvents()
    
    if not success:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("FFmpeg não encontrado")
        msg.setText(
            "O FFmpeg é necessário para o funcionamento do aplicativo.\n\n"
            "Não foi possível instalá-lo automaticamente."
        )
        if error_msg:
            msg.setDetailedText(error_msg + "\n\n"
                "Por favor, instale o FFmpeg manualmente:\n"
                "1. Baixe de https://ffmpeg.org/download.html\n"
                "2. Extraia e adicione ao PATH do sistema\n"
                "3. Ou use: winget install Gyan.FFmpeg\n\n"
                "Após instalar, reinicie o aplicativo.")
        msg.exec()
        return False
    
    return True


def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Amarelo Legendas")

        set_app_icon(app)
        load_styles(app)

        # INICIALIZA CONFIG ANTES DE TUDO
        config = ConfigManager()
        config.load()

        # Verifica e instala FFmpeg antes de continuar
        if not check_and_install_ffmpeg(app, config):
            sys.exit(1)
        
        # Verifica e instala dependências Python
        dialog = QProgressDialog("Verificando dependências...", None, 0, 0)
        dialog.setWindowTitle("Verificação de Dependências")
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.setCancelButton(None)
        dialog.setMinimumDuration(0)
        dialog.setAutoClose(False)
        dialog.setAutoReset(False)
        dialog.show()
        app.processEvents()
        
        def update_dep_progress(message: str):
            dialog.setLabelText(message)
            app.processEvents()
            import time
            time.sleep(0.01)
        
        try:
            success, error_msg = ensure_dependencies(update_dep_progress)
        except Exception as e:
            success = False
            error_msg = f"Erro ao verificar dependências: {str(e)}"
        finally:
            dialog.close()
            app.processEvents()
        
        if not success:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Dependências não encontradas")
            msg.setText(
                "Algumas dependências necessárias não foram encontradas.\n\n"
                "O aplicativo pode não funcionar corretamente."
            )
            if error_msg:
                msg.setDetailedText(error_msg + "\n\n"
                    "Por favor, instale manualmente usando:\n"
                    "pip install faster-whisper openai PySide6")
            msg.exec()

        # O config já foi carregado acima, então apenas obtemos os valores de GPU
        gpu_info = detect_gpu()
        if gpu_info:
            config.set_runtime_value("gpu_available", gpu_info.get("available", False))
            config.set_runtime_value("gpu_name", gpu_info.get("name"))
            config.set_runtime_value("gpu_backend", gpu_info.get("backend"))
        else:
            config.set_runtime_value("gpu_available", False)
            config.set_runtime_value("gpu_name", None)
            config.set_runtime_value("gpu_backend", None)

        window = MainWindow(config=config)
        window.show()

        sys.exit(app.exec())

    except Exception:
        tb = traceback.format_exc()
        show_fatal_error(
            "O aplicativo encontrou um erro inesperado e precisa ser encerrado.",
            details=tb
        )


if __name__ == "__main__":
    main()