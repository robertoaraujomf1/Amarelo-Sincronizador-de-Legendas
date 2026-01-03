import os
import ctypes
import sys
import subprocess
import time
import random
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QMessageBox, QGroupBox, 
                             QLabel, QCheckBox, QTextEdit, QColorDialog, QComboBox,
                             QProgressBar)
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtCore import Qt, QSize

from src.core.workflow_manager import WorkflowManager

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
        self.start_time = 0
        
        self.setWindowTitle("Amarelo Subs")
        
        # Força a abertura maximizada
        self.setWindowState(Qt.WindowState.WindowMaximized)
        
        # Caminhos de Ícones
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.icon_path = os.path.join(base_dir, "assets", "icons", "app_icon.png")
        self.paint_icon_path = os.path.join(base_dir, "assets", "icons", "paint.png")
        self.setWindowIcon(QIcon(self.icon_path))

        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:1 #1e293b);
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
                font-family: 'Consolas';
                font-size: 13px;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 20, 0, 0)
        self.main_layout.setSpacing(10)

        # Chama a montagem da interface
        self._setup_ui()

    def _update_button_style(self):
        """Atualiza a cor do botão de conta-gotas"""
        self.btn_color_picker.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.selected_color};
                border-radius: 6px;
                border: 2px solid #475569;
            }}
            QPushButton:hover {{
                border: 2px solid #f4c430;
            }}
        """)

    def _setup_ui(self):
        # --- CONTAINER CONFIGURAÇÕES ---
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(20, 0, 20, 0)

        self.style_group = QGroupBox("Estilo da Legenda e Tradução")
        self.style_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid rgba(244, 196, 48, 0.3);
                border-radius: 10px;
                margin-top: 20px;
                color: #f4c430;
                background-color: rgba(30, 41, 59, 0.4);
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)
        
        group_layout = QHBoxLayout()
        group_layout.setContentsMargins(15, 20, 15, 15)
        
        self.btn_color_picker = QPushButton()
        if os.path.exists(self.paint_icon_path):
            self.btn_color_picker.setIcon(QIcon(self.paint_icon_path))
            self.btn_color_picker.setIconSize(QSize(20, 20))
        self.btn_color_picker.setFixedSize(45, 35)
        
        # Agora o método já existe quando é chamado
        self._update_button_style()
        self.btn_color_picker.clicked.connect(self._open_color_dialog)

        self.combo_size = QComboBox()
        self.combo_size.addItems(["Pequeno", "Médio", "Grande"])
        self.combo_size.setCurrentIndex(1)

        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Original", "Português", "Inglês", "Espanhol"])

        self.check_bold = QCheckBox("Negrito")
        self.check_bold.setChecked(True)

        group_layout.addWidget(QLabel("Cor:"))
        group_layout.addWidget(self.btn_color_picker)
        group_layout.addSpacing(15)
        group_layout.addWidget(QLabel("Tamanho:"))
        group_layout.addWidget(self.combo_size)
        group_layout.addSpacing(15)
        group_layout.addWidget(QLabel("Traduzir:"))
        group_layout.addWidget(self.combo_lang)
        group_layout.addSpacing(15)
        group_layout.addWidget(self.check_bold)
        group_layout.addStretch()

        self.style_group.setLayout(group_layout)
        top_layout.addWidget(self.style_group)
        self.main_layout.addWidget(top_container)

        # --- PAINEL DE PROGRESSO INTEGRADO ---
        self.prog_container = QWidget()
        self.prog_container.setVisible(False)
        prog_layout = QVBoxLayout(self.prog_container)
        prog_layout.setContentsMargins(25, 10, 25, 10)

        self.status_main = QLabel("Iniciando motores...")
        self.status_main.setStyleSheet("color: #f4c430; font-size: 15px; font-weight: bold;")
        
        self.status_detail = QLabel("Preparando arquivos...")
        self.status_detail.setStyleSheet("color: #94a3b8; font-size: 12px; font-style: italic;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #334155;
                border-radius: 9px;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #fde047, stop:1 #f4c430);
                border-radius: 9px;
            }
        """)

        self.eta_label = QLabel("Tempo restante: calculando...")
        self.eta_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.eta_label.setStyleSheet("color: #64748b; font-size: 11px;")

        prog_layout.addWidget(self.status_main)
        prog_layout.addWidget(self.status_detail)
        prog_layout.addWidget(self.progress_bar)
        prog_layout.addWidget(self.eta_label)
        self.main_layout.addWidget(self.prog_container)

        # --- ÁREA DE LOG ---
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.main_layout.addWidget(self.log_view)

        # --- BOTÕES DE AÇÃO ---
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(20, 10, 20, 20)

        self.btn_open_folder = QPushButton(" 📂 ABRIR PASTA RESULTANTE")
        self.btn_open_folder.setVisible(False)
        self.btn_open_folder.setMinimumHeight(45)
        self.btn_open_folder.setStyleSheet("QPushButton { background-color: #334155; color: #f4c430; border: 1px solid #f4c430; border-radius: 10px; font-weight: bold; }")
        self.btn_open_folder.clicked.connect(self._open_folder)
        bottom_layout.addWidget(self.btn_open_folder)

        self.btn_run = QPushButton(" INICIAR LEGENDAGEM")
        self.btn_run.setMinimumHeight(65)
        self.btn_run.setStyleSheet("QPushButton { background: #f4c430; color: #0f172a; font-weight: bold; font-size: 16px; border-radius: 12px; }")
        self.btn_run.clicked.connect(self._on_start)
        bottom_layout.addWidget(self.btn_run)

        self.main_layout.addWidget(bottom_container)

    def _open_color_dialog(self):
        color = QColorDialog.getColor(QColor(self.selected_color), self, "Cor da Legenda")
        if color.isValid():
            self.selected_color = color.name()
            self._update_button_style()

    def _open_folder(self):
        if self.last_dir:
            if sys.platform == "win32":
                os.startfile(self.last_dir)
            else:
                subprocess.run(["xdg-open", self.last_dir])

    def _handle_progress(self, value):
        if isinstance(value, (int, float)):
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(int(value))
            elapsed = time.time() - self.start_time
            if value > 3:
                total_est = (elapsed / value) * 100
                remaining = total_est - elapsed
                m, s = divmod(int(remaining), 60)
                self.eta_label.setText(f"Tempo restante: {m:02d}:{s:02d}")

    def _handle_preview(self, text):
        messages = ["Sincronizando áudio...", "IA analisando contexto...", "Traduzindo termos..."]
        if len(text) > 5:
            self.status_detail.setText(f"✍️ Ouvido: \"{text[:70]}...\"")
        else:
            self.status_detail.setText(random.choice(messages))
        self.log_view.append(f"<span style='color: #64748b;'>[INFO]</span> {text}")

    def _on_finished(self, success, message):
        self.prog_container.setVisible(False)
        self.btn_run.setEnabled(True)
        if success:
            self.btn_open_folder.setVisible(True)
            self.log_view.append("<br><b style='color: #4ade80;'>✔ Sucesso!</b>")
            QMessageBox.information(self, "Concluído", "Legendas geradas com sucesso!")
        else:
            QMessageBox.critical(self, "Erro", message)

    def _on_start(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Escolha a pasta")
        if dir_path:
            self.last_dir = dir_path
            self.btn_run.setEnabled(False)
            self.btn_open_folder.setVisible(False)
            self.log_view.clear()
            self.prog_container.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.start_time = time.time()
            
            self.config.set("font_color", self.selected_color)
            self.config.set("font_bold", self.check_bold.isChecked())
            self.config.set("font_size_label", self.combo_size.currentText())
            self.config.set("target_lang", self.combo_lang.currentText())

            self.workflow.set_directory(dir_path)
            self.workflow.progress_update.connect(self._handle_progress)
            self.workflow.preview_update.connect(self._handle_preview)
            self.workflow.finished.connect(self._on_finished)
            self.workflow.start()