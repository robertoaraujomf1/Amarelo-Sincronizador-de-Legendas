import os
import re

def find_video_subtitle_pairs(directory):
    """
    Encontra pares de vídeo e legenda no diretório.
    
    Args:
        directory: Caminho do diretório
        
    Returns:
        Lista de tuplas (video_path, subtitle_path) onde subtitle_path pode ser None
    """
    # Extensões suportadas
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'}
    SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.ssa', '.sub', '.vtt', '.sbv', '.dfxp', '.ttml'}
    
    # Listar todos os arquivos
    all_files = {}
    video_files = []
    subtitle_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)
            name, ext = os.path.splitext(file)
            ext_lower = ext.lower()
            
            # Armazenar arquivo por nome base
            if name not in all_files:
                all_files[name] = {'video': None, 'subtitle': None}
            
            if ext_lower in VIDEO_EXTENSIONS:
                video_files.append(full_path)
                all_files[name]['video'] = full_path
            elif ext_lower in SUBTITLE_EXTENSIONS:
                subtitle_files.append(full_path)
                all_files[name]['subtitle'] = full_path
    
    # Criar pares
    pairs = []
    
    # Primeiro, tentar correspondência exata por nome base
    for name, files in all_files.items():
        if files['video']:
            pairs.append((files['video'], files['subtitle']))
    
    # Se ainda houver legendas sem vídeo correspondente, tentar correspondência fuzzy
    for sub_path in subtitle_files:
        sub_name = os.path.splitext(os.path.basename(sub_path))[0]
        
        # Remover padrões comuns de legendas
        clean_sub_name = re.sub(r'\.(pt|en|es|fr|de|it|ru|jp|ko|zh)(\.|$)', '', sub_name)
        clean_sub_name = re.sub(r'\[.*?\]', '', clean_sub_name).strip()
        clean_sub_name = re.sub(r'\(.*?\)', '', clean_sub_name).strip()
        
        # Procurar vídeo correspondente
        video_found = False
        for video_path in video_files:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            clean_video_name = re.sub(r'\[.*?\]', '', video_name).strip()
            clean_video_name = re.sub(r'\(.*?\)', '', clean_video_name).strip()
            
            # Comparar nomes limpos
            if clean_video_name == clean_sub_name:
                # Encontramos correspondência
                for pair in pairs:
                    if pair[0] == video_path:
                        # Já existe um par para este vídeo, substituir se a legenda atual for melhor
                        current_sub = pair[1]
                        if current_sub is None or len(os.path.basename(current_sub)) > len(os.path.basename(sub_path)):
                            pairs.remove(pair)
                            pairs.append((video_path, sub_path))
                        video_found = True
                        break
                else:
                    pairs.append((video_path, sub_path))
                    video_found = True
                break
        
        if not video_found:
            # Legenda sem vídeo correspondente
            pass
    
    # Adicionar vídeos sem legendas
    for video_path in video_files:
        found = False
        for pair in pairs:
            if pair[0] == video_path:
                found = True
                break
        if not found:
            pairs.append((video_path, None))
    
    return pairs