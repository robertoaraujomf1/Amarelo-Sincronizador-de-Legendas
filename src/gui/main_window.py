from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QLineEdit, QFileDialog, QProgressBar, QTextEdit,
                            QGroupBox, QComboBox, QSpinBox, QColorDialog, QMessageBox,
                            QTabWidget, QWidget, QFrame, QCheckBox, QApplication)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QPixmap, QGuiApplication, QFontDatabase, QIcon, QFontMetrics
import os
import json

from src.core.subtitle_sync import SubtitleSyncEngine
from src.gui.settings_dialog import SettingsDialog
from src.gui.style_manager import StyleManager

class SyncThread(QThread):
    progress_updated = Signal(int, str)
    finished = Signal(bool, str)
    
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

class FontComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                combobox-popup: 0;
                max-height: 200px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ccc;
                background-color: white;
                selection-background-color: #e6f3ff;
            }
        """)

class MainWindow(QMainWindow):
    def __init__(self, config, language_manager, app_icon):
        super().__init__()
        self.config = config
        self.language_manager = language_manager
        self.app_icon = app_icon
        self.sync_thread = None
        self.current_directory = ""
        
        # AUMENTAR FONTE GLOBAL
        font = self.font()
        font.setPointSize(11)
        self.setFont(font)
        
        self.setWindowTitle("Amarelo Sincronizador de Legendas")
        self.setWindowIcon(self.app_icon)
        self.setMinimumSize(900, 700)
        
        # Aplicar estilo
        self.style_manager = StyleManager()
        self.apply_styles()
        
        # Inicializar log_text antes de setup_ui
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        
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
        
        # REMOVIDO: Cabeçalho com título
        
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
        
    def create_folder_section(self):
        group = QGroupBox("Seleção de Pasta")
        layout = QVBoxLayout(group)
        
        folder_layout = QHBoxLayout()
        self.folder_path = QLineEdit()
        self.folder_path.setPlaceholderText("Selecione a pasta contendo os vídeos e legendas...")
        folder_layout.addWidget(self.folder_path)
        
        browse_btn = QPushButton()
        browse_btn.setFixedSize(120, 100)  # BOTÃO AINDA MAIOR
        # Adicionar ícone de pasta
        if os.path.exists("assets/icons/folder_icon.png"):
            pixmap = QPixmap("assets/icons/folder_icon.png")
            scaled_pixmap = pixmap.scaled(110, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            browse_btn.setIcon(QIcon(scaled_pixmap))
            browse_btn.setIconSize(QSize(110, 90))
        browse_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-radius: 10px;
            }
        """)
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)
        
        layout.addLayout(folder_layout)
        
        # Informação sobre bloqueio de arquivos (OCULTÁVEL)
        self.file_lock_frame = QFrame()
        self.file_lock_frame.setStyleSheet("""
            QFrame {
                background-color: #FFF3E0;
                border-radius: 5px;
                border: 1px solid #FFE0B2;
            }
        """)
        file_lock_layout = QVBoxLayout(self.file_lock_frame)
        file_lock_layout.setContentsMargins(10, 5, 10, 5)
        
        file_lock_header = QHBoxLayout()
        
        self.file_lock_label = QLabel(
            "⚠️ Durante a análise, os arquivos serão bloqueados para evitar modificações. "
            "Não mova, renomeie ou exclua arquivos até que a análise seja concluída."
        )
        self.file_lock_label.setWordWrap(True)
        self.file_lock_label.setStyleSheet("color: #FF6B35; font-size: 12px;")
        file_lock_header.addWidget(self.file_lock_label)
        
        # Botão para ocultar/mostrar o aviso
        self.hide_lock_btn = QPushButton("✕")
        self.hide_lock_btn.setFixedSize(24, 24)
        self.hide_lock_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #FF6B35;
                color: #FF6B35;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF6B35;
                color: white;
            }
        """)
        self.hide_lock_btn.clicked.connect(self.toggle_file_lock_warning)
        file_lock_header.addWidget(self.hide_lock_btn)
        
        file_lock_layout.addLayout(file_lock_header)
        layout.addWidget(self.file_lock_frame)
        
        return group
    
    def create_subtitle_settings(self):
        group = QGroupBox("Configurações de Legenda")
        layout = QVBoxLayout(group)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Fonte
        font_layout = QHBoxLayout()
        font_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font_layout.addWidget(QLabel("Fonte:"))
        
        # Usar o novo FontComboBox customizado
        self.font_combo = FontComboBox()
        self.font_combo.setMinimumWidth(250)
        self.font_combo.setMaxVisibleItems(15)
        
        # Carregar TODAS as fontes do sistema
        self.load_system_fonts()
        
        font_layout.addWidget(self.font_combo)
        
        font_layout.addWidget(QLabel("Tamanho:"))
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        self.font_size.setValue(16)
        font_layout.addWidget(self.font_size)
        
        # Botão para Negrito - "N" em negrito (toggle button)
        self.bold_button = QPushButton("N")
        self.bold_button.setCheckable(True)  # Torna o botão um toggle button
        self.bold_button.setFixedSize(40, 30)
        
        # Usar a mesma fonte global do aplicativo (já configurada como size 11)
        app_font = self.font()
        bold_font = QFont(app_font)
        bold_font.setBold(True)
        self.bold_button.setFont(bold_font)
        
        # Estilo para o botão de negrito
        self.bold_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: #0078d4;
                color: white;
                border: 1px solid #005a9e;
            }
            QPushButton:checked:hover {
                background-color: #106ebe;
            }
        """)
        
        # Tooltip para explicar que é negrito - com fonte maior
        self.bold_button.setToolTip("<span style='font-size: 11pt; font-weight: bold;'>Negrito</span>")
        font_layout.addWidget(self.bold_button)
        
        font_layout.addWidget(QLabel("Cor:"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(30, 30)
        self.color_btn.setStyleSheet("background-color: #FFFFFF; border: 1px solid #ccc;")
        self.color_btn.clicked.connect(self.choose_color)
        font_layout.addWidget(self.color_btn)
        
        layout.addLayout(font_layout)
        
        # Preview da fonte
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(QLabel("Preview:"))
        self.font_preview_label = QLabel("AaBbCc 123 @#$")
        self.font_preview_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px;
                border-radius: 4px;
                min-width: 200px;
            }
        """)
        preview_layout.addWidget(self.font_preview_label)
        preview_layout.addStretch()
        layout.addLayout(preview_layout)
        
        # Conectar sinais para atualizar o preview
        self.font_combo.currentTextChanged.connect(self.update_font_preview)
        self.font_size.valueChanged.connect(self.on_font_size_changed)
        self.bold_button.toggled.connect(self.on_bold_toggled)
        
        # Informações sobre formatação (OCULTÁVEL)
        self.format_info_frame = QFrame()
        self.format_info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #dee2e6;
            }
        """)
        format_info_layout = QVBoxLayout(self.format_info_frame)
        format_info_layout.setContentsMargins(10, 5, 10, 5)
        
        format_info_header = QHBoxLayout()
        
        self.format_info_label = QLabel(
            "📝 As legendas serão centralizadas na parte inferior. "
            "Cada bloco terá no máximo 2 linhas e respeitará as margens da tela."
        )
        self.format_info_label.setWordWrap(True)
        self.format_info_label.setStyleSheet("color: #666; font-size: 12px;")
        format_info_header.addWidget(self.format_info_label)
        
        # Botão para ocultar/mostrar o aviso
        self.hide_format_btn = QPushButton("✕")
        self.hide_format_btn.setFixedSize(24, 24)
        self.hide_format_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #666;
                color: #666;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #666;
                color: white;
            }
        """)
        self.hide_format_btn.clicked.connect(self.toggle_format_info)
        format_info_header.addWidget(self.hide_format_btn)
        
        format_info_layout.addLayout(format_info_header)
        layout.addWidget(self.format_info_frame)
        
        return group
    
    def toggle_file_lock_warning(self):
        """Alterna a visibilidade do aviso sobre bloqueio de arquivos"""
        is_visible = self.file_lock_frame.isVisible()
        self.file_lock_frame.setVisible(not is_visible)
        
        # Salvar preferência
        self.config.set_setting('show_file_lock_warning', not is_visible)
        
        # Atualizar texto do botão
        self.hide_lock_btn.setText("✕" if not is_visible else "↻")
        if not is_visible:
            self.hide_lock_btn.setToolTip("Ocultar aviso")
        else:
            self.hide_lock_btn.setToolTip("Mostrar aviso")
    
    def toggle_format_info(self):
        """Alterna a visibilidade da informação sobre formatação"""
        is_visible = self.format_info_frame.isVisible()
        self.format_info_frame.setVisible(not is_visible)
        
        # Salvar preferência
        self.config.set_setting('show_format_info', not is_visible)
        
        # Atualizar texto do botão
        self.hide_format_btn.setText("✕" if not is_visible else "↻")
        if not is_visible:
            self.hide_format_btn.setToolTip("Ocultar informação")
        else:
            self.hide_format_btn.setToolTip("Mostrar informação")
    
    def load_system_fonts(self):
        """Carrega TODAS as fontes do sistema e as exibe com sua aparência real"""
        try:
            # Obter todas as famílias de fontes do sistema
            font_database = QFontDatabase()
            all_font_families = font_database.families()
            
            # Ordenar as fontes alfabeticamente
            sorted_fonts = sorted(all_font_families)
            
            self.font_combo.clear()
            
            # Adicionar cada fonte com sua aparência real
            for font_family in sorted_fonts:
                # Verificar se a fonte tem suporte a caracteres latinos básicos
                if self.has_latin_support(font_family):
                    self.font_combo.addItem(font_family)
                    
                    # Definir a fonte para o item (ícone no combobox)
                    index = self.font_combo.count() - 1
                    self.font_combo.setItemData(index, QFont(font_family, 10), Qt.ItemDataRole.FontRole)
            
            # Se não conseguiu carregar fontes, usar fallback
            if self.font_combo.count() == 0:
                self.load_fallback_fonts()
                
            # Usar messagebox em vez de log_text que pode não estar pronto
            if hasattr(self, 'log_text') and self.log_text:
                self.log_text.append(f"✅ Carregadas {self.font_combo.count()} fontes do sistema")
            
        except Exception as e:
            # Usar messagebox em caso de erro durante inicialização
            if hasattr(self, 'log_text') and self.log_text:
                self.log_text.append(f"❌ Erro ao carregar fontes: {str(e)}")
            self.load_fallback_fonts()
    
    def has_latin_support(self, font_family):
        """Verifica se a fonte tem suporte a caracteres latinos básicos"""
        try:
            # Criar fonte de teste
            test_font = QFont(font_family, 10)
            test_font_metrics = QFontMetrics(test_font)
            
            # Testar com caracteres latinos básicos
            test_string = "AaBbCc"
            
            # Se a fonte não suportar os caracteres, retornará uma métrica diferente
            # ou largura zero para alguns caracteres
            width = test_font_metrics.horizontalAdvance(test_string)
            
            # Se a largura for zero ou muito pequena, a fonte provavelmente não suporta latim
            return width > 20
            
        except:
            return True  # Em caso de erro, assume que tem suporte
    
    def load_fallback_fonts(self):
        """Carrega fontes fallback caso não consiga obter as do sistema"""
        fallback_fonts = [
            "Arial", "Segoe UI", "Times New Roman", "Verdana", "Tahoma",
            "Calibri", "Microsoft Sans Serif", "Courier New", "Georgia",
            "Impact", "Comic Sans MS", "Trebuchet MS", "Arial Black",
            "Palatino Linotype", "Lucida Sans Unicode", "Franklin Gothic Medium"
        ]
        
        for font in fallback_fonts:
            self.font_combo.addItem(font)
            index = self.font_combo.count() - 1
            self.font_combo.setItemData(index, QFont(font, 10), Qt.ItemDataRole.FontRole)
    
    def update_font_preview(self, font_family=None):
        """Atualiza o preview da fonte selecionada"""
        try:
            if font_family is None:
                font_family = self.font_combo.currentText()
            
            font_size = self.font_size.value()
            preview_font = QFont(font_family, font_size)
            
            # Aplicar negrito se o botão estiver pressionado
            if self.bold_button.isChecked():
                preview_font.setBold(True)
            else:
                preview_font.setBold(False)
            
            self.font_preview_label.setFont(preview_font)
            
            # Atualizar também a cor se estiver definida
            current_style = self.font_preview_label.styleSheet()
            if "color:" in current_style:
                # Manter a cor atual se existir
                pass
            else:
                # Definir cor padrão para contraste
                self.font_preview_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: #f8f9fa;
                        border: 1px solid #dee2e6;
                        padding: 8px;
                        border-radius: 4px;
                        min-width: 200px;
                        color: #000000;
                    }}
                """)
                
        except Exception as e:
            # Em caso de erro, usar fonte padrão
            default_font = QFont("Arial", self.font_size.value())
            if self.bold_button.isChecked():
                default_font.setBold(True)
            self.font_preview_label.setFont(default_font)
    
    def on_font_size_changed(self):
        """Atualiza o preview quando o tamanho da fonte muda"""
        self.update_font_preview()
    
    def on_bold_toggled(self):
        """Atualiza o preview quando o negrito é alterado"""
        self.update_font_preview()
    
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
        
        # self.log_text já foi criado no __init__, apenas adicionar ao layout
        layout.addWidget(self.log_text)
        
        return group
    
    def create_action_buttons(self):
        layout = QHBoxLayout()
        
        self.sync_btn = QPushButton()
        self.sync_btn.setFixedSize(180, 140)  # BOTÃO AINDA MAIOR
        # Adicionar ícone de sincronização
        if os.path.exists("assets/icons/sync_icon.png"):
            pixmap = QPixmap("assets/icons/sync_icon.png")
            scaled_pixmap = pixmap.scaled(170, 130, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.sync_btn.setIcon(QIcon(scaled_pixmap))
            self.sync_btn.setIconSize(QSize(170, 130))
        self.sync_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-radius: 15px;
            }
            QPushButton:disabled {
                background-color: #f0f0f0;
            }
        """)
        self.sync_btn.clicked.connect(self.start_sync)
        
        settings_btn = QPushButton()
        settings_btn.setFixedSize(160, 120)  # BOTÃO AINDA MAIOR
        # Adicionar ícone de configurações
        if os.path.exists("assets/icons/settings_icon.png"):
            pixmap = QPixmap("assets/icons/settings_icon.png")
            scaled_pixmap = pixmap.scaled(150, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            settings_btn.setIcon(QIcon(scaled_pixmap))
            settings_btn.setIconSize(QSize(150, 110))
        settings_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-radius: 10px;
            }
        """)
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
            recent_folders = recent_folders[:5]
            self.config.set_setting('recent_folders', recent_folders)
    
    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #ccc;")
            # Atualizar também o preview da fonte com a nova cor
            self.update_font_preview_color(color.name())
    
    def update_font_preview_color(self, color):
        """Atualiza a cor do texto no preview da fonte"""
        current_style = self.font_preview_label.styleSheet()
        # Manter o estilo existente, mas atualizar a cor
        new_style = f"""
            QLabel {{
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px;
                border-radius: 4px;
                min-width: 200px;
                color: {color};
            }}
        """
        self.font_preview_label.setStyleSheet(new_style)
    
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
            'bold': self.bold_button.isChecked(),
            'font_color': self.color_btn.styleSheet().split('background-color: ')[1].split(';')[0]
        }
        
        # Salvar configurações
        self.config.set_setting('font_family', subtitle_settings['font_family'])
        self.config.set_setting('font_size', subtitle_settings['font_size'])
        self.config.set_setting('font_bold', subtitle_settings['bold'])
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
            self.load_settings()
    
    def load_settings(self):
        font_family = self.config.get_setting('font_family', 'Arial')
        font_size = self.config.get_setting('font_size', 16)
        font_bold = self.config.get_setting('font_bold', False)
        font_color = self.config.get_setting('font_color', '#FFFFFF')
        
        self.font_combo.setCurrentText(font_family)
        self.font_size.setValue(font_size)
        self.bold_button.setChecked(font_bold)
        self.color_btn.setStyleSheet(f"background-color: {font_color}; border: 1px solid #ccc;")
        
        # Carregar preferências de visibilidade dos avisos
        show_file_lock_warning = self.config.get_setting('show_file_lock_warning', True)
        show_format_info = self.config.get_setting('show_format_info', True)
        
        self.file_lock_frame.setVisible(show_file_lock_warning)
        self.format_info_frame.setVisible(show_format_info)
        
        # Atualizar textos dos botões
        self.hide_lock_btn.setText("✕" if show_file_lock_warning else "↻")
        self.hide_lock_btn.setToolTip("Ocultar aviso" if show_file_lock_warning else "Mostrar aviso")
        
        self.hide_format_btn.setText("✕" if show_format_info else "↻")
        self.hide_format_btn.setToolTip("Ocultar informação" if show_format_info else "Mostrar informação")
        
        # Atualizar preview com as configurações carregadas
        self.update_font_preview(font_family)
        self.update_font_preview_color(font_color)
    
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