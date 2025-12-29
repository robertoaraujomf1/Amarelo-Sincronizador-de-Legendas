from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                               QWidget, QLabel, QLineEdit, QPushButton, 
                               QComboBox, QSpinBox, QCheckBox, QColorDialog,
                               QGroupBox, QFormLayout, QFileDialog)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

class SettingsDialog(QDialog):
    """Diálogo de configurações"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Configurações")
        self.resize(600, 500)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Configura a interface"""
        layout = QVBoxLayout(self)
        
        # Abas
        tabs = QTabWidget()
        
        # Aba Geral
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "Geral")
        
        # Aba Transcrição
        transcription_tab = self.create_transcription_tab()
        tabs.addTab(transcription_tab, "Transcrição")
        
        # Aba Tradução
        translation_tab = self.create_translation_tab()
        tabs.addTab(translation_tab, "Tradução")
        
        # Aba Formatação
        formatting_tab = self.create_formatting_tab()
        tabs.addTab(formatting_tab, "Formatação")
        
        layout.addWidget(tabs)
        
        # Botões
        button_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("Salvar")
        self.btn_save.clicked.connect(self.save_settings)
        button_layout.addWidget(self.btn_save)
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
    
    def create_general_tab(self):
        """Cria aba de configurações gerais"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.output_dir_edit = QLineEdit()
        self.btn_browse = QPushButton("Procurar")
        self.btn_browse.clicked.connect(self.browse_output_dir)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.output_dir_edit)
        dir_layout.addWidget(self.btn_browse)
        
        layout.addRow("Diretório de saída:", dir_layout)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["pt-BR", "en-US", "es-ES", "fr-FR", "de-DE"])
        layout.addRow("Idioma da interface:", self.language_combo)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light", "system"])
        layout.addRow("Tema:", self.theme_combo)
        
        return widget
    
    def create_transcription_tab(self):
        """Cria aba de configurações de transcrição"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        layout.addRow("Modelo Whisper:", self.model_combo)
        
        self.device_combo = QComboBox()
        self.device_combo.addItems(["auto", "cpu", "cuda", "mps"])
        layout.addRow("Dispositivo:", self.device_combo)
        
        self.transcription_lang_combo = QComboBox()
        self.transcription_lang_combo.addItems(["auto", "pt", "en", "es", "fr", "de", "ja", "ko", "zh"])
        layout.addRow("Idioma de transcrição:", self.transcription_lang_combo)
        
        return widget
    
    def create_translation_tab(self):
        """Cria aba de configurações de tradução"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.translate_enabled = QCheckBox("Ativar tradução")
        layout.addRow(self.translate_enabled)
        
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems(["pt", "en", "es", "fr", "de", "it", "ja", "ko", "zh"])
        layout.addRow("Idioma de destino:", self.target_lang_combo)
        
        self.translation_provider_combo = QComboBox()
        self.translation_provider_combo.addItems(["google", "deepl", "libretranslate"])
        layout.addRow("Provedor:", self.translation_provider_combo)
        
        return widget
    
    def create_formatting_tab(self):
        """Cria aba de configurações de formatação"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Tipo de formatação
        self.format_type_combo = QComboBox()
        self.format_type_combo.addItems(["ass", "srt"])
        layout.addRow("Tipo de formatação:", self.format_type_combo)
        
        # Fonte
        self.font_name_edit = QLineEdit()
        layout.addRow("Nome da fonte:", self.font_name_edit)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        layout.addRow("Tamanho da fonte:", self.font_size_spin)
        
        # Cor
        self.color_label = QLabel()
        self.color_label.setFixedSize(50, 25)
        self.color_label.setStyleSheet("background-color: #FFFFFF; border: 1px solid black;")
        
        self.btn_choose_color = QPushButton("Escolher cor")
        self.btn_choose_color.clicked.connect(self.choose_color)
        
        color_layout = QHBoxLayout()
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.btn_choose_color)
        layout.addRow("Cor da fonte:", color_layout)
        
        # Estilo
        self.font_bold = QCheckBox("Negrito")
        layout.addRow("", self.font_bold)
        
        return widget
    
    def browse_output_dir(self):
        """Seleciona diretório de saída"""
        dir_path = QFileDialog.getExistingDirectory(self, "Selecionar diretório de saída")
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def choose_color(self):
        """Seleciona cor da fonte"""
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            self.color_label.setStyleSheet(f"background-color: {hex_color}; border: 1px solid black;")
            self.selected_color = hex_color
    
    def load_settings(self):
        """Carrega configurações atuais"""
        # Geral
        self.output_dir_edit.setText(self.config_manager.get('general.output_dir', 'output'))
        self.language_combo.setCurrentText(self.config_manager.get('general.language', 'pt-BR'))
        self.theme_combo.setCurrentText(self.config_manager.get('general.theme', 'dark'))
        
        # Transcrição
        self.model_combo.setCurrentText(self.config_manager.get('transcription.model', 'base'))
        self.device_combo.setCurrentText(self.config_manager.get('transcription.device', 'auto'))
        self.transcription_lang_combo.setCurrentText(self.config_manager.get('transcription.language', 'auto'))
        
        # Tradução
        self.translate_enabled.setChecked(self.config_manager.get('translation.enabled', False))
        self.target_lang_combo.setCurrentText(self.config_manager.get('translation.target_language', 'pt'))
        self.translation_provider_combo.setCurrentText(self.config_manager.get('translation.provider', 'google'))
        
        # Formatação
        font_config = self.config_manager.get_font_config()
        self.format_type_combo.setCurrentText(font_config.get('format_type', 'ass'))
        self.font_name_edit.setText(font_config.get('name', 'Arial'))
        self.font_size_spin.setValue(font_config.get('size', 20))
        
        color = font_config.get('color', '#FFFFFF')
        self.color_label.setStyleSheet(f"background-color: {color}; border: 1px solid black;")
        self.selected_color = color
        
        self.font_bold.setChecked(font_config.get('bold', False))
    
    def save_settings(self):
        """Salva configurações"""
        # Geral
        self.config_manager.set('general.output_dir', self.output_dir_edit.text())
        self.config_manager.set('general.language', self.language_combo.currentText())
        self.config_manager.set('general.theme', self.theme_combo.currentText())
        
        # Transcrição
        self.config_manager.set('transcription.model', self.model_combo.currentText())
        self.config_manager.set('transcription.device', self.device_combo.currentText())
        self.config_manager.set('transcription.language', self.transcription_lang_combo.currentText())
        
        # Tradução
        self.config_manager.set('translation.enabled', self.translate_enabled.isChecked())
        self.config_manager.set('translation.target_language', self.target_lang_combo.currentText())
        self.config_manager.set('translation.provider', self.translation_provider_combo.currentText())
        
        # Formatação
        self.config_manager.set('font.format_type', self.format_type_combo.currentText())
        self.config_manager.set('font.name', self.font_name_edit.text())
        self.config_manager.set('font.size', self.font_size_spin.value())
        self.config_manager.set('font.color', self.selected_color)
        self.config_manager.set('font.bold', self.font_bold.isChecked())
        
        self.accept()