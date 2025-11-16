from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QLineEdit, QFileDialog, QProgressBar, QTextEdit,
                            QGroupBox, QComboBox, QSpinBox, QColorDialog, QMessageBox,
                            QTabWidget, QWidget, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QGuiApplication
import os
import json

from src.core.subtitle_sync import SubtitleSyncEngine
from src.gui.settings_dialog import SettingsDialog
from src.gui.style_manager import StyleManager

class SyncThread(QThread):
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, directory, subtitle_settings):
        super().__init__()
        self.directory = directory
        self.subtitle_settings = subtitle_settings
        self.sync_engine = SubtitleSyncEngine()
        
    def run(self):
        try:
            self.progress_updated.emit(0, "Iniciando análise...")
            
            # Encontrar pares de vídeo e legenda
            pairs = self.sync_engine.find_video_subtitle_pairs(self.directory)
            
            total_pairs = len(pairs)
            if total_pairs == 0:
                self.finished.emit(False, "Nenhum par vídeo-legenda encontrado.")
                return
            
            for i, (video_path, subtitle_path) in enumerate(pairs):
                progress = int((i / total_pairs) * 100)
                self.progress_updated.emit(
                    progress,
                    f"Analisando: {os.path.basename(video_path)}"
                )
                
                # Analisar e sincronizar
                result = self.sync_engine.analyze_and_sync(
                    video_path, 
                    subtitle_path, 
                    self.subtitle_settings
                )
                
                if not result:
                    self.progress_updated.emit(
                        progress,
                        f"Erro ao sincronizar: {os.path.basename(video_path)}"
                    )
            
            self.progress_updated.emit(100, "Análise concluída!")
            self.finished.emit(True, "Sincronização concluída com sucesso!")
            
        except Exception as e:
            self.finished.emit(False, f"Erro durante a sincronização: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self, config, language_manager):
        super().__init__()
        self.config = config
        self.language_manager = language_manager
        self.sync_thread = None
        self.current_directory = ""
        
        self.setWindowTitle("Amarelo Sincronizador de Legendas")
        self.setMinimumSize(900, 700)
        
        # Aplicar estilo
        self.style_manager = StyleManager()
        self.apply_styles()
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Cabeçalho com logo e título
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)
        
        # Seção de seleção de pasta
        folder_section = self.create_folder_section()
        main_layout.addWidget(folder_section)
        
        # Configurações de legenda
        subtitle_settings = self.create_subtitle_settings()
        main_layout.addWidget(subtitle_settings)
        
        # Progresso
        progress_section = self.create_progress_section()
        main_layout.addWidget(progress_section)
        
        # Log
        log_section = self.create_log_section()
        main_layout.addWidget(log_section)
        
        # Botões de ação
        button_layout = self.create_action_buttons()
        main_layout.addLayout(button_layout)
        
    def create_header(self):
        layout = QHBoxLayout()
        
        # Logo/Ícone
        icon_label = QLabel()
        if os.path.exists("assets/icons/app_icon.png"):
            pixmap = QPixmap("assets/icons/app_icon.png")
            icon_label.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
        layout.addWidget(icon_label)
        
        # Título
        title_label = QLabel("Amarelo Sincronizador de Legendas")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #FF9800;")
        layout.addWidget(title_label)
        layout.addStretch()
        
        return layout
    
    def create_folder_section(self):
        group = QGroupBox("Seleção de Pasta")
        layout = QVBoxLayout(group)
        
        folder_layout = QHBoxLayout()
        self.folder_path = QLineEdit()
        self.folder_path.setPlaceholderText("Selecione a pasta contendo os vídeos e legendas...")
        folder_layout.addWidget(self.folder_path)
        
        browse_btn = QPushButton("Procurar...")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)
        
        layout.addLayout(folder_layout)
        
        # Informação sobre bloqueio de arquivos
        info_label = QLabel(
            "⚠️ Durante a análise, os arquivos serão bloqueados para evitar modificações. "
            "Não mova, renomeie ou exclua arquivos até que a análise seja concluída."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #FF6B35; background-color: #FFF3E0; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)
        
        return group
    
    def create_subtitle_settings(self):
        group = QGroupBox("Configurações de Legenda")
        layout = QVBoxLayout(group)
        
        # Fonte
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Fonte:"))
        self.font_combo = QComboBox()
        
        # Obter fontes do sistema
        font_database = QGuiApplication.fontDatabase()
        system_fonts = font_database.families()
        common_fonts = ["Arial", "Segoe UI", "Times New Roman", "Verdana", "Tahoma", 
                       "Calibri", "Microsoft Sans Serif", "Courier New"]
        
        for font in common_fonts:
            if font in system_fonts:
                self.font_combo.addItem(font)
        
        if self.font_combo.count() == 0 and system_fonts:
            for font in system_fonts[:10]:  # Limitar a 10 fontes
                self.font_combo.addItem(font)
        
        font_layout.addWidget(self.font_combo)
        
        font_layout.addWidget(QLabel("Tamanho:"))
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        self.font_size.setValue(16)
        font_layout.addWidget(self.font_size)
        
        font_layout.addWidget(QLabel("Cor:"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(30, 30)
        self.color_btn.setStyleSheet("background-color: #FFFFFF; border: 1px solid #ccc;")
        self.color_btn.clicked.connect(self.choose_color)
        font_layout.addWidget(self.color_btn)
        
        layout.addLayout(font_layout)
        
        # Informações sobre formatação
        format_info = QLabel(
            "📝 As legendas serão centralizadas na parte inferior. "
            "Cada bloco terá no máximo 2 linhas e respeitará as margens da tela."
        )
        format_info.setWordWrap(True)
        format_info.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        layout.addWidget(format_info)
        
        return group
    
    def create_progress_section(self):
        group = QGroupBox("Progresso da Análise")
        layout = QVBoxLayout(group)
        
        self.status_label = QLabel("Status: Parado")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return group
    
    def create_log_section(self):
        group = QGroupBox("Log de Atividades")
        layout = QVBoxLayout(group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        return group
    
    def create_action_buttons(self):
        layout = QHBoxLayout()
        
        self.sync_btn = QPushButton("Iniciar Sincronização")
        self.sync_btn.clicked.connect(self.start_sync)
        self.sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        settings_btn = QPushButton("Configurações")
        settings_btn.clicked.connect(self.open_settings)
        
        layout.addWidget(self.sync_btn)
        layout.addStretch()
        layout.addWidget(settings_btn)
        
        return layout
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if folder:
            self.folder_path.setText(folder)
            self.current_directory = folder
            
            # Salvar pasta recente
            recent_folders = self.config.get_setting('recent_folders', [])
            if folder in recent_folders:
                recent_folders.remove(folder)
            recent_folders.insert(0, folder)
            recent_folders = recent_folders[:5]  # Manter apenas as 5 mais recentes
            self.config.set_setting('recent_folders', recent_folders)
    
    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #ccc;")
    
    def start_sync(self):
        if not self.current_directory:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma pasta primeiro.")
            return
        
        if not os.path.exists(self.current_directory):
            QMessageBox.critical(self, "Erro", "A pasta selecionada não existe.")
            return
        
        # Configurações de legenda
        subtitle_settings = {
            'font_family': self.font_combo.currentText(),
            'font_size': self.font_size.value(),
            'font_color': self.color_btn.styleSheet().split('background-color: ')[1].split(';')[0]
        }
        
        # Salvar configurações
        self.config.set_setting('font_family', subtitle_settings['font_family'])
        self.config.set_setting('font_size', subtitle_settings['font_size'])
        self.config.set_setting('font_color', subtitle_settings['font_color'])
        
        # Iniciar thread de sincronização
        self.sync_thread = SyncThread(self.current_directory, subtitle_settings)
        self.sync_thread.progress_updated.connect(self.update_progress)
        self.sync_thread.finished.connect(self.sync_finished)
        
        self.sync_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Status: Análise e correções em andamento...")
        
        self.log_text.append("Iniciando análise de sincronização...")
        self.sync_thread.start()
    
    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(f"Status: {message}")
        if message:
            self.log_text.append(message)
    
    def sync_finished(self, success, message):
        self.sync_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("Status: Análise concluída")
            self.log_text.append("✅ " + message)
            QMessageBox.information(self, "Concluído", message)
        else:
            self.status_label.setText("Status: Erro na análise")
            self.log_text.append("❌ " + message)
            QMessageBox.critical(self, "Erro", message)
    
    def open_settings(self):
        dialog = SettingsDialog(self.config, self.language_manager, self)
        if dialog.exec():
            # Recarregar configurações
            self.load_settings()
    
    def load_settings(self):
        # Carregar configurações salvas
        font_family = self.config.get_setting('font_family', 'Arial')
        font_size = self.config.get_setting('font_size', 16)
        font_color = self.config.get_setting('font_color', '#FFFFFF')
        
        self.font_combo.setCurrentText(font_family)
        self.font_size.setValue(font_size)
        self.color_btn.setStyleSheet(f"background-color: {font_color}; border: 1px solid #ccc;")
    
    def apply_styles(self):
        self.style_manager.apply_style(self, 'main')
    
    def closeEvent(self, event):
        if self.sync_thread and self.sync_thread.isRunning():
            reply = QMessageBox.question(
                self, 'Confirmação',
                'A sincronização ainda está em andamento. Deseja realmente fechar?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.sync_thread.terminate()
                self.sync_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()