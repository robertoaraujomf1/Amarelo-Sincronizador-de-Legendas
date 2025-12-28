import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from PySide6.QtCore import QObject, QThread, Signal, Qt, QSize, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QMessageBox, QLabel, QComboBox, QHBoxLayout,
    QLineEdit, QDialog, QSpinBox, QCheckBox, QColorDialog,
    QStyle, QProxyStyle, QDialogButtonBox, QProgressBar, QTextEdit, QGroupBox
)
from PySide6.QtGui import QIcon, QCloseEvent, QPixmap

# Imports movidos para o topo para melhor organização
from src.core.workflow_manager import WorkflowManager

SUPPORTED_LANGS = {
    "de_DE": "Alemão",
    "en_GB": "Inglês (UK)",
    "en_US": "Inglês (US)",
    "es_ES": "Espanhol",
    "fr_FR": "Francês",
    "ja_JP": "Japonês",
    "pt_BR": "Português (Brasil)",
    "pt_PT": "Português (Portugal)",
    "ko_KR": "Coreano",
}

class BlackTextComboStyle(QProxyStyle):
    """Style proxy para forçar texto preto apenas em itens NÃO selecionados"""
    def drawControl(self, element, option, painter, widget=None):
        if element == QStyle.CE_ItemViewItem:
            # Verifica se o item NÃO está selecionado
            if not (option.state & QStyle.State_Selected):
                # Salva a cor original
                original_color = option.palette.color(option.palette.Text)
                # Força cor preta apenas para itens não selecionados
                option.palette.setColor(option.palette.Text, Qt.black)
                super().drawControl(element, option, painter, widget)
                # Restaura cor original
                option.palette.setColor(option.palette.Text, original_color)
                return
        # Para itens selecionados ou outros elementos, usa o comportamento padrão
        super().drawControl(element, option, painter, widget)

