import subprocess
import platform
import logging

logger = logging.getLogger(__name__)

class GPUDetector:
    """
    Detecta e fornece informações sobre GPUs disponíveis para aceleração de IA.
    """
    
    def __init__(self):
        self.gpu_info = self._detect_gpu()
        
    def _detect_gpu(self):
        """
        Detecta se há GPU disponível para aceleração de IA.
        Retorna um dicionário padronizado.
        """
        system = platform.system().lower()

        # Tentativa CUDA (NVIDIA)
        cuda_info = self._detect_cuda()
        if cuda_info["available"]:
            return cuda_info

        # Tentativa DirectML (Windows)
        if system == "windows":
            directml_info = self._detect_directml()
            if directml_info["available"]:
                return directml_info

        # Tentativa MPS (macOS)
        elif system == "darwin":
            mps_info = self._detect_mps()
            if mps_info["available"]:
                return mps_info

        # Fallback CPU
        return {
            "available": False,
            "name": "CPU",
            "backend": "cpu"
        }
    
    def _detect_cuda(self):
        """Detecta GPU NVIDIA via CUDA"""
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # Extrai a primeira linha não vazia
                lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                if lines:
                    return {
                        "available": True,
                        "name": lines[0],
                        "backend": "cuda"
                    }
        except Exception as e:
            logger.debug(f"CUDA não disponível: {e}")
        
        return {"available": False, "name": None, "backend": "cuda"}
    
    def _detect_directml(self):
        """Detecta suporte a DirectML no Windows"""
        # Verificação simplificada para DirectML
        # Em vez de importar torch, apenas verificamos se é Windows
        # A verificação real do DirectML seria feita em outro lugar se necessário
        try:
            # Verifica se o sistema é Windows 10/11 64-bit
            if platform.machine().endswith('64'):
                return {
                    "available": True,
                    "name": "DirectML (Windows)",
                    "backend": "directml"
                }
        except Exception as e:
            logger.debug(f"DirectML não disponível: {e}")
        
        return {"available": False, "name": None, "backend": "directml"}
    
    def _detect_mps(self):
        """Detecta suporte a Metal Performance Shaders no macOS"""
        # Para macOS, assumimos que MPS pode estar disponível
        try:
            # Verifica se é macOS com arquitetura Apple Silicon
            if platform.processor() == 'arm':
                return {
                    "available": True,
                    "name": "Metal Performance Shaders",
                    "backend": "mps"
                }
        except Exception as e:
            logger.debug(f"MPS não disponível: {e}")
        
        return {"available": False, "name": None, "backend": "mps"}
    
    def is_cuda_available(self):
        """Verifica se CUDA está disponível"""
        return self.gpu_info.get("backend") == "cuda" and self.gpu_info.get("available", False)
    
    def get_backend(self):
        """Retorna o backend recomendado para uso"""
        return self.gpu_info.get("backend", "cpu")
    
    def get_gpu_name(self):
        """Retorna o nome da GPU"""
        return self.gpu_info.get("name", "CPU")
    
    def has_gpu(self):
        """Verifica se há GPU disponível"""
        return self.gpu_info.get("available", False)