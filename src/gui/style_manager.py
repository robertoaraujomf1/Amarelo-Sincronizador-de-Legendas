from PyQt6.QtCore import QFile, QTextStream

class StyleManager:
    def __init__(self):
        self.styles = {}
    
    def load_style(self, style_name):
        if style_name in self.styles:
            return self.styles[style_name]
        
        style_file = QFile(f"assets/styles/{style_name}.qss")
        if style_file.exists() and style_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stream = QTextStream(style_file)
            style = stream.readAll()
            self.styles[style_name] = style
            style_file.close()
            return style
        return ""
    
    def apply_style(self, widget, style_name):
        style = self.load_style(style_name)
        if style:
            widget.setStyleSheet(style)