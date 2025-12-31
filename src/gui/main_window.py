import os
import ctypes
import sys
import subprocess
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QMessageBox, QGroupBox, 
                             QLabel, QCheckBox, QTextEdit, QColorDialog, QComboBox)
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtCore import Qt, QSize

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
        self.last_dir = ""
        
        self.setWindowTitle("Amarelo Subs")
        
        # Iniciar Maximizado
        self.showMaximized()
        
        # Caminhos de Ícones
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.icon_path = os.path.join(base_dir, "assets", "icons", "app_icon.png")
        self.paint_icon_path = os.path.join(base_dir, "assets", "icons", "paint.png")
        self.setWindowIcon(QIcon(self.icon_path))

        # Estilo Global (Design Deep Ocean)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #0f172a, stop:1 #1e293b);
            }
            QLabel { color: #e2e8f0; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }
            QCheckBox { color: #f4c430; font-weight: bold; }
            QComboBox { 
                background-color: #334155; 
                color: white; 
                border: 1px solid #475569; 
                border-radius: 6px;
                padding: 4px;
            }
            QTextEdit {
                background-color: rgba(15, 23, 42, 0.9);
                color: #94a3b8;
                border: none;
                border-top: 1px solid #334155;
                border-bottom: 1px solid #334155;
                font-family: 'Consolas';
                font-size: 14px;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout Principal com Margem Zero nas laterais para o Log
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 20, 0, 20)
        self.main_layout.setSpacing(15)

        self._setup_ui()

    def _setup_ui(self):
        # --- CONTAINER SUPERIOR (Configurações) ---
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setContentsMargins(20, 0, 20, 0)

        self.style_group = QGroupBox("Personalização da Legenda e Tradução")
        self.style_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid rgba(244, 196, 48, 0.4);
                border-radius: 10px;
                margin-top: 20px;
                color: #f4c430;
                font-weight: bold;
                background-color: rgba(30, 41, 59, 0.4);
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)
        
        group_layout = QHBoxLayout()
        group_layout.setContentsMargins(15, 20, 15, 15)
        
        # Cor
        self.btn_color_picker = QPushButton()
        if os.path.exists(self.paint_icon_path):
            self.btn_color_picker.setIcon(QIcon(self.paint_icon_path))
            self.btn_color_picker.setIconSize(QSize(24, 24))
        self.btn_color_picker.setFixedSize(45, 40)
        self._update_button_style()
        self.btn_color_picker.clicked.connect(self._open_color_dialog)

        # Tamanho
        self.combo_size = QComboBox()
        self.combo_size.addItems(["Pequeno", "Médio", "Grande"])
        self.combo_size.setCurrentIndex(1)

        # Tradução
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Original", "Português", "Inglês", "Espanhol"])

        # Negrito
        self.check_bold = QCheckBox("Negrito")
        self.check_bold.setChecked(True)

        group_layout.addWidget(QLabel("Cor:"))
        group_layout.addWidget(self.btn_color_picker)
        group_layout.addSpacing(20)
        group_layout.addWidget(QLabel("Tamanho:"))
        group_layout.addWidget(self.combo_size)
        group_layout.addSpacing(20)
        group_layout.addWidget(QLabel("Traduzir para:"))
        group_layout.addWidget(self.combo_lang)
        group_layout.addSpacing(20)
        group_layout.addWidget(self.check_bold)
        group_layout.addStretch()

        self.style_group.setLayout(group_layout)
        settings_layout.addWidget(self.style_group)
        self.main_layout.addWidget(settings_container)

        # --- LOG DE ATIVIDADES (Margem Lateral Zero) ---
        log_label_container = QWidget()
        log_label_layout = QVBoxLayout(log_label_container)
        log_label_layout.setContentsMargins(20, 10, 20, 0)
        log_label_layout.addWidget(QLabel("Histórico de Processamento:"))
        self.main_layout.addWidget(log_label_container)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.document().setDocumentMargin(20) # Respiro interno para o texto
        self.main_layout.addWidget(self.log_view)

        # --- CONTAINER INFERIOR (Botões) ---
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(20, 10, 20, 0)

        self.btn_open_folder = QPushButton(" 📂 ABRIR PASTA DAS LEGENDAS")
        self.btn_open_folder.setVisible(False)
        self.btn_open_folder.setMinimumHeight(45)
        self.btn_open_folder.setStyleSheet("""
            QPushButton { 
                background-color: #334155; 
                color: #f4c430; 
                border: 1px solid #f4c430; 
                border-radius: 10px; 
                font-weight: bold; 
            }
            QPushButton:hover { background-color: #475569; }
        """)
        self.btn_open_folder.clicked.connect(self._open_folder)
        buttons_layout.addWidget(self.btn_open_folder)

        self.btn_run = QPushButton(" INICIAR PROCESSO DE LEGENDAGEM")
        self.btn_run.setMinimumHeight(70)
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fde047, stop:1 #f4c430);
                color: #0f172a; 
                font-weight: bold; 
                font-size: 16px; 
                border-radius: 12px;
            }
            QPushButton:hover { background: #fde047; }
        """)
        self.btn_run.clicked.connect(self._on_start)
        buttons_layout.addWidget(self.btn_run)

        self.main_layout.addWidget(buttons_container)

    def _update_button_style(self):
        self.btn_color_picker.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.selected_color};
                border-radius: 8px;
                border: 2px solid rgba(255,255,255,0.2);
            }}
            QPushButton:hover {{ border: 2px solid #f4c430; }}
        """)

    def _open_color_dialog(self):
        color = QColorDialog.getColor(QColor(self.selected_color), self, "Escolha a Cor")
        if color.isValid():
            self.selected_color = color.name()
            self._update_button_style()

    def _open_folder(self):
        if self.last_dir:
            if sys.platform == "win32":
                os.startfile(self.last_dir)
            else:
                subprocess.run(["xdg-open", self.last_dir])

    def _handle_status_update(self, text):
        if hasattr(self, 'progress_ui'):
            self.progress_ui.update_preview(text)
        self.log_view.append(f"<span style='color: #64748b;'>»</span> {text}")

    def _on_finished(self, success, message):
        if hasattr(self, 'progress_ui'): self.progress_ui.close()
        
        if success:
            self.btn_open_folder.setVisible(True)
            self.log_view.append("<br><b style='color: #4ade80;'>✔ Finalizado com sucesso.</b>")
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Sucesso")
            msg_box.setText(message)
            msg_box.setInformativeText("Clique em OK para abrir a pasta automaticamente.")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            
            if msg_box.exec() == QMessageBox.StandardButton.Ok:
                self._open_folder()
        else:
            self.log_view.append(f"<br><b style='color: #f87171;'>✘ Erro: {message}</b>")
            QMessageBox.critical(self, "Erro", message)

    def _on_start(self):
        self.btn_open_folder.setVisible(False)
        self.config.set("font_color", self.selected_color)
        self.config.set("font_bold", self.check_bold.isChecked())
        self.config.set("font_size_label", self.combo_size.currentText())
        self.config.set("target_lang", self.combo_lang.currentText())

        dir_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if dir_path:
            self.last_dir = dir_path
            self.log_view.clear()
            self.log_view.append(f"<b>[INÍCIO]</b> Pasta: <i style='color:#f4c430;'>{dir_path}</i>")
            
            self.progress_ui = ProgressDialog(self)
            self.progress_ui.show()
            
            self.workflow.set_directory(dir_path)
            self.workflow.progress_update.connect(self.progress_ui.update_progress)
            self.workflow.preview_update.connect(self._handle_status_update)
            self.workflow.finished.connect(self._on_finished)
            self.workflow.start()