from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

class ThemeManager:
    def __init__(self, app, config_manager):
        self.app = app
        self.config_manager = config_manager
    
    def apply_theme(self):
        """Aplica o tema baseado na configuração"""
        theme_name = self.config_manager.get('general.theme', 'dark')
        logger.info(f"Aplicando tema: {theme_name}")
        
        if theme_name == 'dark':
            self._apply_dark_theme()
        elif theme_name == 'light':
            self._apply_light_theme()
        else:
            self._apply_system_theme()
    
    def _apply_dark_theme(self):
        """Aplica o tema escuro"""
        self.app.setStyle("Fusion")
        
        dark_palette = QPalette()
        
        # Cores do tema escuro
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        
        # Cores para itens desabilitados
        dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, Qt.gray)
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, Qt.gray)
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.gray)
        
        self.app.setPalette(dark_palette)
        
        # Aplicar estilo adicional via CSS se disponível
        self._apply_dark_stylesheet()
    
    def _apply_light_theme(self):
        """Aplica o tema claro"""
        self.app.setStyle("Fusion")
        
        # Usar paleta padrão para tema claro
        light_palette = QPalette()
        self.app.setPalette(light_palette)
        
        # Remover qualquer stylesheet escuro
        self.app.setStyleSheet("")
    
    def _apply_system_theme(self):
        """Usa o tema do sistema"""
        self.app.setStyle("Fusion")
        
        # Usar paleta padrão do sistema
        system_palette = QPalette()
        self.app.setPalette(system_palette)
        
        # Remover stylesheet customizado
        self.app.setStyleSheet("")
    
    def _apply_dark_stylesheet(self):
        """Aplica stylesheet adicional para tema escuro"""
        dark_stylesheet = """
        QToolTip {
            color: #ffffff;
            background-color: #2a2a2a;
            border: 1px solid #767676;
        }
        
        QMenuBar {
            background-color: #353535;
            color: white;
        }
        
        QMenuBar::item:selected {
            background-color: #505050;
        }
        
        QMenu {
            background-color: #353535;
            color: white;
        }
        
        QMenu::item:selected {
            background-color: #505050;
        }
        
        QStatusBar {
            background-color: #353535;
            color: white;
        }
        
        QGroupBox {
            border: 1px solid #767676;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QTabWidget::pane {
            border: 1px solid #767676;
            background-color: #353535;
        }
        
        QTabBar::tab {
            background-color: #2a2a2a;
            color: #ffffff;
            padding: 8px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #353535;
            border-bottom: 2px solid #2a82da;
        }
        
        QScrollBar:vertical {
            border: none;
            background-color: #2a2a2a;
            width: 12px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background-color: #505050;
            min-height: 20px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #606060;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        """
        
        self.app.setStyleSheet(dark_stylesheet)
    
    def toggle_theme(self):
        """Alterna entre tema escuro e claro"""
        current_theme = self.config_manager.get('general.theme', 'dark')
        new_theme = 'light' if current_theme == 'dark' else 'dark'
        
        self.config_manager.set('general.theme', new_theme)
        self.apply_theme()
        
        return new_theme