# src/gui/main_window.py - VERSÃO COMPLETA E FUNCIONAL
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QLineEdit, QFileDialog, QProgressBar, QTextEdit,
                            QGroupBox, QComboBox, QSpinBox, QColorDialog, QMessageBox,
                            QTabWidget, QWidget, QFrame, QCheckBox, QApplication,
                            QRadioButton, QButtonGroup, QDialog, QDialogButtonBox,
                            QFormLayout)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QPixmap, QGuiApplication, QFontDatabase, QIcon, QFontMetrics
import os
import json

from src.core.subtitle_sync import SubtitleSyncEngine
from src.gui.settings_dialog import SettingsDialog
from src.gui.style_manager import StyleManager
from src.gui.theme_manager import apply_dark_theme


class LanguageDialog(QDialog):
    """Diálogo para seleção de idioma quando não há legenda"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleção de Idioma")
        self.setModal(True)
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        # Label informativo
        info_label = QLabel(
            "Nenhuma legenda encontrada para os vídeos.\n"
            "Selecione o idioma para gerar legendas:"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Combobox de idiomas
        form_layout = QFormLayout()
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            "Português (Brasil)",
            "Português (Portugal)", 
            "Inglês (EUA)",
            "Inglês (Reino Unido)",
            "Espanhol",
            "Francês",
            "Alemão",
            "Italiano",
            "Japonês"
        ])
        form_layout.addRow("Idioma:", self.language_combo)
        layout.addLayout(form_layout)
        
        # Botões
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_selected_language(self):
        """Retorna o código do idioma selecionado"""
        language_map = {
            "Português (Brasil)": "pt-BR",
            "Português (Portugal)": "pt-PT", 
            "Inglês (EUA)": "en-US",
            "Inglês (Reino Unido)": "en-GB",
            "Espanhol": "es-ES",
            "Francês": "fr-FR",
            "Alemão": "de-DE",
            "Italiano": "it-IT",
            "Japonês": "ja-JP"
        }
        current_text = self.language_combo.currentText()
        return language_map.get(current_text, "pt-BR")


class SyncThread(QThread):
    progress_updated = Signal(int, str)
    finished = Signal(bool, str)
    
    def __init__(self, directory, subtitle_settings, target_language=None):
        super().__init__()
        self.directory = directory
        self.subtitle_settings = subtitle_settings
        self.target_language = target_language
        self.sync_engine = SubtitleSyncEngine()
        
    def run(self):
        try:
            self.progress_updated.emit(0, "Iniciando análise...")
            
            # Encontrar pares de vídeo e legenda
            pairs = self.sync_engine.find_video_subtitle_pairs(self.directory)
            
            total_pairs = len(pairs)
            if total_pairs == 0:
                self.finished.emit(False, "Nenhum vídeo encontrado no diretório.")
                return
            
            # Adicionar idioma alvo às configurações
            if self.target_language:
                self.subtitle_settings['target_language'] = self.target_language
            
            # Contadores para estatísticas
            processed = 0
            with_subtitles = 0
            generated = 0
            synced = 0
            errors = 0
            
            for i, (video_path, subtitle_path) in enumerate(pairs):
                progress = int((i / total_pairs) * 100)
                self.progress_updated.emit(
                    progress,
                    f"Processando: {os.path.basename(video_path)}"
                )
                
                # Analisar e sincronizar/gerar legenda
                result = self.sync_engine.analyze_and_sync(
                    video_path, 
                    subtitle_path, 
                    self.subtitle_settings
                )
                
                if result:
                    processed += 1
                    if subtitle_path:
                        with_subtitles += 1
                        # Verificar se foi sincronizada
                        self.progress_updated.emit(
                            progress,
                            f"Legenda sincronizada: {os.path.basename(video_path)}"
                        )
                        synced += 1
                    else:
                        generated += 1
                        self.progress_updated.emit(
                            progress,
                            f"Legenda gerada: {os.path.basename(video_path)}"
                        )
                else:
                    errors += 1
                    self.progress_updated.emit(
                        progress,
                        f"Erro ao processar: {os.path.basename(video_path)}"
                    )
            
            # Resumo
            summary = (
                f"Processamento concluído!\n"
                f"Vídeos processados: {processed}/{total_pairs}\n"
                f"Com legenda existente: {with_subtitles}\n"
                f"Legendas sincronizadas: {synced}\n"
                f"Legendas geradas: {generated}\n"
                f"Erros: {errors}"
            )
            
            self.progress_updated.emit(100, "Processamento concluído!")
            self.finished.emit(True, summary)
            
        except Exception as e:
            self.finished.emit(False, f"Erro durante o processamento: {str(e)}")


class FontComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark_theme = False
        
    def apply_theme(self, is_dark):
        """Aplica apenas cores básicas"""
        self.is_dark_theme = is_dark
        
        if is_dark:
            # Estilo MÍNIMO para tema escuro
            style = """
                QComboBox {
                    background-color: #404040;
                    color: white;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 5px;
                    padding-right: 20px;
                    min-height: 30px;
                }
                QComboBox:hover {
                    border: 1px solid #777;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 25px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 6px solid white;
                    width: 0;
                    height: 0;
                }
            """
        else:
            # Estilo MÍNIMO para tema claro
            style = """
                QComboBox {
                    background-color: white;
                    color: #333;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    padding: 5px;
                    padding-right: 20px;
                    min-height: 30px;
                }
                QComboBox:hover {
                    border: 1px solid #999;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 25px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 6px solid #333;
                    width: 0;
                    height: 0;
                }
            """
        
        self.setStyleSheet(style)


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
        
        # Inicializar log_text antes de setup_ui
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        
        self.setup_ui()
        self.load_settings()
        self.apply_current_theme()
        
    def setup_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
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
        self.folder_path.setPlaceholderText("Selecione a pasta contendo os vídeos...")
        folder_layout.addWidget(self.folder_path)
        
        browse_btn = QPushButton()
        browse_btn.setFixedSize(120, 100)
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
                background-color: transparent;
            }
            QPushButton:pressed {
                background-color: transparent;
            }
        """)
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)
        
        layout.addLayout(folder_layout)
        
        # Informação sobre processamento
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("""
            QFrame {
                background-color: #FFF3E0;
                border-radius: 5px;
                border: 1px solid #FFE0B2;
            }
        """)
        info_layout = QVBoxLayout(self.info_frame)
        info_layout.setContentsMargins(10, 5, 10, 5)

        # Layout para o texto e o botão de ocultar
        top_info_layout = QHBoxLayout()
        
        info_label = QLabel(
            "📹 O aplicativo processará TODOS os vídeos da pasta.\n"
            "• Se houver legenda: Verificará sincronização e corrigirá se necessário\n"
            "• Se não houver legenda: Gerará legenda no idioma selecionado"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #FF6B35; font-size: 12px; border: none; background: transparent;")
        top_info_layout.addWidget(info_label)

        top_info_layout.addStretch()
        
        info_label = QLabel(
            "📹 O aplicativo processará TODOS os vídeos da pasta.\n"
            "• Se houver legenda: Verificará sincronização e corrigirá se necessário\n"
            "• Se não houver legenda: Gerará legenda no idioma selecionado"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #FF6B35; font-size: 12px;")
        
        hide_button = QPushButton("Ocultar")
        hide_button.setCursor(Qt.PointingHandCursor)
        hide_button.setStyleSheet("""
            QPushButton { 
                font-size: 10px; color: #FF6B35; border: 1px solid #FF6B35; 
                border-radius: 5px; padding: 2px 8px; max-height: 20px;
            }
            QPushButton:hover { background-color: #FFE0B2; }
        """)
        hide_button.clicked.connect(self.info_frame.hide)
        top_info_layout.addWidget(hide_button, 0, Qt.AlignTop)
        info_layout.addLayout(top_info_layout)
        
        layout.addWidget(self.info_frame)
        
        return group
    
    def create_subtitle_settings(self):
        group = QGroupBox("Configurações de Legenda")
        layout = QVBoxLayout(group)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Fonte
        font_layout = QHBoxLayout()
        font_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font_layout.addWidget(QLabel("Fonte:"))
        
        self.font_combo = FontComboBox()
        self.font_combo.setMinimumWidth(250)
        self.font_combo.setMaxVisibleItems(15)
        
        # Carregar fontes do sistema
        self.load_system_fonts()
        
        font_layout.addWidget(self.font_combo)
        
        font_layout.addWidget(QLabel("Tamanho:"))
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        self.font_size.setValue(16)
        font_layout.addWidget(self.font_size)
        
        # Botão para Negrito
        self.bold_button = QPushButton("N")
        self.bold_button.setCheckable(True)
        self.bold_button.setFixedSize(40, 30)
        
        app_font = self.font()
        bold_font = QFont(app_font)
        bold_font.setBold(True)
        self.bold_button.setFont(bold_font)
        
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
        
        return group
    
    def create_progress_section(self):
        group = QGroupBox("Progresso do Processamento")
        layout = QVBoxLayout(group)
        
        self.status_label = QLabel("Status: Pronto")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return group
    
    def create_log_section(self):
        group = QGroupBox("Log de Atividades")
        layout = QVBoxLayout(group)
        
        layout.addWidget(self.log_text)
        
        return group
    
    def create_action_buttons(self):
        layout = QHBoxLayout()
        
        self.sync_btn = QPushButton()
        self.sync_btn.setFixedSize(180, 140)
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
                background-color: transparent;
            }
            QPushButton:pressed {
                background-color: transparent;
            }
            QPushButton:disabled {
                background-color: transparent;
                opacity: 0.5;
            }
        """)
        self.sync_btn.clicked.connect(self.start_sync)
        
        settings_btn = QPushButton()
        settings_btn.setFixedSize(160, 120)
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
                background-color: transparent;
            }
            QPushButton:pressed {
                background-color: transparent;
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
            
            # Verificar vídeos na pasta
            self.check_videos_in_folder(folder)
    
    def check_videos_in_folder(self, folder):
        """Verifica se há vídeos na pasta selecionada"""
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.m4v']
        video_count = 0
        
        for root, dirs, files in os.walk(folder):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    video_count += 1
        
        if video_count > 0:
            self.log_text.append(f"✅ Encontrados {video_count} vídeo(s) na pasta")
        else:
            self.log_text.append("⚠️ Nenhum vídeo encontrado na pasta")
    
    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #ccc;")
            self.update_font_preview_color(color.name())
    
    def update_font_preview_color(self, color):
        """Atualiza a cor do texto no preview da fonte"""
        current_style = self.font_preview_label.styleSheet()
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
        
        # Verificar se há vídeos
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.m4v']
        has_videos = False
        
        for root, dirs, files in os.walk(self.current_directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    has_videos = True
                    break
            if has_videos:
                break
        
        if not has_videos:
            QMessageBox.warning(self, "Aviso", "Nenhum vídeo encontrado na pasta selecionada.")
            return
        
        # Configurações de legenda
        subtitle_settings = {
            'font_family': self.font_combo.currentText(),
            'font_size': self.font_size.value(),
            'bold': self.bold_button.isChecked(),
            'font_color': self.color_btn.styleSheet().split('background-color: ')[1].split(';')[0]
        }
        
        # Carregar configurações de saída
        output_mode = self.config.get_setting('output_mode', 'same_folder')
        output_folder = self.config.get_setting('output_folder', 'output')
        
        subtitle_settings['output_mode'] = output_mode
        subtitle_settings['output_folder'] = output_folder
        
        # Verificar se há legendas existentes
        sync_engine = SubtitleSyncEngine()
        pairs = sync_engine.find_video_subtitle_pairs(self.current_directory)
        
        videos_with_subtitles = sum(1 for _, subtitle_path in pairs if subtitle_path)
        videos_without_subtitles = sum(1 for _, subtitle_path in pairs if not subtitle_path)
        
        self.log_text.append(f"📊 Análise da pasta:")
        self.log_text.append(f"   • Total de vídeos: {len(pairs)}")
        self.log_text.append(f"   • Com legenda: {videos_with_subtitles}")
        self.log_text.append(f"   • Sem legenda: {videos_without_subtitles}")
        
        # Se houver vídeos sem legenda, perguntar idioma
        target_language = None
        if videos_without_subtitles > 0:
            dialog = LanguageDialog(self)
            if dialog.exec():
                target_language = dialog.get_selected_language()
                self.log_text.append(f"🌐 Idioma selecionado: {target_language}")
            else:
                self.log_text.append("❌ Processamento cancelado pelo usuário")
                return
        
        # Salvar configurações
        self.config.set_setting('font_family', subtitle_settings['font_family'])
        self.config.set_setting('font_size', subtitle_settings['font_size'])
        self.config.set_setting('font_bold', subtitle_settings['bold'])
        self.config.set_setting('font_color', subtitle_settings['font_color'])
        
        # Iniciar thread de processamento
        self.sync_thread = SyncThread(
            self.current_directory, 
            subtitle_settings, 
            target_language
        )
        self.sync_thread.progress_updated.connect(self.update_progress)
        self.sync_thread.finished.connect(self.sync_finished)
        
        self.sync_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Status: Processamento em andamento...")
        
        self.log_text.append("▶️ Iniciando processamento...")
        self.sync_thread.start()
    
    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(f"Status: {message}")
        if message:
            self.log_text.append(f"   {message}")
    
    def sync_finished(self, success, message):
        self.sync_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("Status: Processamento concluído")
            self.log_text.append("✅ " + message)
            QMessageBox.information(self, "Concluído", message)
        else:
            self.status_label.setText("Status: Erro no processamento")
            self.log_text.append("❌ " + message)
            QMessageBox.critical(self, "Erro", message)
    
    def open_settings(self):
        dialog = SettingsDialog(self.config, self.language_manager, self)
        if dialog.exec():
            self.load_settings()
            self.apply_current_theme()
    
    def load_system_fonts(self):
        """Carrega TODAS as fontes do sistema"""
        try:
            font_database = QFontDatabase()
            all_font_families = font_database.families()
            
            sorted_fonts = sorted(all_font_families)
            
            self.font_combo.clear()
            
            for font_family in sorted_fonts:
                if self.has_latin_support(font_family):
                    self.font_combo.addItem(font_family)
                    index = self.font_combo.count() - 1
                    self.font_combo.setItemData(index, QFont(font_family, 10), Qt.ItemDataRole.FontRole)
            
            if self.font_combo.count() == 0:
                self.load_fallback_fonts()
                
            if hasattr(self, 'log_text') and self.log_text:
                self.log_text.append(f"✅ Carregadas {self.font_combo.count()} fontes do sistema")
            
        except Exception as e:
            if hasattr(self, 'log_text') and self.log_text:
                self.log_text.append(f"❌ Erro ao carregar fontes: {str(e)}")
            self.load_fallback_fonts()
    
    def has_latin_support(self, font_family):
        """Verifica se a fonte tem suporte a caracteres latinos básicos"""
        try:
            test_font = QFont(font_family, 10)
            test_font_metrics = QFontMetrics(test_font)
            test_string = "AaBbCc"
            width = test_font_metrics.horizontalAdvance(test_string)
            return width > 20
        except:
            return True
    
    def load_fallback_fonts(self):
        """Carrega fontes fallback"""
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
            
            if self.bold_button.isChecked():
                preview_font.setBold(True)
            else:
                preview_font.setBold(False)
            
            self.font_preview_label.setFont(preview_font)
            
            current_style = self.font_preview_label.styleSheet()
            if "color:" in current_style:
                pass
            else:
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
            default_font = QFont("Arial", self.font_size.value())
            if self.bold_button.isChecked():
                default_font.setBold(True)
            self.font_preview_label.setFont(default_font)
    
    def on_font_size_changed(self):
        self.update_font_preview()
    
    def on_bold_toggled(self):
        self.update_font_preview()
    
    def load_settings(self):
        font_family = self.config.get_setting('font_family', 'Arial')
        font_size = self.config.get_setting('font_size', 16)
        font_bold = self.config.get_setting('font_bold', False)
        font_color = self.config.get_setting('font_color', '#FFFFFF')
        
        self.font_combo.setCurrentText(font_family)
        self.font_size.setValue(font_size)
        self.bold_button.setChecked(font_bold)
        self.color_btn.setStyleSheet(f"background-color: {font_color}; border: 1px solid #ccc;")
        
        self.update_font_preview(font_family)
        self.update_font_preview_color(font_color)
    
    def apply_current_theme(self):
        """Aplica o tema atual"""
        theme = self.config.get_setting('theme', 'light')
        is_dark = (theme == 'dark')
        
        if is_dark:
            apply_dark_theme(QApplication.instance())
            self.apply_dark_theme_styles()
        else:
            QApplication.instance().setStyle("Fusion")
            QApplication.instance().setPalette(QApplication.instance().style().standardPalette())
            self.apply_light_theme_styles()
        
        if hasattr(self, 'font_combo') and isinstance(self.font_combo, FontComboBox):
            self.font_combo.apply_theme(is_dark)
        
        self.style_manager.apply_style(self, 'main')
    
    def apply_dark_theme_styles(self):
        """Aplica estilos para tema escuro"""
        self.bold_button.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 4px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #505050;
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
        
        current_color_style = self.color_btn.styleSheet()
        if "background-color: #FFFFFF" in current_color_style:
            self.color_btn.setStyleSheet("background-color: #FFFFFF; border: 1px solid #606060;")
        
        current_preview_style = self.font_preview_label.styleSheet()
        if "background-color: #f8f9fa" in current_preview_style:
            self.font_preview_label.setStyleSheet("""
                QLabel {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    padding: 8px;
                    border-radius: 4px;
                    min-width: 200px;
                    color: white;
                }
            """)
        
        self.info_frame.setStyleSheet("""
            QFrame {
                background-color: #3A2C1C;
                border-radius: 5px;
                border: 1px solid #5A3C1C;
            }
        """)
    
    def apply_light_theme_styles(self):
        """Aplica estilos para tema claro"""
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
        
        current_color = self.color_btn.styleSheet().split('background-color: ')[1].split(';')[0]
        self.color_btn.setStyleSheet(f"background-color: {current_color}; border: 1px solid #ccc;")
        
        current_preview_style = self.font_preview_label.styleSheet()
        if "background-color: #2d2d2d" in current_preview_style:
            self.font_preview_label.setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    padding: 8px;
                    border-radius: 4px;
                    min-width: 200px;
                    color: #000000;
                }
            """)
        
        self.info_frame.setStyleSheet("""
            QFrame {
                background-color: #FFF3E0;
                border-radius: 5px;
                border: 1px solid #FFE0B2;
            }
        """)
    
    def apply_styles(self):
        self.apply_current_theme()
    
    def closeEvent(self, event):
        if self.sync_thread and self.sync_thread.isRunning():
            reply = QMessageBox.question(
                self, 'Confirmação',
                'O processamento ainda está em andamento. Deseja realmente fechar?',
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


# Exportar a classe MainWindow
__all__ = ['MainWindow']