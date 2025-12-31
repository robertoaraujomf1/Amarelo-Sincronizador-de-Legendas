import os
import ctypes
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QMessageBox, QGroupBox, 
                             QLabel, QCheckBox, QTextEdit, QColorDialog)
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtCore import Qt, QSize  # <--- O QSize deve estar aqui!

from src.core.workflow_manager import WorkflowManager
from src.gui.progress_dialog import ProgressDialog

def set_app_id():
    if sys.platform == "win32":
        myappid = 'amarelo.subs.ai.v1' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

set_app_id()

class MainWindow(QMainWindow):
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.workflow = WorkflowManager(self.config)
        
        self.selected_color = "#f4c430"
        
        self.setWindowTitle("Amarelo Subs")
        self.setMinimumSize(700, 550)
        
        # Caminhos Absolutos
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.icon_path = os.path.join(base_dir, "assets", "icons", "app_icon.png")
        self.paint_icon_path = os.path.join(base_dir, "assets", "icons", "paint.png")
        
        self.setWindowIcon(QIcon(self.icon_path))

        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QLabel { color: #f4c430; font-weight: bold; }
            QCheckBox { color: #f4c430; font-weight: bold; }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._setup_ui()

    def _setup_ui(self):
        self.style_group = QGroupBox("Configurações de Estilo")
        self.style_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #f4c430;
                border-radius: 8px;
                margin-top: 15px;
                font-weight: bold;
                color: #f4c430;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        style_layout = QHBoxLayout()

        # --- BOTÃO COM ÍCONE DE TINTA ---
        self.btn_color_picker = QPushButton()
        
        if os.path.exists(self.paint_icon_path):
            icon = QIcon(self.paint_icon_path)
            self.btn_color_picker.setIcon(icon)
            self.btn_color_picker.setIconSize(QSize(32, 32))
        else:
            self.btn_color_picker.setText("Cor")

        self.btn_color_picker.setFixedSize(55, 50)
        self._update_button_style()
        self.btn_color_picker.clicked.connect(self._open_color_dialog)
        
        self.check_bold = QCheckBox("Negrito")
        self.check_bold.setChecked(True)

        style_layout.addWidget(QLabel("Cor da Legenda:"))
        style_layout.addWidget(self.btn_color_picker)
        style_layout.addSpacing(20)
        style_layout.addWidget(self.check_bold)
        style_layout.addStretch()
        self.style_group.setLayout(style_layout)
        
        self.main_layout.addWidget(self.style_group)

        # Log de Atividades
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(QLabel("Log de Atividades:"))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("background-color: #1e1e1e; color: #f4c430; border: 1px solid #f4c430; font-family: 'Consolas';")
        self.main_layout.addWidget(self.log_view)

        # Botão Principal
        self.btn_run = QPushButton(" SELECIONAR PASTA E GERAR LEGENDAS")
        self.btn_run.setIcon(QIcon(self.icon_path))
        self.btn_run.setMinimumHeight(65)
        self.btn_run.setStyleSheet("background-color: #f4c430; color: black; font-weight: bold; border-radius: 10px;")
        self.btn_run.clicked.connect(self._on_start)
        self.main_layout.addWidget(self.btn_run)

    def _update_button_style(self):
        self.btn_color_picker.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.selected_color};
                border: 2px solid #f4c430;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: #ffd700; }}
        """)

    def _open_color_dialog(self):
        color = QColorDialog.getColor(QColor(self.selected_color), self, "Escolha a Cor")
        if color.isValid():
            self.selected_color = color.name()
            self._update_button_style()

    def _handle_status_update(self, text):
        if hasattr(self, 'progress_ui'):
            self.progress_ui.update_preview(text)
        self.log_view.append(f"<b>[STATUS]</b> {text}")

    def _on_finished(self, success, message):
        if hasattr(self, 'progress_ui'): self.progress_ui.close()
        if success: QMessageBox.information(self, "Sucesso", message)
        else: QMessageBox.critical(self, "Erro", message)

    def _on_start(self):
        self.config.set("font_color", self.selected_color)
        self.config.set("font_bold", self.check_bold.isChecked())
        dir_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if dir_path:
            self.log_view.clear()
            self.progress_ui = ProgressDialog(self)
            self.progress_ui.show()
            self.workflow.set_directory(dir_path)
            self.workflow.progress_update.connect(self.progress_ui.update_progress)
            self.workflow.preview_update.connect(self._handle_status_update)
            self.workflow.finished.connect(self._on_finished)
            self.workflow.start()