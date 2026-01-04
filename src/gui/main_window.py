import os
import sys
import time
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QMessageBox, QGroupBox, 
                             QLabel, QCheckBox, QTextEdit, QColorDialog, QComboBox,
                             QProgressBar, QScrollArea)
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtCore import Qt
from src.core.workflow_manager import WorkflowManager

class MainWindow(QMainWindow):
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.workflow = WorkflowManager(self.config)
        self.selected_color = "#f4c430"
        self.start_time = 0
        self.last_dir = ""
        
        # Configuração Básica da Janela
        self.setWindowTitle("Amarelo Subs")
        
        # Lógica do Ícone (assets/icons/app_icon.png)
        # Sobe dois níveis para sair de src/core e chegar na raiz do projeto
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        icon_path = os.path.join(base_path, "assets", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setWindowState(Qt.WindowState.WindowMaximized)
        
        # Inicialização da Interface
        self._apply_styles()
        self._setup_ui()
        self._connect_signals()

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:1 #1e293b); }
            QLabel { color: #e2e8f0; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }
            QCheckBox { color: #f4c430; font-weight: bold; }
            QComboBox { background-color: #334155; color: white; border: 1px solid #475569; border-radius: 6px; padding: 4px; }
            QTextEdit { background-color: rgba(15, 23, 42, 0.9); color: #94a3b8; border: 1px solid #334155; font-family: 'Consolas'; }
            
            QScrollArea { border: 1px solid #334155; border-radius: 8px; background-color: #1e293b; }
            #scrollContent { background-color: #1e293b; }
            
            QProgressBar { background: #0f172a; border: 1px solid #334155; border-radius: 5px; text-align: center; color: white; font-weight: bold; }
            QProgressBar::chunk { background: #4ade80; }
            #progressCurrent::chunk { background: #f4c430; }

            QScrollBar:vertical { border: none; background: #0f172a; width: 10px; border-radius: 5px; }
            QScrollBar::handle:vertical { background: #334155; min-height: 20px; border-radius: 5px; }

            QMessageBox { background-color: #1e293b; border: 1px solid #f4c430; }
            QMessageBox QLabel { color: #e2e8f0; }
            QMessageBox QPushButton { background-color: #334155; color: white; padding: 6px 20px; border-radius: 4px; }
        """)

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(30, 30, 30, 30)

        # Configurações do Projeto
        self.style_group = QGroupBox("Configurações do Projeto")
        self.style_group.setStyleSheet("QGroupBox { border: 1px solid #f4c430; border-radius: 10px; margin-top: 20px; padding-top: 15px; color: #f4c430; }")
        style_layout = QHBoxLayout()
        
        self.btn_color = QPushButton(); self.btn_color.setFixedSize(50, 35)
        self.btn_color.clicked.connect(self._select_color); self._update_btn_color()
        
        self.combo_size = QComboBox(); self.combo_size.addItems(["Pequeno", "Médio", "Grande"]); self.combo_size.setCurrentIndex(1)
        self.check_bold = QCheckBox("Negrito"); self.check_bold.setChecked(True)
        self.combo_lang = QComboBox(); self.combo_lang.addItems(["Original (Sem Tradução)", "Português", "Inglês", "Espanhol", "Francês", "Alemão", "Italiano"])
        
        style_layout.addWidget(QLabel("Cor:")); style_layout.addWidget(self.btn_color); style_layout.addSpacing(15)
        style_layout.addWidget(QLabel("Tamanho:")); style_layout.addWidget(self.combo_size); style_layout.addSpacing(20)
        style_layout.addWidget(self.check_bold); style_layout.addSpacing(20)
        style_layout.addWidget(QLabel("Traduzir para:")); style_layout.addWidget(self.combo_lang); style_layout.addStretch()
        self.style_group.setLayout(style_layout); self.main_layout.addWidget(self.style_group)

        # Fila de Vídeos
        self.video_group = QGroupBox("Fila de Processamento")
        self.video_group.setStyleSheet("QGroupBox { border: 1px solid #334155; color: #94a3b8; }")
        video_vbox = QVBoxLayout()
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget(); self.scroll_content.setObjectName("scrollContent")
        self.video_list_layout = QVBoxLayout(self.scroll_content)
        self.video_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content); video_vbox.addWidget(self.scroll_area)
        self.video_group.setLayout(video_vbox); self.main_layout.addWidget(self.video_group, stretch=1)

        # Container de Progresso e ETA
        self.prog_container = QWidget(); self.prog_container.setVisible(False)
        prog_layout = QVBoxLayout(self.prog_container)
        
        self.label_general = QLabel("Progresso Geral: 0%")
        self.progress_general = QProgressBar(); self.progress_general.setFixedHeight(22)
        
        self.label_current = QLabel("Vídeo Atual: 0%")
        self.progress_current = QProgressBar(); self.progress_current.setFixedHeight(14); self.progress_current.setObjectName("progressCurrent")
        
        self.label_eta = QLabel("Tempo restante estimado: calculando...")
        self.label_eta.setStyleSheet("color: #4ade80; font-size: 11px;")
        
        prog_layout.addWidget(self.label_general); prog_layout.addWidget(self.progress_general)
        prog_layout.addSpacing(5)
        prog_layout.addWidget(self.label_current); prog_layout.addWidget(self.progress_current)
        prog_layout.addWidget(self.label_eta)
        self.main_layout.addWidget(self.prog_container)

        # Visualização de Logs
        self.log_view = QTextEdit(); self.log_view.setReadOnly(True); self.log_view.setMaximumHeight(100)
        self.main_layout.addWidget(self.log_view)

        # Botões Inferiores
        self.bottom_layout = QHBoxLayout()
        self.btn_open_folder = QPushButton("📁 ABRIR PASTA"); self.btn_open_folder.setFixedHeight(45); self.btn_open_folder.setVisible(False)
        self.btn_open_folder.setStyleSheet("QPushButton { background: #1e293b; color: white; border: 1px solid #f4c430; border-radius: 8px; }")
        self.btn_open_folder.clicked.connect(self._open_folder)
        
        self.btn_run = QPushButton("🚀 INICIAR LEGENDAGEM"); self.btn_run.setFixedHeight(45)
        self.btn_run.setStyleSheet("QPushButton { background: #f4c430; color: #0f172a; font-weight: bold; border-radius: 8px; }")
        self.btn_run.clicked.connect(self._on_start)
        
        self.bottom_layout.addWidget(self.btn_open_folder, 1); self.bottom_layout.addWidget(self.btn_run, 2)
        self.main_layout.addLayout(self.bottom_layout)

    def _connect_signals(self):
        """Conecta os sinais da thread de trabalho à interface"""
        self.workflow.progress_individual.connect(self._update_current_ui)
        self.workflow.progress_general.connect(self._update_general_ui)
        self.workflow.preview_update.connect(self.log_view.append)
        self.workflow.finished.connect(self._on_finished)

    def _select_color(self):
        color = QColorDialog.getColor(QColor(self.selected_color))
        if color.isValid():
            self.selected_color = color.name()
            self._update_btn_color()

    def _update_btn_color(self):
        self.btn_color.setStyleSheet(f"background-color: {self.selected_color}; border-radius: 4px; border: 1px solid white;")

    def _open_folder(self):
        if self.last_dir:
            os.startfile(self.last_dir)

    def _on_start(self):
        path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if not path:
            return
        self.last_dir = path
        
        # Detectar arquivos de vídeo compatíveis
        extensions = ('.mp4', '.mkv', '.avi', '.mov')
        videos = [f for f in os.listdir(path) if f.lower().endswith(extensions)]
        if not videos:
            QMessageBox.warning(self, "Erro", "Nenhum vídeo compatível encontrado na pasta.")
            return

        # Limpar a fila visual anterior com segurança
        for i in reversed(range(self.video_list_layout.count())): 
            widget = self.video_list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Adicionar novos vídeos à fila visual
        for v in videos:
            lbl = QLabel(f" 🎥 {v}")
            lbl.setStyleSheet("color: #94a3b8; padding: 5px; border-bottom: 1px solid #334155;")
            self.video_list_layout.addWidget(lbl)

        # Mapeamento e Persistência de Configurações
        lang_map = {"Português": "pt", "Inglês": "en", "Espanhol": "es", "Francês": "fr", "Alemão": "de", "Italiano": "it"}
        choice = self.combo_lang.currentText()
        self.config.set("font.color", self.selected_color)
        self.config.set("font.bold", self.check_bold.isChecked())
        self.config.set("translation.enabled", choice != "Original (Sem Tradução)")
        self.config.set("translation.target_language", lang_map.get(choice, "pt"))

        # Reiniciar Estado da UI
        self.btn_run.setEnabled(False)
        self.btn_open_folder.setVisible(False)
        self.prog_container.setVisible(True)
        self.start_time = time.time()
        self.log_view.clear()
        
        # Sinalização inicial de 0%
        self.progress_general.setValue(0)
        self.progress_current.setValue(0)
        self.label_general.setText("Progresso Geral: 0%")
        self.label_current.setText("Vídeo Atual: Iniciando...")

        self.workflow.set_directory(path)
        self.workflow.start()

    def _update_current_ui(self, val):
        self.progress_current.setValue(val)
        self.label_current.setText(f"Vídeo Atual: {val}%")

    def _update_general_ui(self, val):
        self.progress_general.setValue(val)
        self.label_general.setText(f"Progresso Geral: {val}%")
        
        # Cálculo de ETA (Tempo Restante)
        if val > 0:
            elapsed = time.time() - self.start_time
            remaining = (elapsed / val) * (100 - val)
            mins, secs = divmod(int(remaining), 60)
            self.label_eta.setText(f"Tempo restante estimado: {mins:02d}:{secs:02d}")

    def _on_finished(self, success, message):
        self.btn_run.setEnabled(True)
        self.btn_open_folder.setVisible(True)
        if success:
            self.label_eta.setText("Processamento finalizado com sucesso.")
            QMessageBox.information(self, "Concluído", "Todas as legendas foram geradas!")
        else:
            self.label_eta.setText("O processamento foi interrompido por um erro.")
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro: {message}")