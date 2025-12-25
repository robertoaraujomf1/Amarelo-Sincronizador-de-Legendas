import os
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QMessageBox, QLabel, QComboBox
)

# Imports movidos para o topo para melhor organização
from gui.progress_dialog import ProgressDialog
from core.workflow_manager import WorkflowManager


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


class Worker(QObject):
    """
    Worker para executar tarefas pesadas em uma thread separada,
    evitando o congelamento da UI.
    """
    finished = Signal()
    error = Signal(str)
    progress = Signal(str, int, int)

    def __init__(self, manager: WorkflowManager, directory: str):
        super().__init__()
        self.manager = manager
        self.directory = directory

    def run(self):
        """Inicia a execução do processo."""
        try:
            self.manager.process_directory(
                directory=self.directory,
                progress_callback=self.progress.emit
            )
        except Exception as e:
            import traceback
            # Envia o erro com traceback para o thread principal
            error_info = f"Ocorreu um erro inesperado:\n{e}\n\n{traceback.format_exc()}"
            self.error.emit(error_info)
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Amarelo - Sincronizador de Legendas")
        self.setMinimumSize(500, 300)

        self.selected_dir = None
        self.thread = None

        self._build_ui()

    def _build_ui(self):
        central = QWidget(self)
        layout = QVBoxLayout(central)

        self.label_dir = QLabel("Nenhum diretório selecionado")
        btn_select = QPushButton("Selecionar Diretório")
        self.btn_start = QPushButton("Iniciar Sincronização")
        btn_settings = QPushButton("Configurações")

        btn_select.clicked.connect(self.select_directory)
        self.btn_start.clicked.connect(self.start)
        btn_settings.clicked.connect(self.open_settings)

        layout.addWidget(self.label_dir)
        layout.addWidget(btn_select)
        layout.addWidget(self.btn_start)
        layout.addWidget(btn_settings)

        layout.addStretch()
        self.setCentralWidget(central)

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Selecionar Diretório de Vídeos"
        )
        if directory:
            self.selected_dir = directory
            self.label_dir.setText(directory)

    def open_settings(self):
        from gui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self.config, self)
        dlg.exec()

    def show_error(self, error_message: str):
        """Exibe uma caixa de diálogo de erro crítico."""
        QMessageBox.critical(self, "Erro na Execução", error_message)

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

    def start(self):
        """Inicia o processo de sincronização em uma thread separada."""
        if self.thread and self.thread.isRunning():
            QMessageBox.information(self, "Aviso", "Um processo já está em andamento.")
            return

        if not self.selected_dir or not os.path.isdir(self.selected_dir):
            QMessageBox.warning(self, "Aviso", "Selecione um diretório válido.")
            return

        self.btn_start.setEnabled(False)

        # Configura a caixa de diálogo de progresso
        self.progress = ProgressDialog(self)
        self.progress.setModal(True)
        self.progress.show()

        # Configura a thread e o worker
        self.thread = QThread()
        manager = WorkflowManager(config=self.config)
        worker = Worker(manager, self.selected_dir)
        worker.moveToThread(self.thread)

        # Conecta os sinais da thread e do worker
        self.thread.started.connect(worker.run)
        worker.finished.connect(self.thread.quit)

        # Limpeza automática da thread e do worker
        worker.finished.connect(worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Conecta os sinais do worker aos slots da UI
        worker.error.connect(self.show_error)
        worker.progress.connect(self.progress.update_progress)

        # Ações a serem executadas quando o trabalho terminar
        worker.finished.connect(self.progress.close)
        worker.finished.connect(lambda: self.btn_start.setEnabled(True))

        self.thread.start()
