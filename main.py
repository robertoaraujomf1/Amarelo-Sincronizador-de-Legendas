import sys
import os
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import QFile, QTextStream


# =========================
# PATH BASE
# =========================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


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
        from gui.main_window import MainWindow
        from utils.config_manager import ConfigManager
        from core.gpu_detector import detect_gpu

        app = QApplication(sys.argv)
        app.setApplicationName("Amarelo - Sincronizador de Legendas")

        set_app_icon(app)
        load_styles(app)

        config = ConfigManager()
        config.load()

        gpu_info = detect_gpu()
        config.set_runtime_value("gpu_available", gpu_info["available"])
        config.set_runtime_value("gpu_name", gpu_info["name"])
        config.set_runtime_value("gpu_backend", gpu_info["backend"])

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
