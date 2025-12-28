"""
Módulo para verificar e instalar FFmpeg automaticamente no Windows
"""
import os
import sys
import subprocess
import shutil
import platform
import zipfile
import urllib.request
from pathlib import Path
from typing import Optional, Tuple


def is_ffmpeg_installed(config=None) -> bool:
    """
    Verifica se FFmpeg está acessível.
    Prioridade: 1. Caminho salvo no config -> 2. PATH do sistema -> 3. PATH da sessão.
    """
    # 1. Verifica usando o caminho salvo no config (se fornecido)
    if config:
        saved_path = config.get_ffmpeg_path()
        if saved_path:
            ffmpeg_exe = Path(saved_path) / "ffmpeg.exe"
            if ffmpeg_exe.exists():
                # Testa executar o binário local
                try:
                    result = subprocess.run(
                        [str(ffmpeg_exe), "-version"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=3,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    )
                    if result.returncode == 0:
                        # Adiciona o caminho ao PATH da sessão atual para uso imediato
                        bin_path_str = str(ffmpeg_exe.parent)
                        if bin_path_str not in os.environ.get("PATH", ""):
                            os.environ["PATH"] = bin_path_str + os.pathsep + os.environ.get("PATH", "")
                        return True
                except Exception:
                    pass  # Caminho salvo é inválido, continua para outras verificações

    # 2. Verificação padrão no PATH do sistema
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_ffmpeg_download_url() -> str:
    """Retorna a URL para download do FFmpeg para Windows"""
    # URL do FFmpeg builds do BtbN (builds estáveis e completos)
    return "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"


def download_ffmpeg(download_path: Path, progress_callback=None, app=None) -> bool:
    """Baixa o FFmpeg do GitHub com timeout e processamento de eventos"""
    url = get_ffmpeg_download_url()
    
    try:
        if progress_callback:
            progress_callback("Conectando ao servidor...")
        
        # Processa eventos da UI se app fornecido
        if app:
            app.processEvents()
        
        # Usa urllib com timeout
        import socket
        socket.setdefaulttimeout(30)  # Timeout de 30 segundos
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        with urllib.request.urlopen(req, timeout=60) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192  # 8KB chunks
            
            if progress_callback:
                progress_callback(f"Baixando FFmpeg... 0%")
            
            with open(download_path, 'wb') as f:
                chunk_count = 0
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    downloaded += len(chunk)
                    chunk_count += 1
                    
                    # Processa eventos da UI a cada 5 chunks (mais responsivo)
                    if app and chunk_count % 5 == 0:
                        app.processEvents()
                    
                    # Atualiza progresso a cada 10 chunks ou se for o último chunk
                    if progress_callback and (chunk_count % 10 == 0 or not chunk):
                        if total_size > 0:
                            percent = min(100, (downloaded * 100) // total_size)
                            mb_downloaded = downloaded // 1024 // 1024
                            mb_total = total_size // 1024 // 1024 if total_size > 0 else 0
                            progress_callback(f"Baixando FFmpeg... {percent}% ({mb_downloaded}/{mb_total} MB)")
                        else:
                            mb_downloaded = downloaded // 1024 // 1024
                            progress_callback(f"Baixando FFmpeg... {mb_downloaded} MB")
        
        return True
    except urllib.error.URLError as e:
        print(f"Erro de rede ao baixar FFmpeg: {e}")
        return False
    except socket.timeout:
        print("Timeout ao baixar FFmpeg")
        return False
    except Exception as e:
        print(f"Erro ao baixar FFmpeg: {e}")
        return False


def extract_ffmpeg(zip_path: Path, extract_dir: Path, progress_callback=None, app=None) -> bool:
    """Extrai o FFmpeg do arquivo ZIP com processamento de eventos"""
    try:
        if progress_callback:
            progress_callback("Preparando extração...")
        
        if app:
            app.processEvents()
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Conta o total de arquivos para progresso
            members = zip_ref.namelist()
            total_files = len(members)
            extracted = 0
            
            if progress_callback:
                progress_callback(f"Extraindo {total_files} arquivos...")
            
            for i, member in enumerate(members):
                try:
                    zip_ref.extract(member, extract_dir)
                    extracted += 1
                    
                    # Processa eventos da UI a cada 10 arquivos
                    if app and i % 10 == 0:
                        app.processEvents()
                    
                    if progress_callback and total_files > 0:
                        percent = (extracted * 100) // total_files
                        progress_callback(f"Extraindo FFmpeg... {percent}% ({extracted}/{total_files})")
                except Exception as e:
                    print(f"Erro ao extrair {member}: {e}")
                    # Continua com os próximos arquivos
        
        if progress_callback:
            progress_callback("Extração concluída!")
        
        if app:
            app.processEvents()
        
        return True
    except zipfile.BadZipFile:
        print("Arquivo ZIP corrompido")
        return False
    except Exception as e:
        print(f"Erro ao extrair FFmpeg: {e}")
        return False


def find_ffmpeg_bin(extract_dir: Path) -> Optional[Path]:
    """Encontra o diretório bin do FFmpeg extraído"""
    # O FFmpeg geralmente está em um subdiretório como ffmpeg-master-latest-win64-gpl/bin
    for root, dirs, files in os.walk(extract_dir):
        if 'ffmpeg.exe' in files and 'ffprobe.exe' in files:
            return Path(root)
    return None


def add_to_path(ffmpeg_bin_path: Path) -> bool:
    """Adiciona o FFmpeg ao PATH do sistema (requer privilégios de administrador)"""
    try:
        if sys.platform != 'win32':
            return False
        
        import winreg
        
        # Obtém o PATH atual do sistema
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                0,
                winreg.KEY_ALL_ACCESS
            )
        except PermissionError:
            # Se não tiver permissão, tenta adicionar ao PATH do usuário
            return add_to_user_path(ffmpeg_bin_path)
        
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
            path_value = str(ffmpeg_bin_path)
            
            # CORREÇÃO: Removida indentação extra nesta linha
            if path_value not in current_path:
                new_path = current_path + os.pathsep + path_value
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                
                # Notifica o sistema sobre a mudança
                try:
                    import ctypes
                    ctypes.windll.user32.SendMessageW(
                        0xFFFF,  # HWND_BROADCAST
                        0x001A,  # WM_SETTINGCHANGE
                        0,
                        "Environment"
                    )
                except Exception:
                    pass  # Ignora erros na notificação
            
            winreg.CloseKey(key)
            return True
        except Exception as e:
            winreg.CloseKey(key)
            print(f"Erro ao modificar PATH do sistema: {e}")
            return add_to_user_path(ffmpeg_bin_path)
    except Exception as e:
        print(f"Erro ao adicionar ao PATH do sistema: {e}")
        # Tenta adicionar ao PATH do usuário como fallback
        return add_to_user_path(ffmpeg_bin_path)


def add_to_user_path(ffmpeg_bin_path: Path) -> bool:
    """Adiciona o FFmpeg ao PATH do usuário (não requer admin)"""
    try:
        if sys.platform != 'win32':
            return False
        
        import winreg
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Environment",
            0,
            winreg.KEY_ALL_ACCESS
        )
        
        try:
            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                # PATH não existe ainda, cria novo
                current_path = ""
            
            path_value = str(ffmpeg_bin_path)
            
            if path_value not in current_path:
                if current_path:
                    new_path = current_path + os.pathsep + path_value
                else:
                    new_path = path_value
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                
                # Notifica o sistema
                try:
                    import ctypes
                    ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Environment")
                except Exception:
                    pass  # Ignora erros na notificação
            
            winreg.CloseKey(key)
            return True
        except Exception as e:
            winreg.CloseKey(key)
            print(f"Erro ao adicionar ao PATH do usuário: {e}")
            return False
    except Exception as e:
        print(f"Erro ao acessar registro: {e}")
        return False


