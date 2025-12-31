import sys
import os
import importlib

# Adicionar a pasta raiz ao sys.path para que o Python encontre a pasta 'src'
# Se o test_app.py estiver na raiz do projeto, isso garante que 'from src.core...' funcione
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

print("=== Iniciando Diagnóstico do Sistema ===\n")

# 1. Testar Imports Internos do Projeto
components = [
    ('src.core.transcription_engine', 'TranscriptionEngine'),
    ('src.core.translator', 'Translator'),
    ('src.gui.main_window', 'MainWindow')
]

for module_path, class_name in components:
    try:
        module = importlib.import_module(module_path)
        getattr(module, class_name)
        print(f"✓ {class_name} importado com sucesso de {module_path}")
    except ImportError as e:
        print(f"✗ Erro ao importar {class_name}: {e}")
    except Exception as e:
        print(f"✗ Erro inesperado ao carregar {class_name}: {e}")

print("\n=== Verificando Dependências Externas ===\n")

# 2. Verificar bibliotecas instaladas no PIP
# Nota: 'openai-whisper' é instalado via pip, mas importado como 'whisper'
requirements = [
    ('whisper', 'openai-whisper'), 
    ('torch', 'torch'), 
    ('PyQt6', 'PyQt6'), 
    ('requests', 'requests'),
    ('numpy', 'numpy')
]

for import_name, pip_name in requirements:
    try:
        importlib.import_module(import_name)
        print(f"✓ Biblioteca '{pip_name}' está instalada.")
    except ImportError:
        print(f"✗ Biblioteca '{pip_name}' NÃO ENCONTRADA.")

# 3. Verificação Extra: CUDA (Placa de Vídeo)
try:
    import torch
    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "Nenhum"
    print(f"\n--- Info de Hardware ---")
    print(f"CUDA (GPU NVIDIA) disponível: {'Sim' if cuda_available else 'Não'}")
    print(f"Dispositivo detectado: {device_name}")
except:
    pass

print("\nPara corrigir falhas de bibliotecas, execute:")
print("pip install openai-whisper torch numpy PyQt6 requests")