import os

from PySide6.QtCore import QFile, QTextStream, QIODevice


class StyleManager:
    def __init__(self):
        self.styles = {}

    def load_style(self, style_name: str) -> str:
        """
        Carrega um arquivo QSS da pasta assets/styles e mantém em cache.
        """
        if style_name in self.styles:
            return self.styles[style_name]

        style_path = os.path.join("assets", "styles", f"{style_name}.qss")
        style_file = QFile(style_path)

        if style_file.exists() and style_file.open(
            QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text
        ):
            stream = QTextStream(style_file)
            style = stream.readAll()
            style_file.close()

            self.styles[style_name] = style
            return style

        return ""

    def apply_style(self, widget, style_name: str):
        """
        Aplica o estilo carregado a um widget Qt.
        """
        style = self.load_style(style_name)
        if style:
            widget.setStyleSheet(style)
