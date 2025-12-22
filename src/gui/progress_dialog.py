from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt


class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processando")
        self.setModal(True)
        self.setFixedSize(400, 120)

        layout = QVBoxLayout(self)

        self.label = QLabel("Preparando...")
        self.label.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)

        layout.addWidget(self.label)
        layout.addWidget(self.progress)

    def update_progress(self, current: int, total: int, filename: str):
        percent = int((current / total) * 100) if total else 0
        self.progress.setValue(percent)
        self.label.setText(f"Processando:\n{filename}")
