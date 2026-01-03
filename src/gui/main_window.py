import os
import sys
import time
import subprocess
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QMessageBox, QGroupBox, 
                             QLabel, QCheckBox, QTextEdit, QColorDialog, QComboBox,
                             QProgressBar, QScrollArea, QFrame)
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
        self.video_start_time = 0
        self.last_output_path = ""
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.paint_icon_path = os.path.join(base_dir, "assets", "icons", "paint.png")
        
        self.setWindowTitle("Amarelo Subs")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        
        self._apply_styles()
        self._setup_ui()

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:1 #1e293b); }
            QLabel { color: #e2e8f0; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }
            QCheckBox { color: #f4c430; font-weight: bold; }
            QComboBox { background-color: #334155; color: white; border: 1px solid #475569; border-radius: 6px; padding: 4px; min-width: 100px; }
            QTextEdit { background-color: rgba(15, 23, 42, 0.9); color: #94a3b8; border: 1px solid #334155; font-family: 'Consolas'; font-size: 11px; }
            
            QScrollArea { border: 1px solid #334155; border-radius: 8px; background-color: #1e293b; }
            #scrollContent { background-color: #1e293b; } 
            
            QScrollBar:vertical { border: none; background: #0f172a; width: 10px; margin: 0px; }
            QScrollBar::handle:vertical { background: #334155; min-height: 20px; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

            /* Estilo para as caixas de mensagem (Popups) */
            QMessageBox { background-color: #1e293b; }
            QMessageBox QLabel { color: #e2e8f0; font-family: 'Segoe UI'; }
            QMessageBox QPushButton { background-color: #334155; color: white; border-radius: 4px; padding: 5px 15px; min-width: 70px; border: 1px solid #475569; }
            QMessageBox QPushButton:hover { background-color: #f4c430; color: #0f172a; }
        """)

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(15)

        # --- CONFIGURAÇÕES SUPERIORES ---
        self.style_group = QGroupBox("Configurações do Projeto")
        self.style_group.setStyleSheet("QGroupBox { border: 1px solid #f4c430; border-radius: 10px; margin-top: 20px; padding-top: 15px; color: #f4c430; }")
        
        style_layout = QHBoxLayout()
        
        self.btn_color = QPushButton()
        if os.path.exists(self.paint_icon_path):
            self.btn_color.setIcon(QIcon(self.paint_icon_path))
            self.btn_color.setIconSize(QSize(20, 20))
        self.btn_color.setFixedSize(50, 35)
        self.btn_color.clicked.connect(self._select_color)
        self._update_btn_color()

        self.combo_size = QComboBox()
        self.combo_size.addItems(["Pequeno", "Médio", "Grande"])
        self.combo_size.setCurrentIndex(1)

        # Negrito posicionado antes de traduzir para
        self.check_bold = QCheckBox("Negrito")
        self.check_bold.setChecked(True)

        self.combo_lang = QComboBox()
        self.combo_lang.addItems([
            "Original (Sem Tradução)", "Português", "Inglês", 
            "Espanhol", "Francês", "Alemão", "Italiano"
        ])
        self.combo_lang.setFixedWidth(180)

        style_layout.addWidget(QLabel("Cor:"))
        style_layout.addWidget(self.btn_color)
        style_layout.addSpacing(15)
        style_layout.addWidget(QLabel("Tamanho:"))
        style_layout.addWidget(self.combo_size)
        style_layout.addSpacing(20)
        style_layout.addWidget(self.check_bold) # <--- Ordem corrigida
        style_layout.addSpacing(20)
        style_layout.addWidget(QLabel("Traduzir para:"))
        style_layout.addWidget(self.combo_lang)
        style_layout.addStretch()
        self.style_group.setLayout(style_layout)
        self.main_layout.addWidget(self.style_group)

        # --- PAINEL DE VÍDEOS ENCONTRADOS ---
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

        # --- PROGRESSO ---
        self.prog_container = QWidget()
        self.prog_container.setVisible(False)
        prog_layout = QVBoxLayout(self.prog_container)

        self.progress_general = QProgressBar()
        self.progress_general.setFixedHeight(22)
        self.progress_general.setFormat("PROCESSO GERAL: %p% CONCLUÍDO")
        self.progress_general.setStyleSheet("""
            QProgressBar { background: #0f172a; border: 1px solid #334155; border-radius: 5px; text-align: center; color: white; font-weight: bold; }
            QProgressBar::chunk { background: #4ade80; }
        """)
        self.eta_total_label = QLabel("Tempo total restante: calculando...")
        self.eta_total_label.setStyleSheet("color: #4ade80; font-size: 12px; font-weight: bold;")

        self.progress_current = QProgressBar()
        self.progress_current.setFixedHeight(12)
        self.progress_current.setFormat("VÍDEO ATUAL: %p%")
        self.progress_current.setStyleSheet("QProgressBar { background: #0f172a; border-radius: 4px; text-align: center; color: white; font-size: 9px; } QProgressBar::chunk { background: #f4c430; }")
        
        prog_layout.addWidget(self.progress_general)
        prog_layout.addWidget(self.eta_total_label)
        prog_layout.addSpacing(5)
        prog_layout.addWidget(self.progress_current)
        self.main_layout.addWidget(self.prog_container)

        # Logs
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(100)
        self.main_layout.addWidget(self.log_view)

        # --- BOTÕES DE AÇÃO ---
        self.action_layout = QHBoxLayout()
        
        self.btn_open_folder = QPushButton(" ABRIR PASTA RESULTANTE")
        self.btn_open_folder.setFixedHeight(50)
        self.btn_open_folder.setVisible(False) 
        self.btn_open_folder.setStyleSheet("QPushButton { background: #334155; color: white; font-weight: bold; border-radius: 8px; border: 1px solid #f4c430; } QPushButton:hover { background: #475569; }")
        self.btn_open_folder.clicked.connect(self._open_result_folder)
        
        self.btn_run = QPushButton(" INICIAR LEGENDAGEM")
        self.btn_run.setFixedHeight(50)
        self.btn_run.setStyleSheet("QPushButton { background: #f4c430; color: #0f172a; font-weight: bold; font-size: 14px; border-radius: 8px; } QPushButton:hover { background: #fde047; }")
        self.btn_run.clicked.connect(self._on_start)
        
        self.action_layout.addWidget(self.btn_open_folder, 1)
        self.action_layout.addWidget(self.btn_run, 2)
        self.main_layout.addLayout(self.action_layout)

    def _select_color(self):
        color = QColorDialog.getColor(QColor(self.selected_color))
        if color.isValid():
            self.selected_color = color.name()
            self._update_btn_color()

    def _update_btn_color(self):
        self.btn_color.setStyleSheet(f"QPushButton {{ background-color: {self.selected_color}; border: 1px solid white; border-radius: 4px; }}")

    def _clear_video_list(self):
        while self.video_list_layout.count():
            item = self.video_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _update_current_progress(self, val):
        self.progress_current.setValue(val)

    def _update_general_progress(self, val):
        self.progress_general.setValue(val)
        if val > 0:
            elapsed = time.time() - self.total_start_time
            remaining = ((elapsed / val) * 100) - elapsed
            m, s = divmod(int(remaining), 60)
            h, m = divmod(m, 60)
            t_str = f"{h:02d}h {m:02d}m {s:02d}s" if h > 0 else f"{m:02d}:{s:02d}"
            self.eta_total_label.setText(f"Tempo total restante: {t_str}")

    def _open_result_folder(self):
        if self.last_output_path and os.path.exists(self.last_output_path):
            if sys.platform == 'win32':
                os.startfile(self.last_output_path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', self.last_output_path])
            else:
                subprocess.Popen(['xdg-open', self.last_output_path])

    def _on_start(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if not dir_path: return

        self.last_output_path = dir_path
        self._clear_video_list()
        videos = [f for f in os.listdir(dir_path) if f.lower().endswith(('.mp4', '.mkv', '.mov'))]
        
        if not videos:
            QMessageBox.warning(self, "Erro", "Nenhum vídeo encontrado.")
            return

        for v in videos:
            lbl = QLabel(f"  • {v}")
            lbl.setStyleSheet("color: #e2e8f0; font-size: 12px; padding: 2px;")
            self.video_list_layout.addWidget(lbl)

        self.prog_container.setVisible(True)
        self.btn_run.setEnabled(False)
        self.btn_open_folder.setVisible(False)
        self.total_start_time = time.time()
        self.video_start_time = time.time()
        
        # MAPEAMENTO PARA O SEU CONFIG_MANAGER (CHAVES COM PONTOS)
        lang_choice = self.combo_lang.currentText()
        is_translation = lang_choice != "Original (Sem Tradução)"
        
        lang_map = {
            "Português": "pt",
            "Inglês": "en",
            "Espanhol": "es",
            "Francês": "fr",
            "Alemão": "de",
            "Italiano": "it"
        }
        
        # Salvando usando o padrão k.k do seu ConfigManager
        self.config.set("font.color", self.selected_color)
        self.config.set("font.bold", self.check_bold.isChecked())
        self.config.set("font.size_label", self.combo_size.currentText())
        
        # Ativa a tradução no config e define o idioma alvo
        self.config.set("translation.enabled", is_translation)
        if is_translation:
            self.config.set("translation.target_language", lang_map.get(lang_choice, "pt"))

        self.workflow.set_directory(dir_path)

        try:
            self.workflow.progress_individual.disconnect()
            self.workflow.progress_general.disconnect()
            self.workflow.preview_update.disconnect()
            self.workflow.finished.disconnect()
        except: pass

        self.workflow.progress_individual.connect(self._update_current_progress)
        self.workflow.progress_general.connect(self._update_general_progress)
        self.workflow.preview_update.connect(self.log_view.append)
        self.workflow.finished.connect(self._on_finished)
        
        self.workflow.start()

    def _on_finished(self, success, message):
        self.prog_container.setVisible(False)
        self.btn_run.setEnabled(True)
        self.btn_open_folder.setVisible(True) 
        
        # Pop-up Customizado com Estilo Azul
        msg = QMessageBox(self)
        msg.setWindowTitle("Fim")
        msg.setText(f"<b>Processamento em lotes concluído</b><br><br>{message}")
        msg.setIcon(QMessageBox.Icon.Information if success else QMessageBox.Icon.Critical)
        msg.exec()