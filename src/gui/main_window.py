import os
import threading

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QMessageBox, QLabel, QComboBox
)


SUPPORTED_LANGS = {
    "de_DE": "Alemão",
    "en_GB": "Inglês (UK)",
    "en_US": "Inglês (US)",
    "es_ES": "Espanhol",
    "fr_FR": "Francês",
    "ja_JP": "Japonês",
    "pt_BR": "Português (Brasil)",
    "pt_PT": "Português (Portugal)",
    "ko_KR": "Coreano",
}


class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Amarelo - Sincronizador de Legendas")
        self.setMinimumSize(500, 300)

        self.selected_dir = None

        self._build_ui()

    # ---------------- UI ----------------

    def _build_ui(self):
        central = QWidget(self)
        layout = QVBoxLayout(central)

        self.label_dir = QLabel("Nenhum diretório selecionado")
        btn_select = QPushButton("Selecionar Diretório")
        btn_start = QPushButton("Iniciar Sincronização")
        btn_settings = QPushButton("Configurações")

        btn_select.clicked.connect(self.select_directory)
        btn_start.clicked.connect(self.start)
        btn_settings.clicked.connect(self.open_settings)

        layout.addWidget(self.label_dir)
        layout.addWidget(btn_select)
        layout.addWidget(btn_start)
        layout.addWidget(btn_settings)

        layout.addStretch()
        self.setCentralWidget(central)

    # ---------------- Ações ----------------

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Selecionar Diretório de Vídeos"
        )
        if directory:
            self.selected_dir = directory
            self.label_dir.setText(directory)

    def open_settings(self):
        # IMPORT TARDIO (evita QWidget antes do QApplication)
        from gui.settings_dialog import SettingsDialog

        dlg = SettingsDialog(self.config, self)
        dlg.exec()

    # ---------------- Perguntas ----------------

    def ask_language_new(self, detected_lang):
        return self._ask_language(
            f"Idioma detectado: {detected_lang}\n"
            "Em qual idioma deseja gerar as legendas?"
        )

    def ask_translate_existing(self):
        reply = QMessageBox.question(
            self,
            "Tradução",
            "Deseja traduzir as legendas para outro idioma?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            return self._ask_language("Escolha o idioma de destino:")
        return None

    def _ask_language(self, title):
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Idioma")
        dialog.setText(title)

        combo = QComboBox(dialog)
        for code, name in SUPPORTED_LANGS.items():
            combo.addItem(f"{name} ({code})", code)

        dialog.layout().addWidget(combo)
        dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        if dialog.exec() == QMessageBox.Ok:
            return combo.currentData()

        return None

    # ---------------- Execução ----------------

    def start(self):
        if not self.selected_dir or not os.path.isdir(self.selected_dir):
            QMessageBox.warning(
                self, "Aviso", "Selecione um diretório válido."
            )
            return

        # IMPORTS TARDIOS (evita QWidget antes do QApplication)
        from gui.progress_dialog import ProgressDialog
        from core.workflow_manager import WorkflowManager

        progress = ProgressDialog(self)
        progress.show()

        manager = WorkflowManager(
            config=self.config,
            gpu_info={
                "available": self.config.get_runtime_value("gpu_available"),
                "name": self.config.get_runtime_value("gpu_name"),
                "backend": self.config.get_runtime_value("gpu_backend"),
            },
            ui_callbacks={
                "progress": progress.update_progress,
                "ask_language_new": self.ask_language_new,
                "ask_translate_existing": self.ask_translate_existing,
            }
        )

        def run():
            try:
                manager.process_directory(self.selected_dir)
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))
            finally:
                progress.close()

        threading.Thread(target=run, daemon=True).start()
