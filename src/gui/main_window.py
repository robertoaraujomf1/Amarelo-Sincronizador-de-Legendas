import os
import json
# Alterado para PyQt6
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
                             QLabel, QTextEdit, QGroupBox, QCheckBox, QComboBox, QSpinBox,
                             QColorDialog, QListWidget, QListWidgetItem, QProgressBar,
                             QMessageBox, QFileDialog, QSplitter, QTabWidget, QLineEdit,
                             QFormLayout, QDialog, QDialogButtonBox, QScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QFont, QColor, QTextCursor, QIcon

# Mantendo seus imports de lógica
from src.core.workflow_manager import WorkflowManager
from src.core.file_matcher import find_video_subtitle_pairs
# Nota: Certifique-se que estes diálogos abaixo também foram/serão convertidos para PyQt6
from src.gui.progress_dialog import ProgressDialog
from src.gui.settings_dialog import SettingsDialog
from src.gui.theme_manager import ThemeManager
from src.utils.config_manager import ConfigManager
from src.utils.language_manager import LanguageManager

class FontSettingsDialog(QDialog):
    """Diálogo para configuração da fonte"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações da Fonte")
        self.setModal(True)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(20)
        form_layout.addRow("Tamanho da fonte:", self.font_size_spin)
        
        self.font_color_button = QPushButton("Selecionar Cor")
        self.font_color_button.clicked.connect(self.select_color)
        self.font_color = QColor(255, 255, 0) 
        form_layout.addRow("Cor da fonte:", self.font_color_button)
        
        self.bold_checkbox = QCheckBox("Negrito")
        form_layout.addRow("Estilo:", self.bold_checkbox)
        
        layout.addLayout(form_layout)
        
        # PyQt6 usa QDialogButtonBox.StandardButton
        buttons = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        button_box = QDialogButtonBox(buttons)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def select_color(self):
        color = QColorDialog.getColor(self.font_color, self)
        if color.isValid():
            self.font_color = color

class MainWindow(QMainWindow):
    """Janela principal do aplicativo"""
    
    log_signal = pyqtSignal(str)
    subtitle_signal = pyqtSignal(dict)
    progress_signal = pyqtSignal(int)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.language_manager = LanguageManager(config_manager)
        self.theme_manager = ThemeManager()
        self.workflow_manager = None
        self.worker_thread = None
        self.current_directory = "" # Inicializado
        self.font_settings = {
            'size': 20,
            'color': QColor(255, 255, 0),
            'bold': False
        }
        
        self.init_ui()
        self.load_settings()
        self.apply_theme()
        
    def init_ui(self):
        self.setWindowTitle("Amarelo Subs")
        self.resize(1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # PyQt6: Qt.Orientation.Horizontal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 800])
        main_layout.addWidget(splitter)
        
        self.status_label = QLabel("Pronto")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_bar)
        main_layout.addLayout(status_layout)
        
        self.log_signal.connect(self.update_log)
        self.subtitle_signal.connect(self.add_subtitle_preview)
        self.progress_signal.connect(self.update_progress)
        
    def create_toolbar(self):
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.select_dir_btn = QPushButton("Selecionar Diretório")
        self.select_dir_btn.clicked.connect(self.select_directory)
        layout.addWidget(self.select_dir_btn)
        
        self.font_settings_btn = QPushButton("Configurar Fonte")
        self.font_settings_btn.clicked.connect(self.show_font_settings)
        layout.addWidget(self.font_settings_btn)
        
        self.settings_btn = QPushButton("Configurações")
        self.settings_btn.clicked.connect(self.show_settings)
        layout.addWidget(self.settings_btn)
        
        self.open_output_btn = QPushButton("Abrir Saída")
        self.open_output_btn.clicked.connect(self.open_output_folder)
        layout.addWidget(self.open_output_btn)
        
        layout.addStretch()
        return toolbar

    def create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        config_group = QGroupBox("Configurações")
        config_layout = QVBoxLayout()
        
        self.dir_label = QLabel("Nenhum diretório selecionado")
        self.dir_label.setWordWrap(True)
        config_layout.addWidget(self.dir_label)
        
        self.translate_checkbox = QCheckBox("Traduzir legendas")
        self.translate_checkbox.stateChanged.connect(self.on_translate_changed)
        config_layout.addWidget(self.translate_checkbox)
        
        self.language_combo = QComboBox()
        # Adicionando itens com userData de forma compatível
        languages = [
            ("Português (Brasil)", "pt-BR"), ("Inglês (EUA)", "en-US"),
            ("Espanhol", "es-ES"), ("Francês", "fr-FR"),
            ("Alemão", "de-DE"), ("Japonês", "ja-JP"), ("Coreano", "ko-KR")
        ]
        for text, data in languages:
            self.language_combo.addItem(text, data)
            
        self.language_combo.setEnabled(False)
        config_layout.addWidget(QLabel("Idioma de destino:"))
        config_layout.addWidget(self.language_combo)
        
        self.merge_checkbox = QCheckBox("Mesclar legendas no vídeo")
        config_layout.addWidget(self.merge_checkbox)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        files_group = QGroupBox("Arquivos no Diretório")
        files_layout = QVBoxLayout()
        self.files_list = QListWidget()
        files_layout.addWidget(self.files_list)
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)
        
        self.process_btn = QPushButton("Processar")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        
        layout.addStretch()
        return panel

    def create_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        tabs = QTabWidget()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        tabs.addTab(self.log_text, "Log")
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        tabs.addTab(self.preview_text, "Pré-visualização")
        
        layout.addWidget(tabs)
        return panel

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Diretório")
        if directory:
            self.current_directory = directory
            self.dir_label.setText(f"Diretório: {directory}")
            self.scan_directory(directory)
            self.process_btn.setEnabled(True)
            
    def scan_directory(self, directory):
        self.files_list.clear()
        try:
            pairs = find_video_subtitle_pairs(directory)
            for video_path, subtitle_path in pairs:
                video_name = os.path.basename(video_path)
                status = "✓" if subtitle_path else "📹"
                sub_info = f" → {os.path.basename(subtitle_path)}" if subtitle_path else " (sem legenda)"
                
                item = QListWidgetItem(f"{status} {video_name}{sub_info}")
                # PyQt6: Qt.ItemDataRole.UserRole
                item.setData(Qt.ItemDataRole.UserRole, (video_path, subtitle_path))
                self.files_list.addItem(item)
                
            self.log_signal.emit(f"Encontrados {len(pairs)} vídeos no diretório")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao escanear: {e}")

    def show_font_settings(self):
        dialog = FontSettingsDialog(self)
        if dialog.exec(): # Removido o underscore
            self.font_settings.update({
                'size': dialog.font_size_spin.value(),
                'color': dialog.font_color,
                'bold': dialog.bold_checkbox.isChecked()
            })
            self.log_signal.emit(f"Fonte atualizada.")

    def on_translate_changed(self, state):
        # PyQt6: compara com o valor inteiro ou usa o enum
        self.language_combo.setEnabled(state == 2) # 2 é Checked

    def start_processing(self):
        if self.files_list.count() == 0: return
            
        config = {
            'directory': self.current_directory,
            'translate': self.translate_checkbox.isChecked(),
            'target_language': self.language_combo.currentData(),
            'merge': self.merge_checkbox.isChecked(),
            'font_settings': self.font_settings,
            'files': []
        }
        
        for i in range(self.files_list.count()):
            item = self.files_list.item(i)
            v_path, s_path = item.data(Qt.ItemDataRole.UserRole)
            config['files'].append({
                'video_path': v_path,
                'subtitle_path': s_path,
                'has_subtitle': bool(s_path)
            })
        
        self.worker_thread = QThread()
        self.workflow_manager = WorkflowManager(config)
        self.workflow_manager.moveToThread(self.worker_thread)
        
        self.workflow_manager.log_signal.connect(self.log_signal.emit)
        self.workflow_manager.subtitle_signal.connect(self.subtitle_signal.emit)
        self.workflow_manager.progress_signal.connect(self.progress_signal.emit)
        self.workflow_manager.finished.connect(self.on_processing_finished)
        
        self.worker_thread.started.connect(self.workflow_manager.process_all)
        self.worker_thread.start()
        
        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Processando...")

    @pyqtSlot(str)
    def update_log(self, message):
        self.log_text.append(message)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    @pyqtSlot(dict)
    def add_subtitle_preview(self, subtitle_data):
        text = f"{subtitle_data.get('start')} --> {subtitle_data.get('end')}\n"
        text += f"{subtitle_data.get('text')}\n{'-'*20}"
        self.preview_text.append(text)

    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_processing_finished(self, results):
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.process_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Concluído")
        QMessageBox.information(self, "Fim", "Processamento concluído com sucesso!")

    def open_output_folder(self):
        path = os.path.abspath("output")
        if not os.path.exists(path): os.makedirs(path)
        if os.name == 'nt': os.startfile(path)
        else: subprocess.Popen(['xdg-open', path])

    def show_settings(self):
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec(): self.load_settings()

    @pyqtSlot(str, str)
    def exibir_alerta_atualizacao(self, titulo, mensagem):
        """Slot para receber o sinal do UpdateChecker"""
        QMessageBox.information(self, titulo, mensagem)

    def load_settings(self):
        pass # Implementar lógica de carregamento se necessário

    def apply_theme(self):
        self.theme_manager.apply_theme(self)

    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(self, "Sair?", "Processo ativo. Sair mesmo assim?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if self.workflow_manager: self.workflow_manager.stop_processing = True
                self.worker_thread.quit()
                self.worker_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()