class Worker(QObject):
    """
    Worker para executar tarefas pesadas em uma thread separada,
    evitando o congelamento da UI.
    """
    finished = Signal()
    error = Signal(str)
    progress = Signal(str, int, int)
    preview = Signal(str)  # Sinal para pré-visualização
    ask_continue = Signal(str)  # Pergunta se deseja continuar
    continue_response = Signal(bool)  # Resposta do usuário

    def __init__(self, manager: WorkflowManager, directory: str, 
                 target_language: str = None, translate_existing: bool = False,
                 apply_to_all: bool = False, merge_with_video: bool = False,
                 subtitle_format: dict = None):
        super().__init__()
        self.manager = manager
        self.directory = directory
        self.target_language = target_language
        self.translate_existing = translate_existing
        self.apply_to_all = apply_to_all
        self.merge_with_video = merge_with_video
        self.subtitle_format = subtitle_format or {}
        self._continue_response = None
        self._response_event = None

    def run(self):
        """Inicia a execução do processo."""
        try:
            from pathlib import Path
            import threading
            self._response_event = threading.Event()
            
            def progress_wrapper(message, current, total):
                self.progress.emit(message, current, total)
            
            def preview_wrapper(content):
                self.preview.emit(content)
            
            def ask_continue_wrapper(filename):
                if self.apply_to_all:
                    return True
                # Emite sinal e espera resposta
                self.ask_continue.emit(filename)
                if self._response_event:
                    self._response_event.wait()
                    self._response_event.clear()
                return self._continue_response if self._continue_response is not None else True
            
            self.manager.process_directory(
                directory=Path(self.directory),
                target_language=self.target_language,
                translate_existing=self.translate_existing,
                progress_callback=progress_wrapper,
                preview_callback=preview_wrapper,
                ask_continue_callback=ask_continue_wrapper if not self.apply_to_all else None,
                merge_with_video=self.merge_with_video,
                subtitle_format=self.subtitle_format
            )
        except Exception as e:
            import traceback
            error_info = f"Ocorreu um erro inesperado:\n{e}\n\n{traceback.format_exc()}"
            self.error.emit(error_info)
        finally:
            try:
                self.finished.emit()
            except RuntimeError:
                pass
    
    def set_continue_response(self, response: bool):
        """Define a resposta do usuário sobre continuar"""
        self._continue_response = response
        if self._response_event:
            self._response_event.set()

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Amarelo Legendas")
        self.setMinimumSize(800, 700)
        
        # Obtém o diretório raiz para acessar os ícones
        self.root_dir = Path(__file__).parent.parent.parent

        self.selected_dir = None
        self.thread = None
        self.worker = None
        self.processing_timer = None
        self.start_time = None

        self._build_ui()
        # PONTO 1: Aplicativo abre maximizado
        self.showMaximized()

    def _get_icon_path(self, icon_name: str) -> str:
        """Retorna o caminho completo do ícone"""
        try:
            icon_path = self.root_dir / "assets" / "icons" / icon_name
            if icon_path.exists():
                return str(icon_path)
        except Exception:
            pass
        return ""

    def mostrar_mensagem_pergunta(self, titulo: str, mensagem: str, padrao_sim: bool = True) -> bool:
        """Exibe uma caixa de diálogo de sim/não em português."""
        caixa = QMessageBox(self)
        caixa.setWindowTitle(titulo)
        caixa.setText(mensagem)
        caixa.setIcon(QMessageBox.Icon.Question)
        
        # Botões personalizados em português
        btn_sim = caixa.addButton("Sim", QMessageBox.ButtonRole.AcceptRole)
        btn_nao = caixa.addButton("Não", QMessageBox.ButtonRole.RejectRole)
        
        # Define o botão padrão (quando pressionar Enter)
        if padrao_sim:
            caixa.setDefaultButton(btn_sim)
        else:
            caixa.setDefaultButton(btn_nao)
        
        # Executa e verifica qual botão foi pressionado
        caixa.exec()
        return caixa.clickedButton() == btn_sim

    def _build_ui(self):
        central = QWidget(self)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # ================================
        # CAMPO DE DIRETÓRIO (CLICÁVEL)
        # ================================
        
        # TextField do diretório (clicável) - REMOVIDO O BOTÃO DE PASTA
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("📁 Clique aqui para selecionar um diretório...")
        self.dir_input.setReadOnly(True)
        self.dir_input.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3a3a3a, stop:1 #2d2d2d);
                border: 2px solid #5a5a5a;
                border-radius: 12px;
                padding: 18px;
                color: #e0e0e0;
                font-size: 12pt;
                min-height: 30px;
                font-weight: 500;
            }
            QLineEdit:hover {
                border: 2px solid #7a7a7a;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4a4a4a, stop:1 #3a3a3a);
            }
        """)
        # Tornar clicável
        self.dir_input.mousePressEvent = lambda e: self.select_directory()
        
        main_layout.addWidget(self.dir_input)

        # ================================
        # BOTÕES DE AÇÃO (APENAS ÍCONES)
        # ================================
        
        # Container para os botões com ícones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(30)
        buttons_layout.setContentsMargins(0, 10, 0, 20)

        # Botão Iniciar Sincronização (apenas ícone)
        self.btn_start = QPushButton()
        
        # TENTA CARREGAR IMAGEM GRANDE, SE NÃO, USA A NORMAL
        sync_icon_large = self._get_icon_path("sync_icon_large.png")
        sync_icon_normal = self._get_icon_path("sync_icon.png")
        
        try:
            # Primeiro tenta a imagem grande
            icon_path = sync_icon_large if sync_icon_large else sync_icon_normal
            if icon_path:
                pixmap = QPixmap(icon_path)
                # Se for a imagem grande, redimensiona para 300x300
                # Se for a normal, redimensiona para 240x240
                target_size = 300 if sync_icon_large else 240
                scaled_pixmap = pixmap.scaled(
                    target_size, target_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.btn_start.setIcon(QIcon(scaled_pixmap))
                self.btn_start.setIconSize(QSize(target_size, target_size))
                # Ajusta tamanho do botão conforme a imagem
                btn_size = target_size + 40  # Botão um pouco maior que a imagem
                self.btn_start.setFixedSize(btn_size, btn_size)
        except Exception as e:
            print(f"Erro ao carregar ícone de sincronização: {e}")

        self.btn_start.setToolTip("Iniciar Sincronização")
        self.btn_start.clicked.connect(self.start)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: transparent;
                opacity: 0.8;
            }
            QPushButton:pressed {
                background: transparent;
                opacity: 0.6;
            }
            QPushButton:disabled {
                background: transparent;
                opacity: 0.3;
            }
        """)

        # Botão Configurações (apenas ícone)
        btn_settings = QPushButton()
        
        # TENTA CARREGAR IMAGEM GRANDE, SE NÃO, USA A NORMAL
        settings_icon_large = self._get_icon_path("settings_icon_large.png")
        settings_icon_normal = self._get_icon_path("settings_icon.png")
        if not settings_icon_normal:
            settings_icon_normal = self._get_icon_path("seetings_icon.png")
        
        try:
            # Primeiro tenta a imagem grande
            icon_path = settings_icon_large if settings_icon_large else settings_icon_normal
            if icon_path:
                pixmap = QPixmap(icon_path)
                # Se for a imagem grande, redimensiona para 300x300
                # Se for a normal, redimensiona para 240x240
                target_size = 300 if settings_icon_large else 240
                scaled_pixmap = pixmap.scaled(
                    target_size, target_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                btn_settings.setIcon(QIcon(scaled_pixmap))
                btn_settings.setIconSize(QSize(target_size, target_size))
                # Ajusta tamanho do botão conforme a imagem
                btn_size = target_size + 40  # Botão um pouco maior que a imagem
                btn_settings.setFixedSize(btn_size, btn_size)
        except Exception as e:
            print(f"Erro ao carregar ícone de configurações: {e}")

        btn_settings.setToolTip("Configurações")
        btn_settings.clicked.connect(self.open_settings)
        btn_settings.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: transparent;
                opacity: 0.8;
            }
            QPushButton:pressed {
                background: transparent;
                opacity: 0.6;
            }
        """)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_start)
        buttons_layout.addWidget(btn_settings)
        buttons_layout.addStretch()

        main_layout.addLayout(buttons_layout)

        # ================================
        # ÁREA DE PROCESSAMENTO
        # ================================
        
        # Grupo para área de processamento
        self.processing_group = QGroupBox("Processamento")
        self.processing_group.setStyleSheet("""
            QGroupBox {
                font-size: 14pt;
                font-weight: bold;
                color: #f4c430;
                border: 2px solid #5a5a5a;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        processing_layout = QVBoxLayout(self.processing_group)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #5a5a5a;
                border-radius: 8px;
                background-color: #2d2d2d;
                text-align: center;
                height: 25px;
                font-size: 11pt;
            }
            QProgressBar::chunk {
                background-color: #f4c430;
                border-radius: 8px;
            }
        """)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        processing_layout.addWidget(self.progress_bar)
        
        # Tempo decorrido
        self.time_label = QLabel("Tempo decorrido: 00:00")
        self.time_label.setStyleSheet("color: #e0e0e0; font-size: 10pt;")
        processing_layout.addWidget(self.time_label)
        
        # Área de log
        log_group = QGroupBox("Log de Processamento")
        log_group.setStyleSheet("""
            QGroupBox {
                font-size: 11pt;
                font-weight: bold;
                color: #e0e0e0;
                border: 1px solid #5a5a5a;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 10px;
            }
        """)
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #5a5a5a;
                border-radius: 5px;
                padding: 5px;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
            }
        """)
        log_layout.addWidget(self.log_text)
        processing_layout.addWidget(log_group)
        
        # Área de pré-visualização
        preview_group = QGroupBox("Pré-visualização da Legenda")
        preview_group.setStyleSheet("""
            QGroupBox {
                font-size: 11pt;
                font-weight: bold;
                color: #e0e0e0;
                border: 1px solid #5a5a5a;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 10px;
            }
        """)
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #5a5a5a;
                border-radius: 5px;
                padding: 5px;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        preview_layout.addWidget(self.preview_text)
        processing_layout.addWidget(preview_group)
        
        # Inicialmente, a área de processamento está visível
        self.processing_group.setVisible(True)
        
        main_layout.addWidget(self.processing_group)
        main_layout.addStretch()
        
        self.setCentralWidget(central)

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Selecionar Diretório de Vídeos"
        )
        if directory:
            self.selected_dir = directory
            # Atualiza o texto no campo
            self.dir_input.setText(directory)

    def open_settings(self):
        from src.gui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self.config, self)
        dlg.exec()

    def show_error(self, error_message: str):
        """Exibe uma caixa de diálogo de erro crítico."""
        QMessageBox.critical(self, "Erro na Execução", error_message)

    def ask_language_new(self, detected_lang=None):
        message = "Em qual idioma deseja gerar as legendas?"
        if detected_lang:
            message = f"Idioma detectado: {detected_lang}\n{message}"
        return self._ask_language(message)

    def ask_translate_existing(self):
        if self.mostrar_mensagem_pergunta("Tradução", 
                                         "Deseja traduzir as legendas para outro idioma?"):
            return self._ask_language("Escolha o idioma de destino:")
        return None

    def _ask_language(self, title):
        dialog = QDialog(self)
        dialog.setWindowTitle("Idioma")
        dialog.setMinimumWidth(350)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel(title)
        label.setStyleSheet("color: #e0e0e0; font-size: 12pt; padding: 15px; font-weight: 500;")
        layout.addWidget(label)
        
        combo = QComboBox()
        combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #5a5a5a;
                border-radius: 8px;
                padding: 12px;
                font-size: 11pt;
                color: #000000;
                min-height: 40px;
                font-weight: 500;
            }
            QComboBox::drop-down {
                border: none;
                width: 40px;
            }
            /* REMOVE todo o espaçamento da view */
            QComboBox * {
                margin: 0px;
                padding: 0px;
            }
            /* Estilo ULTRA compacto para os itens */
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #3a7bd5;
                selection-color: #ffffff;
                border: 2px solid #5a5a5a;
                border-radius: 8px;
                font-size: 11pt;
                margin: 0px;
                padding: 0px;
                border-top: 0px;
                border-bottom: 0px;
                outline: 0px;
            }
            QComboBox QAbstractItemView::item {
                padding: 0px 12px;
                margin: 0px;
                color: #000000;
                background-color: #ffffff;
                font-weight: 500;
                height: 22px;
                min-height: 22px;
                max-height: 22px;
                border: none;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #3a7bd5;
                color: #ffffff;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e6f0ff;
                color: #000000;
            }
        """)
        
        # Adiciona itens verificando por duplicatas
        added_items = set()
        for code, name in SUPPORTED_LANGS.items():
            item_text = f"{name} ({code})"
            if item_text not in added_items:
                combo.addItem(item_text, code)
                added_items.add(item_text)
        
        layout.addWidget(combo)
        
        # Botões abaixo da combobox
        buttons_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancelar")
        btn_ok.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4a4a4a, stop:1 #3a3a3a);
                color: #f4c430;
                border: 2px solid #6a6a6a;
                border-radius: 8px;
                padding: 12px 30px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #5a5a5a, stop:1 #4a4a4a);
            }
        """)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4a4a4a, stop:1 #3a3a3a);
                color: #e0e0e0;
                border: 2px solid #6a6a6a;
                border-radius: 8px;
                padding: 12px 30px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #5a5a5a, stop:1 #4a4a4a);
            }
        """)
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_ok)
        buttons_layout.addWidget(btn_cancel)
        layout.addLayout(buttons_layout)
        
        if dialog.exec() == QDialog.Accepted:
            return combo.currentData()
        return None

    def ask_subtitle_format(self):
        """Pergunta ao usuário sobre formatação das legendas"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Formatação das Legendas")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Tamanho da fonte
        size_layout = QHBoxLayout()
        size_label = QLabel("Tamanho da fonte:")
        size_label.setStyleSheet("color: #e0e0e0; font-size: 11pt;")
        size_spin = QSpinBox()
        size_spin.setRange(8, 72)
        size_spin.setValue(20)
        size_spin.setStyleSheet("""
            QSpinBox {
                background-color: #ffffff;
                border: 1px solid #5a5a5a;
                border-radius: 6px;
                padding: 8px;
                color: #000000;
                font-size: 11pt;
            }
        """)
        size_layout.addWidget(size_label)
        size_layout.addWidget(size_spin)
        size_layout.addStretch()
        layout.addLayout(size_layout)
        
        # Cor
        color_layout = QHBoxLayout()
        color_label = QLabel("Cor:")
        color_label.setStyleSheet("color: #e0e0e0; font-size: 11pt;")
        color_btn = QPushButton("Escolher Cor")
        color_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4a4a4a, stop:1 #3a3a3a);
                color: #f4c430;
                border: 1px solid #6a6a6a;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 11pt;
            }
        """)
        selected_color = "#FFFFFF"
        
        def choose_color():
            nonlocal selected_color
            color = QColorDialog.getColor()
            if color.isValid():
                selected_color = color.name()
                color_btn.setText(f"Cor: {selected_color}")
                color_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #4a4a4a, stop:1 #3a3a3a);
                        color: {selected_color};
                        border: 1px solid #6a6a6a;
                        border-radius: 6px;
                        padding: 8px 20px;
                        font-size: 11pt;
                    }}
                """)
        
        color_btn.clicked.connect(choose_color)
        color_layout.addWidget(color_label)
        color_layout.addWidget(color_btn)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # Negrito
        bold_check = QCheckBox("Negrito")
        bold_check.setStyleSheet("""
            QCheckBox {
                color: #e0e0e0;
                font-size: 11pt;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #6a6a6a;
                border-radius: 4px;
                background: #3a3a3a;
            }
            QCheckBox::indicator:checked {
                background: #f4c430;
            }
        """)
        layout.addWidget(bold_check)
        
        # Botões
        buttons_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancelar")
        btn_ok.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4a4a4a, stop:1 #3a3a3a);
                color: #f4c430;
                border: 1px solid #6a6a6a;
                border-radius: 6px;
                padding: 10px 25px;
                font-size: 11pt;
            }
        """)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4a4a4a, stop:1 #3a3a3a);
                color: #e0e0e0;
                border: 1px solid #6a6a6a;
                border-radius: 6px;
                padding: 10px 25px;
                font-size: 11pt;
            }
        """)
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_ok)
        buttons_layout.addWidget(btn_cancel)
        layout.addLayout(buttons_layout)
        
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
        """)
        
        if dialog.exec() == QDialog.Accepted:
            return {
                "size": size_spin.value(),
                "color": selected_color,
                "bold": bold_check.isChecked()
            }
        return {"size": 20, "color": "#FFFFFF", "bold": False}

    def ask_process_all_files(self, file_count: int):
        """Diálogo correto para processamento múltiplo"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Processar Arquivos")
        dialog.setMinimumWidth(450)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel(
            f"Encontrados {file_count} arquivo(s) de vídeo.\n\n"
            "Como deseja processar os arquivos?"
        )
        label.setStyleSheet("color: #e0e0e0; font-size: 12pt; padding: 15px; font-weight: 500;")
        layout.addWidget(label)
        
        # Botões com ações claras
        button_box = QDialogButtonBox()
        
        btn_process_all = button_box.addButton("Processar Todos", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_ask_each = button_box.addButton("Perguntar a Cada", QDialogButtonBox.ButtonRole.ActionRole)
        btn_cancel = button_box.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        
        # Estilizar botões
        button_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4a4a4a, stop:1 #3a3a3a);
                color: #e0e0e0;
                border: 2px solid #6a6a6a;
                border-radius: 8px;
                padding: 12px 25px;
                font-size: 11pt;
                font-weight: bold;
                margin: 8px;
                min-width: 150px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #5a5a5a, stop:1 #4a4a4a);
            }
        """
        
        for btn in [btn_process_all, btn_ask_each, btn_cancel]:
            btn.setStyleSheet(button_style)
        
        layout.addWidget(button_box)
        dialog.setStyleSheet("background-color: #2d2d2d;")
        
        # Conectar sinais
        result = None
        
        def on_process_all():
            nonlocal result
            result = True  # Processar todos
            dialog.accept()
        
        def on_ask_each():
            nonlocal result
            result = False  # Perguntar a cada
            dialog.accept()
        
        btn_process_all.clicked.connect(on_process_all)
        btn_ask_each.clicked.connect(on_ask_each)
        btn_cancel.clicked.connect(dialog.reject)
        
        if dialog.exec() == QDialog.Accepted:
            return result
        return None

    def start(self):
        """Inicia o processo de sincronização em uma thread separada."""
        if self.thread and self.thread.isRunning():
            QMessageBox.information(self, "Aviso", "Um processo já está em andamento.")
            return

        if not self.selected_dir or not os.path.isdir(self.selected_dir):
            QMessageBox.warning(self, "Aviso", "Selecione um diretório válido.")
            return

        # Pergunta sobre idioma de destino para novas legendas e tradução
        target_language = None
        translate_existing = False
        
        # Verifica se há vídeos sem legendas (precisa gerar) ou com legendas (pode traduzir)
        from pathlib import Path
        from src.core.file_matcher import match_videos_and_subtitles
        
        pairs = match_videos_and_subtitles(Path(self.selected_dir))
        has_videos_without_subtitles = any(pair.get("subtitle") is None for pair in pairs)
        has_videos_with_subtitles = any(pair.get("subtitle") is not None for pair in pairs)
        
        # Se há vídeos sem legendas, pergunta o idioma para gerar
        if has_videos_without_subtitles:
            target_language = self.ask_language_new(None)
            if target_language is None:
                return  # Usuário cancelou
        
        # Se há vídeos com legendas, pergunta se deseja traduzir
        if has_videos_with_subtitles:
            translate_lang = self.ask_translate_existing()
            if translate_lang:
                if has_videos_without_subtitles:
                    if target_language != translate_lang:
                        if self.mostrar_mensagem_pergunta(
                            "Idioma diferente",
                            f"Você escolheu {SUPPORTED_LANGS.get(target_language, target_language)} para novas legendas "
                            f"e {SUPPORTED_LANGS.get(translate_lang, translate_lang)} para tradução.\n"
                            "Deseja usar o mesmo idioma para ambos?"):
                            translate_lang = target_language
                        else:
                            target_language = translate_lang
                else:
                    target_language = translate_lang
                translate_existing = True

        # Nova caixa de diálogo para processamento múltiplo
        apply_to_all = False
        if len(pairs) > 1:
            result = self.ask_process_all_files(len(pairs))
            if result is None:
                return  # Usuário cancelou
            apply_to_all = result  # True = Processar Todos, False = Perguntar a Cada
        
        # Pergunta sobre formatação de legendas
        subtitle_format = self.ask_subtitle_format()
        
        # Pergunta sobre mesclar com vídeo
        merge_with_video = self.mostrar_mensagem_pergunta(
            "Mesclar legenda ao vídeo?",
            "Deseja mesclar a legenda diretamente no arquivo de vídeo?\n\n"
            "Isso criará um novo arquivo de vídeo com as legendas embutidas.",
            padrao_sim=False
        )

        self.btn_start.setEnabled(False)

        # Limpa a área de processamento
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.preview_text.clear()
        self.time_label.setText("Tempo decorrido: 00:00")
        
        # Inicia o timer para o tempo decorrido
        self.start_time = datetime.now()
        if self.processing_timer:
            self.processing_timer.stop()
        self.processing_timer = QTimer()
        self.processing_timer.timeout.connect(self.update_elapsed_time)
        self.processing_timer.start(1000)  # Atualiza a cada segundo

        # Configura a thread e o worker
        self.thread = QThread()
        manager = WorkflowManager(config=self.config)
        self.worker = Worker(
            manager, self.selected_dir, target_language, translate_existing,
            apply_to_all, merge_with_video, subtitle_format
        )
        self.worker.moveToThread(self.thread)

        # Conecta os sinais da thread e do worker
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_worker_finished)

        # Conecta os sinais do worker aos slots da UI
        self.worker.error.connect(self.show_error)
        self.worker.progress.connect(self.update_progress)
        self.worker.preview.connect(self.update_preview)
        
        # Handler para perguntar se deseja continuar (apenas se apply_to_all for False)
        def handle_ask_continue(filename):
            # Se apply_to_all é True, sempre retorna True
            if self.worker.apply_to_all:
                self.worker.set_continue_response(True)
                return
            
            if self.mostrar_mensagem_pergunta(
                "Continuar processamento?",
                f"Arquivo '{filename}' processado com sucesso!\n\n"
                "Deseja processar o próximo arquivo?"):
                self.worker.set_continue_response(True)
            else:
                self.worker.set_continue_response(False)
        
        self.worker.ask_continue.connect(handle_ask_continue)

        # Ações a serem executadas quando o trabalho terminar
        self.worker.finished.connect(self._on_processing_finished)

        self.thread.start()

    def update_progress(self, message: str, current: int, total: int):
        """Atualiza a barra de progresso e o log."""
        # Atualiza a barra de progresso
        if total > 0:
            progress_percent = int((current / total) * 100)
            self.progress_bar.setValue(progress_percent)
        else:
            # Modo indeterminado para tarefas sem contagem total
            self.progress_bar.setMaximum(0)
            self.progress_bar.setMaximum(100)
        
        # Adiciona a mensagem ao log
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        log_message = f"{timestamp} {message}"
        self.log_text.append(log_message)
        
        # Rola para a última linha
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_preview(self, content: str):
        """Atualiza a área de pré-visualização."""
        self.preview_text.setPlainText(content)
        
        # Rola para a primeira linha
        scrollbar = self.preview_text.verticalScrollBar()
        scrollbar.setValue(0)

    def update_elapsed_time(self):
        """Atualiza o tempo decorrido."""
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            minutes = elapsed.seconds // 60
            seconds = elapsed.seconds % 60
            self.time_label.setText(f"Tempo decorrido: {minutes:02d}:{seconds:02d}")

    def _on_processing_finished(self):
        """Lida com a finalização do processamento."""
        # Para o timer
        if self.processing_timer:
            self.processing_timer.stop()
        
        # Atualiza a interface
        self.progress_bar.setValue(100)
        self.btn_start.setEnabled(True)
        
        # Adiciona mensagem de conclusão
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_text.append(f"{timestamp} [✓] Processamento concluído com sucesso!")
        
        # Mostra mensagem de conclusão
        QMessageBox.information(self, "Concluído", "Processamento de legendas finalizado!")

    def _on_worker_finished(self):
        """Callback quando o worker termina - limpa a thread de forma segura"""
        if self.thread:
            self.thread.quit()
            # Aguarda a thread terminar (máximo 5 segundos)
            if not self.thread.wait(5000):
                # Se não terminou em 5 segundos, força a terminação
                self.thread.terminate()
                self.thread.wait()
        
        # Limpa as referências
        if self.worker:
            self.worker.deleteLater()
        if self.thread:
            self.thread.deleteLater()
        
        self.worker = None
        self.thread = None

    def closeEvent(self, event: QCloseEvent):
        """Override do closeEvent para aguardar a thread terminar antes de fechar"""
        if self.thread and self.thread.isRunning():
            # Pergunta ao usuário se deseja cancelar
            if self.mostrar_mensagem_pergunta(
                "Processamento em andamento",
                "Um processamento está em andamento. Deseja realmente sair?",
                padrao_sim=False):
                # Aguarda a thread terminar
                if self.thread:
                    self.thread.quit()
                    if not self.thread.wait(3000):  # Aguarda até 3 segundos
                        self.thread.terminate()
                        self.thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()