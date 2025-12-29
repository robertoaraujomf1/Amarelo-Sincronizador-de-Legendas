import os
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QFileDialog, QTextEdit, 
                               QProgressBar, QCheckBox, QGroupBox, QSplitter,
                               QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QColor

from ..core.workflow_manager import WorkflowManager
from ..utils.config_manager import ConfigManager
from .progress_dialog import ProgressDialog

class ProcessingThread(QThread):
    """Thread para processamento em segundo plano"""
    progress_update = Signal(str, int)
    preview_update = Signal(list, str)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, workflow_manager, video_paths, subtitle_paths, translate, merge):
        super().__init__()
        self.workflow_manager = workflow_manager
        self.video_paths = video_paths
        self.subtitle_paths = subtitle_paths
        self.translate = translate
        self.merge = merge
    
    def run(self):
        try:
            # Configurar callbacks
            self.workflow_manager.set_preview_callback(
                lambda subs, stage: self.preview_update.emit(subs, stage)
            )
            
            # Processar arquivos
            result = self.workflow_manager.process_files(
                self.video_paths, 
                self.subtitle_paths,
                self.translate,
                self.merge
            )
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    """Janela principal da aplicação"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.video_files = []
        self.subtitle_files = []
        self.processing_thread = None
        
        self.setup_ui()
        self.setWindowTitle("Amarelo Legendas")
        self.resize(1200, 800)
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Painel superior: Controles
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Splitter principal: Lista de arquivos + Pré-visualização
        splitter = QSplitter(Qt.Horizontal)
        
        # Painel esquerdo: Lista de arquivos
        file_panel = self.create_file_panel()
        splitter.addWidget(file_panel)
        
        # Painel direito: Pré-visualização
        preview_panel = self.create_preview_panel()
        splitter.addWidget(preview_panel)
        
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)
        
        # Barra de status
        self.status_bar = self.statusBar()
        self.progress_bar = QProgressBar()
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()
    
    def create_control_panel(self):
        """Cria painel de controles"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # Botões de seleção
        self.btn_select_videos = QPushButton("Selecionar Vídeos")
        self.btn_select_videos.clicked.connect(self.select_videos)
        layout.addWidget(self.btn_select_videos)
        
        self.btn_select_subtitles = QPushButton("Selecionar Legendas")
        self.btn_select_subtitles.clicked.connect(self.select_subtitles)
        layout.addWidget(self.btn_select_subtitles)
        
        # Opções
        self.cb_translate = QCheckBox("Traduzir")
        layout.addWidget(self.cb_translate)
        
        self.cb_merge = QCheckBox("Mesclar com vídeo")
        layout.addWidget(self.cb_merge)
        
        # Botão processar
        self.btn_process = QPushButton("Processar")
        self.btn_process.clicked.connect(self.start_processing)
        self.btn_process.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        layout.addWidget(self.btn_process)
        
        layout.addStretch()
        
        return panel
    
    def create_file_panel(self):
        """Cria painel de listagem de arquivos"""
        panel = QGroupBox("Arquivos Selecionados")
        layout = QVBoxLayout(panel)
        
        # Tabela de vídeos
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(2)
        self.video_table.setHorizontalHeaderLabels(["Vídeo", "Status"])
        self.video_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(QLabel("Vídeos:"))
        layout.addWidget(self.video_table)
        
        # Tabela de legendas
        self.subtitle_table = QTableWidget()
        self.subtitle_table.setColumnCount(2)
        self.subtitle_table.setHorizontalHeaderLabels(["Legenda", "Status"])
        self.subtitle_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(QLabel("Legendas:"))
        layout.addWidget(self.subtitle_table)
        
        return panel
    
    def create_preview_panel(self):
        """Cria painel de pré-visualização"""
        panel = QGroupBox("Pré-visualização da Legenda")
        layout = QVBoxLayout(panel)
        
        # Status da pré-visualização
        self.preview_status = QLabel("Nenhuma pré-visualização disponível")
        layout.addWidget(self.preview_status)
        
        # Tabela de pré-visualização
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(3)
        self.preview_table.setHorizontalHeaderLabels(["Tempo", "Duração", "Texto"])
        self.preview_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.preview_table.setAlternatingRowColors(True)
        layout.addWidget(self.preview_table)
        
        # Área de texto para visualização completa
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        layout.addWidget(self.preview_text)
        
        return panel
    
    def select_videos(self):
        """Seleciona arquivos de vídeo"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Vídeos",
            "",
            "Vídeos (*.mp4 *.avi *.mkv *.mov *.wmv *.flv);;Todos os arquivos (*.*)"
        )
        
        if files:
            self.video_files = files
            self.update_file_tables()
    
    def select_subtitles(self):
        """Seleciona arquivos de legenda"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Legendas",
            "",
            "Legendas (*.srt *.ass *.ssa *.vtt *.sub);;Todos os arquivos (*.*)"
        )
        
        if files:
            self.subtitle_files = files
            self.update_file_tables()
    
    def update_file_tables(self):
        """Atualiza tabelas de arquivos"""
        # Atualizar tabela de vídeos
        self.video_table.setRowCount(len(self.video_files))
        for i, file_path in enumerate(self.video_files):
            file_name = os.path.basename(file_path)
            self.video_table.setItem(i, 0, QTableWidgetItem(file_name))
            self.video_table.setItem(i, 1, QTableWidgetItem("Pronto"))
        
        # Atualizar tabela de legendas
        self.subtitle_table.setRowCount(len(self.subtitle_files))
        for i, file_path in enumerate(self.subtitle_files):
            file_name = os.path.basename(file_path)
            self.subtitle_table.setItem(i, 0, QTableWidgetItem(file_name))
            self.subtitle_table.setItem(i, 1, QTableWidgetItem("Pronto"))
    
    def start_processing(self):
        """Inicia o processamento"""
        if not self.video_files:
            self.show_error("Selecione pelo menos um arquivo de vídeo")
            return
        
        # Desabilitar botões durante processamento
        self.btn_process.setEnabled(False)
        self.btn_select_videos.setEnabled(False)
        self.btn_select_subtitles.setEnabled(False)
        
        # Mostrar barra de progresso
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        # Criar workflow manager
        workflow_manager = WorkflowManager(self.config)
        
        # Criar e iniciar thread de processamento
        self.processing_thread = ProcessingThread(
            workflow_manager,
            self.video_files,
            self.subtitle_files if self.subtitle_files else None,
            self.cb_translate.isChecked(),
            self.cb_merge.isChecked()
        )
        
        # Conectar sinais
        self.processing_thread.progress_update.connect(self.update_progress)
        self.processing_thread.preview_update.connect(self.update_preview)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.error.connect(self.processing_error)
        
        self.processing_thread.start()
    
    @Slot(str, int)
    def update_progress(self, message, progress):
        """Atualiza barra de progresso"""
        self.status_bar.showMessage(message)
        self.progress_bar.setValue(progress)
    
    @Slot(list, str)
    def update_preview(self, subtitles, stage):
        """Atualiza pré-visualização das legendas"""
        self.preview_status.setText(f"Pré-visualização: {stage}")
        
        # Atualizar tabela
        self.preview_table.setRowCount(len(subtitles))
        
        for i, sub in enumerate(subtitles):
            # Formatar tempo
            start_time = self.format_time(sub.get('start', 0))
            end_time = self.format_time(sub.get('end', 0))
            duration = sub.get('end', 0) - sub.get('start', 0)
            
            # Adicionar à tabela
            self.preview_table.setItem(i, 0, QTableWidgetItem(f"{start_time} → {end_time}"))
            self.preview_table.setItem(i, 1, QTableWidgetItem(f"{duration:.1f}s"))
            self.preview_table.setItem(i, 2, QTableWidgetItem(sub.get('text', '')))
        
        # Atualizar texto completo
        self.update_preview_text(subtitles)
    
    def update_preview_text(self, subtitles):
        """Atualiza área de texto da pré-visualização"""
        text = ""
        for sub in subtitles[:50]:  # Mostrar apenas primeiras 50 legendas
            start_time = self.format_time(sub.get('start', 0))
            end_time = self.format_time(sub.get('end', 0))
            text += f"[{start_time} --> {end_time}]\n{sub.get('text', '')}\n\n"
        
        if len(subtitles) > 50:
            text += f"\n... e mais {len(subtitles) - 50} legendas"
        
        self.preview_text.setText(text)
    
    def format_time(self, seconds):
        """Formata segundos para formato HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @Slot(dict)
    def processing_finished(self, result):
        """Processamento concluído"""
        self.btn_process.setEnabled(True)
        self.btn_select_videos.setEnabled(True)
        self.btn_select_subtitles.setEnabled(True)
        self.progress_bar.hide()
        
        if result.get('success'):
            self.status_bar.showMessage("Processamento concluído com sucesso!", 5000)
            
            # Mostrar resultados
            if result.get('results'):
                self.show_results(result['results'])
        else:
            errors = "\n".join(result.get('errors', []))
            self.show_error(f"Erros encontrados:\n{errors}")
    
    @Slot(str)
    def processing_error(self, error_message):
        """Erro no processamento"""
        self.btn_process.setEnabled(True)
        self.btn_select_videos.setEnabled(True)
        self.btn_select_subtitles.setEnabled(True)
        self.progress_bar.hide()
        
        self.show_error(f"Erro no processamento: {error_message}")
    
    def show_results(self, results):
        """Mostra resultados do processamento"""
        message = "Processamento concluído:\n\n"
        
        for video_path, result in results.items():
            video_name = os.path.basename(video_path)
            subtitle_files = result.get('subtitle_files', {})
            
            message += f"• {video_name}:\n"
            
            for format_name, file_path in subtitle_files.items():
                if os.path.exists(file_path):
                    message += f"  ✓ {format_name}: {os.path.basename(file_path)}\n"
        
        # Aqui poderia abrir uma caixa de diálogo com os resultados
        self.status_bar.showMessage(message, 10000)
    
    def show_error(self, message):
        """Mostra mensagem de erro"""
        # Em uma implementação completa, usar QMessageBox
        self.status_bar.showMessage(f"Erro: {message}", 10000)