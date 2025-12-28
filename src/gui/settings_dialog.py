from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QRadioButton, QPushButton, QButtonGroup
)


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setFixedSize(380, 240)
        
        # Aplica tema suave
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2d2d2d, stop:1 #252525);
            }
            QLabel {
                color: #e0e0e0;
                font-size: 10pt;
            }
            QRadioButton {
                color: #e0e0e0;
                font-size: 10pt;
                padding: 5px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #6a6a6a;
                background: #3a3a3a;
            }
            QRadioButton::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f4c430, stop:1 #d4a420);
                border: 2px solid #8a8a8a;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4a4a4a, stop:1 #3a3a3a);
                color: #f4c430;
                border: 1px solid #6a6a6a;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 10pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #5a5a5a, stop:1 #4a4a4a);
                border: 1px solid #8a8a8a;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3a3a3a, stop:1 #2d2d2d);
            }
        """)

        self.config = config

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Onde salvar os arquivos de legenda:"))

        self.group = QButtonGroup(self)

        self.rb_overwrite = QRadioButton("Substituir arquivos originais")
        self.rb_alternate = QRadioButton("Salvar com nome alternativo")
        self.rb_output = QRadioButton("Salvar na pasta Output")

        self.group.addButton(self.rb_overwrite)
        self.group.addButton(self.rb_alternate)
        self.group.addButton(self.rb_output)

        layout.addWidget(self.rb_overwrite)
        layout.addWidget(self.rb_alternate)
        layout.addWidget(self.rb_output)

        # Suporta tanto 'output_mode' quanto 'save_mode' para compatibilidade
        save_mode = self.config.get("output_mode") or self.config.get("save_mode", "overwrite")
        
        # Normaliza valores antigos para novos
        if save_mode == "alternate":
            save_mode = "alternate_name"
        elif save_mode == "output":
            save_mode = "output_folder"

        if save_mode == "alternate_name":
            self.rb_alternate.setChecked(True)
        elif save_mode == "output_folder":
            self.rb_output.setChecked(True)
        else:
            self.rb_overwrite.setChecked(True)

        btn_save = QPushButton("Salvar")
        btn_save.clicked.connect(self.save)

        layout.addStretch()
        layout.addWidget(btn_save)

    def save(self):
        if self.rb_alternate.isChecked():
            self.config.set("output_mode", "alternate_name")
            # Remove chave antiga se existir
            if self.config.get("save_mode"):
                self.config.data.pop("save_mode", None)
        elif self.rb_output.isChecked():
            self.config.set("output_mode", "output_folder")
            if self.config.get("save_mode"):
                self.config.data.pop("save_mode", None)
        else:
            self.config.set("output_mode", "overwrite")
            if self.config.get("save_mode"):
                self.config.data.pop("save_mode", None)

        self.config.save()
        self.accept()