def install_ffmpeg_using_winget(progress_callback=None) -> bool:
    """Tenta instalar FFmpeg usando winget (Windows Package Manager)"""
    try:
        if progress_callback:
            progress_callback("Instalando FFmpeg usando winget...")
        
        result = subprocess.run(
            ["winget", "install", "Gyan.FFmpeg", "--silent", "--accept-package-agreements", "--accept-source-agreements"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,  # 5 minutos
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_ffmpeg_manual(progress_callback=None, app=None) -> Tuple[bool, Optional[Path]]:
    """
    Instala o FFmpeg manualmente baixando e extraindo.
    Retorna (sucesso, caminho_do_bin) ou (False, None)
    """
    if platform.system() != "Windows":
        return False, None
    
    # Diretório para instalar o FFmpeg (na pasta do aplicativo)
    app_dir = Path(__file__).parent.parent.parent
    ffmpeg_dir = app_dir / "ffmpeg"
    ffmpeg_dir.mkdir(exist_ok=True)
    
    zip_path = ffmpeg_dir / "ffmpeg.zip"
    extract_dir = ffmpeg_dir / "extracted"
    
    try:
        # Processa eventos antes de começar
        if app:
            app.processEvents()
        
        # Baixa o FFmpeg
        if progress_callback:
            progress_callback("Iniciando download do FFmpeg...")
        
        if not download_ffmpeg(zip_path, progress_callback, app):
            if zip_path.exists():
                zip_path.unlink()  # Remove arquivo parcial
            return False, None
        
        if app:
            app.processEvents()
        
        # Remove diretório de extração anterior se existir
        if extract_dir.exists():
            if progress_callback:
                progress_callback("Limpando instalação anterior...")
            try:
                shutil.rmtree(extract_dir)
            except Exception as e:
                print(f"Erro ao limpar diretório: {e}")
        
        extract_dir.mkdir(exist_ok=True, parents=True)
        
        if app:
            app.processEvents()
        
        # Extrai o FFmpeg
        if not extract_ffmpeg(zip_path, extract_dir, progress_callback, app):
            return False, None
        
        if progress_callback:
            progress_callback("Localizando arquivos do FFmpeg...")
        
        if app:
            app.processEvents()
        
        # Encontra o diretório bin
        ffmpeg_bin = find_ffmpeg_bin(extract_dir)
        if not ffmpeg_bin:
            return False, None
        
        if progress_callback:
            progress_callback("Configurando FFmpeg...")
        
        if app:
            app.processEvents()
        
        # Remove o arquivo ZIP para economizar espaço
        try:
            if zip_path.exists():
                zip_path.unlink()
        except Exception:
            pass  # Ignora erro se não conseguir remover
        
        # CORREÇÃO: Removida indentação extra nesta linha
        # Adiciona ao PATH
        add_to_path(ffmpeg_bin)
        
        return True, ffmpeg_bin
        
    except Exception as e:
        print(f"Erro na instalação manual: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def ensure_ffmpeg_installed(progress_callback=None, app=None, config=None) -> Tuple[bool, Optional[str]]:
    """
    Garante que o FFmpeg está instalado.
    Retorna (sucesso, mensagem_erro)
    """
    # ETAPA 0: Verificação Rápida (já está acessível?)
    if is_ffmpeg_installed(config):
        return True, None

    if platform.system() != "Windows":
        return False, "Instalação automática do FFmpeg só está disponível para Windows."

    # ETAPA 1: Verifica se já existe uma instalação LOCAL válida
    if config:
        # Se o flag de 'instalado' está marcado, tenta usar o caminho salvo
        if config.get_ffmpeg_installed_flag():
            saved_path = config.get_ffmpeg_path()
            if saved_path and (Path(saved_path) / "ffmpeg.exe").exists():
                if progress_callback:
                    progress_callback("Usando instalação local do FFmpeg...")
                # Adiciona ao PATH da sessão e verifica
                bin_path = Path(saved_path)
                os.environ["PATH"] = str(bin_path) + os.pathsep + os.environ.get("PATH", "")
                if is_ffmpeg_installed(config):
                    return True, None
                else:
                    # O arquivo existe mas é inválido, marca para reinstall
                    config.set_ffmpeg_installed_flag(False)

    # ETAPA 2: Tenta instalação via winget (se disponível)
    if progress_callback:
        progress_callback("Tentando instalar FFmpeg via winget...")
    if app:
        app.processEvents()

    winget_success = install_ffmpeg_using_winget(progress_callback)
    if winget_success:
        import time
        for _ in range(10):  # Aguarda 1 segundo para o sistema registrar
            time.sleep(0.1)
            if app:
                app.processEvents()
        if is_ffmpeg_installed():
            # Se winget instalou e está no PATH, salva como instalado
            if config:
                config.set_ffmpeg_installed_flag(True)
                # Tenta obter o caminho do executável
                try:
                    result = subprocess.run(
                        ["where", "ffmpeg"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    )
                    if result.returncode == 0:
                        ffmpeg_exe_path = result.stdout.strip().split('\n')[0]
                        config.set_ffmpeg_path(str(Path(ffmpeg_exe_path).parent))
                except Exception:
                    pass
            return True, None

    # ETAPA 3: Instalação Manual Local (BAIXA UMA ÚNICA VEZ)
    if progress_callback:
        progress_callback("Preparando instalação local do FFmpeg...")
    if app:
        app.processEvents()

    # Diretório de instalação local
    app_dir = Path(__file__).parent.parent.parent
    ffmpeg_dir = app_dir / "ffmpeg"
    ffmpeg_dir.mkdir(exist_ok=True)

    # Verifica se já temos os binários extraídos de uma execução anterior
    extract_dir = ffmpeg_dir / "extracted"
    ffmpeg_bin = find_ffmpeg_bin(extract_dir)  # Reutiliza a função existente

    if ffmpeg_bin and (ffmpeg_bin / "ffmpeg.exe").exists():
        # JÁ EXISTE UMA INSTALAÇÃO LOCAL PRÉVIA
        if progress_callback:
            progress_callback("FFmpeg local encontrado. Configurando...")
    else:
        # PRIMEIRA INSTALAÇÃO: Baixa e extrai
        zip_path = ffmpeg_dir / "ffmpeg.zip"
        success, ffmpeg_bin = install_ffmpeg_manual(progress_callback, app)
        if not success or not ffmpeg_bin:
            return False, "Falha na instalação manual do FFmpeg."

    # CONFIGURAÇÃO FINAL (para ambos os casos: novo ou existente)
    # 1. Adiciona ao PATH da sessão atual
    os.environ["PATH"] = str(ffmpeg_bin) + os.pathsep + os.environ.get("PATH", "")

    # 2. Salva o estado no config
    if config:
        config.set_ffmpeg_installed_flag(True)
        config.set_ffmpeg_path(str(ffmpeg_bin))

    # 3. Verificação final
    if is_ffmpeg_installed(config):
        return True, None
    else:
        return False, "FFmpeg foi instalado mas não pôde ser verificado. Tente reiniciar o aplicativo."