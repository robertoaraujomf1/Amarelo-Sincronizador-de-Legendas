import requests
import threading
from PyQt6.QtCore import QObject, pyqtSignal

class UpdateChecker(QObject):
    """Verificador de atualizações"""
    
    # Sinal que será conectado à função de mostrar o QMessageBox na Main Window
    update_available = pyqtSignal(str, str)
    
    def __init__(self, current_version="1.0.0"):
        super().__init__()
        self.current_version = current_version
        self.github_repo = "robertoaraujomf1/Amarelo-Legendas"
        
    def check_for_updates_async(self):
        """Inicia a verificação em background"""
        thread = threading.Thread(target=self._check_updates, daemon=True)
        thread.start()
        
    def _check_updates(self):
        """Lógica interna de verificação"""
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            # Timeout curto para não travar o encerramento do app
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            # Remove o 'v' inicial se existir (ex: v1.1.0 -> 1.1.0)
            latest_version_str = data.get('tag_name', '').lstrip('v')
            
            if not latest_version_str:
                return

            if self._is_newer_version(latest_version_str, self.current_version):
                title = "Atualização Disponível"
                changelog = data.get('body', 'Sem notas de versão.')
                # Limita o tamanho do texto para não quebrar a janela
                message = (
                    f"Versão {latest_version_str} disponível!\n"
                    f"Sua versão: {self.current_version}\n\n"
                    f"Novidades:\n{changelog[:300]}..."
                )
                self.update_available.emit(title, message)
                
        except (requests.RequestException, ValueError):
            # Ignora falhas de conexão ou JSON inválido de forma segura
            pass
            
    def _is_newer_version(self, new_v, current_v):
        """Compara versões de forma robusta"""
        try:
            from packaging import version
            return version.parse(new_v) > version.parse(current_v)
        except ImportError:
            # Fallback: converte "1.2.3" em (1, 2, 3) para comparação numérica correta
            try:
                def parse_v(v):
                    return tuple(map(int, (v.split('.'))))
                return parse_v(new_v) > parse_v(current_v)
            except:
                return new_v > current_v # Último recurso (alfabético)