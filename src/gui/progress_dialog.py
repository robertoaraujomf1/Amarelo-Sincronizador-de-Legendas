import time
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, 
    QTextEdit, QScrollArea, QWidget
)
from PySide6.QtCore import Qt


class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processando - Amarelo Legendas")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setMaximumSize(800, 700)
        
        # Aplica tema
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2d2d2d, stop:1 #252525);
            }
        """)
        
        # Variáveis para cálculo de tempo
        self.start_time = None
        self.last_update_time = None
        self.processed_count = 0
        self.total_count = 0
        self.errors = []

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Label principal de status
        self.label_status = QLabel("Preparando...")
        self.label_status.setAlignment(Qt.AlignCenter)
        self.label_status.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3a3a3a, stop:1 #2d2d2d);
                border: 1px solid #5a5a5a;
                border-radius: 8px;
                padding: 12px;
                color: #f4c430;
                font-size: 11pt;
                font-weight: 500;
            }
        """)

        # Barra de progresso
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #5a5a5a;
                border-radius: 8px;
                text-align: center;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3a3a3a, stop:1 #2d2d2d);
                color: #f4c430;
                font-weight: 500;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f4c430, stop:1 #d4a420);
                border-radius: 7px;
            }
        """)

        # Label de tempo estimado
        self.label_time = QLabel("")
        self.label_time.setAlignment(Qt.AlignCenter)
        self.label_time.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
                font-size: 9pt;
            }
        """)

        # Área de log detalhado
        log_label = QLabel("Log de Processamento:")
        log_label.setStyleSheet("color: #f4c430; font-weight: 500; font-size: 10pt;")
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2d2d2d, stop:1 #252525);
                border: 1px solid #4a4a4a;
                border-radius: 8px;
                color: #d0d0d0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                padding: 5px;
            }
        """)
        self.log_text.setMaximumHeight(150)

        # Área de pré-visualização da legenda
        preview_label = QLabel("Pré-visualização da Legenda:")
        preview_label.setStyleSheet("color: #f4c430; font-weight: 500; font-size: 10pt;")
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #1a1a1a, stop:1 #0f0f0f);
                border: 1px solid #4a4a4a;
                border-radius: 8px;
                color: #ffffff;
                font-family: 'Arial', sans-serif;
                font-size: 11pt;
                padding: 10px;
            }
        """)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setPlaceholderText("A pré-visualização da legenda aparecerá aqui...")

        # Área de erros
        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4a2d2d, stop:1 #3a2525);
                border: 1px solid #6a4a4a;
                border-radius: 8px;
                padding: 10px;
                color: #ff9999;
                font-size: 9pt;
            }
        """)
        self.error_label.hide()

        layout.addWidget(self.label_status)
        layout.addWidget(self.progress)
        layout.addWidget(self.label_time)
        layout.addWidget(log_label)
        layout.addWidget(self.log_text)
        layout.addWidget(preview_label)
        layout.addWidget(self.preview_text)
        layout.addWidget(self.error_label)

        self._add_log("Sistema inicializado. Aguardando início do processamento...")

    def _add_log(self, message: str, is_error: bool = False):
        """Adiciona uma mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "❌ ERRO:" if is_error else "ℹ️"
        log_message = f"[{timestamp}] {prefix} {message}"
        self.log_text.append(log_message)
        # Auto-scroll para o final
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def _calculate_eta(self, current: int, total: int) -> str:
        """Calcula o tempo estimado para conclusão"""
        if not self.start_time or current == 0:
            return ""
        
        elapsed = time.time() - self.start_time
        if current > 0:
            avg_time_per_item = elapsed / current
            remaining_items = total - current
            eta_seconds = avg_time_per_item * remaining_items
            eta = timedelta(seconds=int(eta_seconds))
            return f"Tempo estimado restante: {str(eta)}"
        return ""

    def update_progress(self, message: str, current: int, total: int):
        """
        Atualiza o progresso da barra de progresso.
        
        Args:
            message: Mensagem a ser exibida
            current: Número atual (índice)
            total: Total de itens
        """
        # Sempre adiciona ao log, mesmo se total for 0
        is_error = message.startswith("Erro ao processar") or "Erro:" in message or message.startswith("⚠️")
        
        if is_error:
            self.errors.append(message)
            self.error_label.setText(f"⚠️ Erros encontrados: {len(self.errors)}")
            self.error_label.show()
            self._add_log(message, is_error=True)
        else:
            self._add_log(message)
        
        # Inicializa o tempo de início quando temos total > 0
        if self.start_time is None and total > 0:
            self.start_time = time.time()
            self.total_count = total
        
        # Atualiza contador
        if current > 0:
            self.processed_count = current

        # Calcula percentual (só se total > 0)
        if total > 0:
            percent = int((current / total) * 100)
            self.progress.setValue(percent)
            self.progress.setFormat(f"{percent}% ({current}/{total})")
        else:
            # Se total é 0, mostra apenas a mensagem
            self.progress.setValue(0)
            self.progress.setFormat("Processando...")
        
        # Atualiza label de status
        self.label_status.setText(message)
        
        # Calcula e exibe tempo estimado
        if total > 0 and current > 0 and self.start_time:
            eta_text = self._calculate_eta(current, total)
            elapsed = timedelta(seconds=int(time.time() - self.start_time))
            elapsed_text = f"Tempo decorrido: {str(elapsed)}"
            
            if eta_text:
                self.label_time.setText(f"{elapsed_text} | {eta_text}")
            else:
                self.label_time.setText(elapsed_text)
        elif self.start_time and total > 0:
            # Mostra apenas tempo decorrido se ainda não processou nenhum
            elapsed = timedelta(seconds=int(time.time() - self.start_time))
            self.label_time.setText(f"Tempo decorrido: {str(elapsed)}")
        else:
            self.label_time.setText("")
        
        # Se concluído
        if total > 0 and current >= total:
            if self.start_time:
                total_time = timedelta(seconds=int(time.time() - self.start_time))
                self._add_log(f"✅ Processamento concluído em {str(total_time)}")
                if self.errors:
                    self._add_log(f"⚠️ Total de erros: {len(self.errors)}", is_error=True)
                else:
                    self._add_log("✅ Nenhum erro encontrado durante o processamento.")
    
    def showEvent(self, event):
        """Reinicia as variáveis quando o diálogo é mostrado"""
        super().showEvent(event)
        self.start_time = None
        self.last_update_time = None
        self.processed_count = 0
        self.total_count = 0
        self.errors = []
        self.log_text.clear()
        self.preview_text.clear()
        self.error_label.hide()
    
    def update_preview(self, subtitle_content: str):
        """Atualiza a pré-visualização da legenda"""
        # Mostra apenas as primeiras 10 linhas para não sobrecarregar
        lines = subtitle_content.split('\n')[:30]
        preview = '\n'.join(lines)
        if len(subtitle_content.split('\n')) > 30:
            preview += "\n\n... (truncado)"
        self.preview_text.setPlainText(preview)
        # Auto-scroll para o topo
        self.preview_text.verticalScrollBar().setValue(0)
