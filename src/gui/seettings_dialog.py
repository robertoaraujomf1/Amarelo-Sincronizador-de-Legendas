from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QPushButton, QGroupBox, QCheckBox,
                            QListWidget, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

class SettingsDialog(QDialog):
    def __init__(self, config, language_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.language_manager = language_manager
        self.parent = parent
        
        self.setWindowTitle("Configurações")
        self.setFixedSize(500, 400)
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Idioma
        language_group = QGroupBox("Idioma")
        language_layout = QVBoxLayout(language_group)
        
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Idioma do programa:"))
        
        self.language_combo = QComboBox()
        self.language_combo.addItem("Sistema", "system")
        self.language_combo.addItem("Português (Brasil)", "pt_BR")
        self.language_combo.addItem("Português (Portugal)", "pt_PT")
        self.language_combo.addItem("English (US)", "en_US")
        self.language_combo.addItem("English (UK)", "en_GB")
        self.language_combo.addItem("Français", "fr_FR")
        self.language_combo.addItem("Deutsch", "de_DE")
        self.language_combo.addItem("Español", "es_ES")
        self.language_combo.addItem("日本語", "ja_JP")
        
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()
        
        language_layout.addLayout(lang_layout)
        layout.addWidget(language_group)
        
        # Tema
        theme_group = QGroupBox("Aparência")
        theme_layout = QVBoxLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Claro", "light")
        self.theme_combo.addItem("Escuro", "dark")
        
        theme_layout.addWidget(QLabel("Tema:"))
        theme_layout.addWidget(self.theme_combo)
        layout.addWidget(theme_group)
        
        # Pastas recentes
        recent_group = QGroupBox("Pastas Recentes")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_list = QListWidget()
        recent_layout.addWidget(self.recent_list)
        
        clear_recent_btn = QPushButton("Limpar Lista")
        clear_recent_btn.clicked.connect(self.clear_recent_folders)
        recent_layout.addWidget(clear_recent_btn)
        
        layout.addWidget(recent_group)
        
        # Botões
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Salvar")
        save_btn.clicked.connect(self.save_settings)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def load_settings(self):
        # Carregar idioma
        current_lang = self.config.get_setting('language', 'system')
        index = self.language_combo.findData(current_lang)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        # Carregar tema
        current_theme = self.config.get_setting('theme', 'light')
        index = self.theme_combo.findData(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        # Carregar pastas recentes
        recent_folders = self.config.get_setting('recent_folders', [])
        self.recent_list.clear()
        for folder in recent_folders:
            self.recent_list.addItem(folder)
    
    def save_settings(self):
        # Salvar idioma
        language = self.language_combo.currentData()
        self.config.set_setting('language', language)
        
        # Salvar tema
        theme = self.theme_combo.currentData()
        self.config.set_setting('theme', theme)
        
        # Aplicar mudanças
        if self.parent:
            self.parent.language_manager.load_language(language)
        
        QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso!")
        self.accept()
    
    def clear_recent_folders(self):
        self.config.set_setting('recent_folders', [])
        self.recent_list.clear()
        QMessageBox.information(self, "Sucesso", "Lista de pastas recentes limpa!")