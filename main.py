import sys
import os
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import QFile, QTextStream


# =========================
# SETUP PATHS
# =========================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.core.gpu_detector import detect_gpu
from src.gui.main_window import MainWindow
from src.utils.config_manager import ConfigManager
# =========================
# UI HELPERS
# =========================
def load_styles(app: QApplication):
    styles_dir = os.path.join(ROOT_DIR, "assets", "styles")
    qss_files = ["main_style.qss", "dark_theme.qss"]

    final_style = ""

    for qss in qss_files:
        qss_path = os.path.join(styles_dir, qss)
        if os.path.exists(qss_path):
            file = QFile(qss_path)
            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                final_style += stream.readAll() + "\n"
                file.close()

    app.setStyleSheet(final_style)


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
def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Amarelo - Sincronizador de Legendas")

        set_app_icon(app)
        load_styles(app)

        config = ConfigManager()
        config.load()

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
