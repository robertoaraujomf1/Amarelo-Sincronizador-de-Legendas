import os
import sys
import time
import subprocess
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QMessageBox, QGroupBox, 
                             QLabel, QCheckBox, QTextEdit, QColorDialog, QComboBox,
                             QProgressBar, QScrollArea)
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtCore import Qt, QSize
from src.core.workflow_manager import WorkflowManager

class MainWindow(QMainWindow):
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.workflow = WorkflowManager(self.config)
        self.selected_color = "#f4c430"
        self.total_start_time = 0
        self.last_dir = ""
        
        self.setWindowTitle("Amarelo Subs")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        
        self._apply_styles()
        self._setup_ui()

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:1 #1e293b); }
            QLabel { color: #e2e8f0; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }
            QCheckBox { color: #f4c430; font-weight: bold; }
            QComboBox { background-color: #334155; color: white; border: 1px solid #475569; border-radius: 6px; padding: 4px; }
            QTextEdit { background-color: rgba(15, 23, 42, 0.9); color: #94a3b8; border: 1px solid #334155; font-family: 'Consolas'; }
            QScrollArea { border: 1px solid #334155; border-radius: 8px; background-color: #1e293b; }
            #scrollContent { background-color: #1e293b; }
            
            /* CAIXA DE DIÁLOGO FIM */
            QMessageBox { background-color: #1e293b; border: 1px solid #f4c430; }
            QMessageBox QLabel { color: #e2e8f0; font-size: 14px; }
            QMessageBox QPushButton { background-color: #334155; color: white; padding: 6px 20px; border-radius: 4px; border: 1px solid #475569; }
            QMessageBox QPushButton:hover { background-color: #f4c430; color: #0f172a; }
        """)

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(30, 30, 30, 30)

        # Configurações
        self.style_group = QGroupBox("Configurações do Projeto")
        self.style_group.setStyleSheet("QGroupBox { border: 1px solid #f4c430; border-radius: 10px; margin-top: 20px; padding-top: 15px; color: #f4c430; font-weight: bold; }")
        
        style_layout = QHBoxLayout()
        
        self.btn_color = QPushButton()
        self.btn_color.setFixedSize(50, 35)
        self.btn_color.clicked.connect(self._select_color)
        self._update_btn_color()

        self.combo_size = QComboBox()
        self.combo_size.addItems(["Pequeno", "Médio", "Grande"])
        self.combo_size.setCurrentIndex(1)

        self.check_bold = QCheckBox("Negrito")
        self.check_bold.setChecked(True)

        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Original (Sem Tradução)", "Português", "Inglês", "Espanhol", "Francês", "Alemão", "Italiano"])

        style_layout.addWidget(QLabel("Cor:"))
        style_layout.addWidget(self.btn_color)
        style_layout.addSpacing(15)
        style_layout.addWidget(QLabel("Tamanho:"))
        style_layout.addWidget(self.combo_size)
        style_layout.addSpacing(20)
        style_layout.addWidget(self.check_bold) # Negrito antes
        style_layout.addSpacing(20)
        style_layout.addWidget(QLabel("Traduzir para:"))
        style_layout.addWidget(self.combo_lang) # Tradução depois
        style_layout.addStretch()
        self.style_group.setLayout(style_layout)
        self.main_layout.addWidget(self.style_group)

        # Fila de vídeos
        self.video_group = QGroupBox("Vídeos na Fila")
        self.video_group.setStyleSheet("QGroupBox { border: 1px solid #334155; border-radius: 10px; padding-top: 15px; color: #94a3b8; }")
        video_vbox = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scrollContent")
        self.video_list_layout = QVBoxLayout(self.scroll_content)
        self.video_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        video_vbox.addWidget(self.scroll_area)
        self.video_group.setLayout(video_vbox)
        self.main_layout.addWidget(self.video_group, stretch=1)

        # Progresso
        self.prog_container = QWidget()
        self.prog_container.setVisible(False)
        prog_layout = QVBoxLayout(self.prog_container)
        self.progress_general = QProgressBar()
        self.progress_general.setFixedHeight(22)
        self.progress_general.setStyleSheet("QProgressBar { background: #0f172a; border: 1px solid #334155; border-radius: 5px; text-align: center; color: white; } QProgressBar::chunk { background: #4ade80; }")
        self.progress_current = QProgressBar()
        self.progress_current.setFixedHeight(12)
        self.progress_current.setStyleSheet("QProgressBar { background: #0f172a; border-radius: 4px; } QProgressBar::chunk { background: #f4c430; }")
        prog_layout.addWidget(self.progress_general)
        prog_layout.addWidget(self.progress_current)
        self.main_layout.addWidget(self.prog_container)

        # Logs
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(100)
        self.main_layout.addWidget(self.log_view)

        # Botões Inferiores
        self.bottom_layout = QHBoxLayout()
        self.btn_open_folder = QPushButton(" 📁 ABRIR PASTA RESULTANTE")
        self.btn_open_folder.setFixedHeight(50)
        self.btn_open_folder.setVisible(False)
        self.btn_open_folder.setStyleSheet("QPushButton { background: #1e293b; color: white; font-weight: bold; border: 1px solid #f4c430; border-radius: 8px; }")
        self.btn_open_folder.clicked.connect(self._open_folder)

        self.btn_run = QPushButton("🚀 INICIAR LEGENDAGEM")
        self.btn_run.setFixedHeight(50)
        self.btn_run.setStyleSheet("QPushButton { background: #f4c430; color: #0f172a; font-weight: bold; font-size: 14px; border-radius: 8px; }")
        self.btn_run.clicked.connect(self._on_start)
        
        self.bottom_layout.addWidget(self.btn_open_folder, 1)
        self.bottom_layout.addWidget(self.btn_run, 2)
        self.main_layout.addLayout(self.bottom_layout)

    def _select_color(self):
        color = QColorDialog.getColor(QColor(self.selected_color))
        if color.isValid():
            self.selected_color = color.name()
            self._update_btn_color()

    def _update_btn_color(self):
        self.btn_color.setStyleSheet(f"QPushButton {{ background-color: {self.selected_color}; border: 1px solid white; border-radius: 4px; }}")

    def _open_folder(self):
        if self.last_dir: os.startfile(self.last_dir)

    def _on_start(self):
        path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if not path: return
        self.last_dir = path
        
        lang_map = {"Português": "pt", "Inglês": "en", "Espanhol": "es", "Francês": "fr", "Alemão": "de", "Italiano": "it"}
        choice = self.combo_lang.currentText()
        
        self.config.set("font.color", self.selected_color)
        self.config.set("font.bold", self.check_bold.isChecked())
        self.config.set("translation.enabled", choice != "Original (Sem Tradução)")
        self.config.set("translation.target_language", lang_map.get(choice, "pt"))

        self.btn_run.setEnabled(False)
        self.btn_open_folder.setVisible(False)
        self.prog_container.setVisible(True)
        self.workflow.set_directory(path)
        
        # Conexões
        self.workflow.progress_individual.connect(self.progress_current.setValue)
        self.workflow.progress_general.connect(self.progress_general.setValue)
        self.workflow.preview_update.connect(self.log_view.append)
        self.workflow.finished.connect(self._on_finished)
        self.workflow.start()

    def _on_finished(self, success, message):
        self.btn_run.setEnabled(True)
        self.btn_open_folder.setVisible(True)
        msg = QMessageBox(self)
        msg.setWindowTitle("Fim")
        msg.setText(f"<b>Processamento em lotes concluído</b>")
        msg.setIcon(QMessageBox.Icon.Information if success else QMessageBox.Icon.Critical)
        msg.exec()