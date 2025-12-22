from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QRadioButton, QPushButton, QButtonGroup
)


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setFixedSize(350, 220)

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

        save_mode = self.config.get("save_mode", "overwrite")

        if save_mode == "alternate":
            self.rb_alternate.setChecked(True)
        elif save_mode == "output":
            self.rb_output.setChecked(True)
        else:
            self.rb_overwrite.setChecked(True)

        btn_save = QPushButton("Salvar")
        btn_save.clicked.connect(self.save)

        layout.addStretch()
        layout.addWidget(btn_save)

    def save(self):
        if self.rb_alternate.isChecked():
            self.config.set("save_mode", "alternate")
        elif self.rb_output.isChecked():
            self.config.set("save_mode", "output")
        else:
            self.config.set("save_mode", "overwrite")

        self.config.save()
        self.accept()
