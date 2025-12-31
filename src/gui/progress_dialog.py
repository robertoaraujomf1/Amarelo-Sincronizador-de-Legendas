from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt

class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processando")
        self.setFixedSize(400, 120)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        self.label = QLabel("Preparando...")
        self.progress = QProgressBar()
        self.progress.setStyleSheet("QProgressBar::chunk { background-color: #f4c430; }")
        
        layout.addWidget(self.label)
        layout.addWidget(self.progress)

    def update_progress(self, value):
        self.progress.setValue(value)

    def update_preview(self, text):
        self.label.setText(text)