from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

class ThemeManager:
    def apply_theme(self, app, theme_name: str):
        if theme_name == 'dark':
            self._apply_dark_theme(app)
        else:
            # Lógica para tema claro ou padrão
            app.setPalette(QApplication.style().standardPalette())

    def _apply_dark_theme(self, app):
        app.setStyle("Fusion")
        
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.black)
        
        app.setPalette(dark_palette)