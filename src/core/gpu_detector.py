import subprocess
import platform


def detect_gpu():
    """
    Detecta se há GPU disponível para aceleração de IA.
    Retorna um dicionário padronizado.
    """
    system = platform.system().lower()

    # Tentativa CUDA (NVIDIA)
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            first_line = result.stdout.splitlines()[0]
            return {
                "available": True,
                "name": first_line.strip(),
                "backend": "cuda"
            }
    except Exception:
        pass

    # Tentativa DirectML (Windows)
    if system == "windows":
        try:
            import torch
            if torch.backends.mps.is_available():
                return {
                    "available": True,
                    "name": "DirectML / MPS",
                    "backend": "directml"
                }
        except Exception:
            pass

    # Fallback CPU
    return {
        "available": False,
        "name": "CPU",
        "backend": "cpu"
    }
