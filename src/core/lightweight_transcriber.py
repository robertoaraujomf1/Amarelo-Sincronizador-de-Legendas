# src/core/lightweight_transcriber.py - VERSÃO SIMPLIFICADA SEM SPEECHRECOGNITION
import os
import re
from typing import Dict, Optional, Tuple


class LightweightTranscriber:
    """Transcritor leve que cria legendas mock inteligentes"""
    
    def __init__(self):
        print("🟢 Transcritor leve inicializado (modo mock inteligente)")
        print("💡 Para transcrição real de áudio, instale: pip install openai-whisper")
    
    def transcribe(self, video_path: str) -> Optional[Dict]:
        """
        Cria transcrição mock inteligente baseada no nome do arquivo.
        """
        try:
            print(f"📝 Criando legenda para: {os.path.basename(video_path)}")
            
            # Informações do arquivo
            file_name = os.path.basename(video_path)
            base_name = os.path.splitext(file_name)[0]
            file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
            
            # Detectar tipo de conteúdo
            content_type, details = self._analyze_filename(base_name)
            
            # Estimativa de duração mais precisa
            estimated_duration = self._estimate_duration(file_size, content_type)
            
            # Criar segmentos baseados no tipo de conteúdo
            if content_type == 'episode':
                segments = self._create_episode_segments(base_name, details, estimated_duration)
            elif content_type == 'movie':
                segments = self._create_movie_segments(base_name, details, estimated_duration)
            else:
                segments = self._create_general_segments(base_name, estimated_duration)
            
            return {
                'language': 'pt-BR',
                'segments': segments,
                'is_mock': True,
                'content_type': content_type,
                'estimated_duration': estimated_duration,
                'note': 'Para transcrição automática do áudio: pip install openai-whisper torch torchaudio'
            }
            
        except Exception as e:
            print(f"❌ Erro no transcritor: {e}")
            return self._create_fallback_transcription(video_path)
    
    def _analyze_filename(self, filename: str) -> Tuple[str, Dict]:
        """Analisa o nome do arquivo para determinar tipo de conteúdo"""
        lower_name = filename.lower()
        
        # Padrões de episódios
        ep_patterns = [
            r'episode\s*\d+', r'episodio\s*\d+', r'ep\s*\d+',
            r'e\d+', r's\d+e\d+', r'temporada\s*\d+', r'season\s*\d+'
        ]
        
        for pattern in ep_patterns:
            if re.search(pattern, lower_name, re.IGNORECASE):
                # Extrair números
                season_match = re.search(r's(\d+)', lower_name, re.IGNORECASE)
                episode_match = re.search(r'e(\d+)', lower_name, re.IGNORECASE) or \
                               re.search(r'episode\s*(\d+)', lower_name, re.IGNORECASE)
                
                season = season_match.group(1) if season_match else "1"
                episode = episode_match.group(1) if episode_match else "1"
                
                return 'episode', {'season': season, 'episode': episode}
        
        # Padrões de filmes
        movie_patterns = [
            r'part\s*\d+', r'parte\s*\d+', r'chapter\s*\d+', 
            r'capitulo\s*\d+', r'cd\s*\d+', r'disc\s*\d+'
        ]
        
        for pattern in movie_patterns:
            if re.search(pattern, lower_name, re.IGNORECASE):
                part_match = re.search(r'part\s*(\d+)', lower_name, re.IGNORECASE)
                part = part_match.group(1) if part_match else "1"
                return 'movie', {'part': part}
        
        return 'general', {}
    
    def _estimate_duration(self, file_size: int, content_type: str) -> float:
        """Estima duração baseada no tamanho e tipo"""
        # Taxas de compressão estimadas (bytes por segundo)
        bitrates = {
            'episode': 250 * 1024,  # 250KB/s para episódios (compressão média)
            'movie': 300 * 1024,    # 300KB/s para filmes (melhor qualidade)
            'general': 200 * 1024   # 200KB/s para conteúdo geral
        }
        
        bitrate = bitrates.get(content_type, 250 * 1024)
        if file_size == 0 or bitrate == 0:
            return 600  # Fallback: 10 minutos
        
        duration = file_size / bitrate
        
        # Limites razoáveis: entre 1 minuto e 2 horas
        return max(60, min(duration, 7200))
    
    def _create_episode_segments(self, filename: str, details: dict, duration: float) -> list:
        """Cria segmentos para episódios de séries"""
        season = details.get('season', '1')
        episode = details.get('episode', '1')
        
        # Contexto baseado no nome do arquivo
        context = self._extract_context_from_filename(filename)
        
        segments = []
        templates = [
            f"EPISÓDIO {episode} - TEMPORADA {season}",
            f"Abertura: {context}" if context else "Cena inicial e apresentação",
            "Desenvolvimento da trama principal",
            "Conflito e momento de tensão",
            "Clímax e resolução",
            f"Próximo: Episódio {int(episode) + 1}"
        ]
        
        # Ajustar número de segmentos baseado na duração
        segment_count = min(len(templates), max(3, int(duration / 120)))  # Segmento a cada ~2 minutos
        segment_duration = duration / segment_count
        
        for i in range(segment_count):
            start = i * segment_duration
            end = min((i + 1) * segment_duration, duration)
            
            text = templates[i] if i < len(templates) else f"Cena {i+1}"
            segments.append({
                'start': round(start, 2),
                'end': round(end, 2),
                'text': text
            })
        
        return segments
    
    def _create_movie_segments(self, filename: str, details: dict, duration: float) -> list:
        """Cria segmentos para filmes"""
        part = details.get('part', '1')
        
        # Contexto baseado no nome do arquivo
        context = self._extract_context_from_filename(filename)
        
        segments = []
        templates = [
            f"FILME - PARTE {part}",
            f"Introdução: {context}" if context else "Contexto inicial",
            "Desenvolvimento dos personagens",
            "Conflito central e reviravoltas",
            "Clímax emocionante",
            f"Conclusão - Parte {part}"
        ]
        
        # Ajustar número de segmentos baseado na duração
        segment_count = min(len(templates), max(4, int(duration / 300)))  # Segmento a cada ~5 minutos
        segment_duration = duration / segment_count
        
        for i in range(segment_count):
            start = i * segment_duration
            end = min((i + 1) * segment_duration, duration)
            
            text = templates[i] if i < len(templates) else f"Cena {i+1}"
            segments.append({
                'start': round(start, 2),
                'end': round(end, 2),
                'text': text
            })
        
        return segments
    
    def _create_general_segments(self, filename: str, duration: float) -> list:
        """Cria segmentos para conteúdo geral"""
        # Extrair palavras-chave do nome do arquivo
        keywords = self._extract_keywords(filename)
        
        segments = []
        templates = [
            f"INTRODUÇÃO: {filename[:50]}" if len(filename) > 10 else "Início do conteúdo",
            f"TÓPICO PRINCIPAL: {', '.join(keywords[:3])}" if keywords else "Conceitos fundamentais",
            "EXPLICAÇÃO DETALHADA",
            "EXEMPLOS PRÁTICOS",
            "CONCLUSÃO E RESUMO"
        ]
        
        # Ajustar número de segmentos
        segment_count = min(len(templates), max(3, int(duration / 180)))  # Segmento a cada ~3 minutos
        segment_duration = duration / segment_count
        
        for i in range(segment_count):
            start = i * segment_duration
            end = min((i + 1) * segment_duration, duration)
            
            text = templates[i] if i < len(templates) else f"Seção {i+1}"
            segments.append({
                'start': round(start, 2),
                'end': round(end, 2),
                'text': text
            })
        
        return segments
    
    def _extract_context_from_filename(self, filename: str) -> str:
        """Extrai contexto do nome do arquivo"""
        # Remover números e caracteres especiais
        clean_name = re.sub(r'[\d\[\]\(\)@,\-\.]', ' ', filename)
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        # Palavras comuns para remover
        common_words = {'episode', 'episodio', 'season', 'temporada', 'part', 'parte', 
                       'chapter', 'capitulo', 'cd', 'disc', 'video', 'movie', 'filme'}
        
        words = [word for word in clean_name.split() 
                if word.lower() not in common_words and len(word) > 2]
        
        if words:
            return ' '.join(words[:4])  # Retorna até 4 palavras significativas
        
        return ""
    
    def _extract_keywords(self, filename: str) -> list:
        """Extrai palavras-chave do nome do arquivo"""
        # Remover extensão e caracteres especiais
        name_without_ext = os.path.splitext(filename)[0]
        clean_name = re.sub(r'[^\w\s]', ' ', name_without_ext)
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        # Palavras para ignorar
        ignore_words = {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'are', 'was', 'were'}
        
        words = [word for word in clean_name.split() 
                if word.lower() not in ignore_words and len(word) > 2]
        
        return words[:5]  # Retorna até 5 palavras-chave
    
    def _create_fallback_transcription(self, video_path: str) -> Dict:
        """Transcrição de fallback mínima"""
        file_name = os.path.basename(video_path)
        
        return {
            'language': 'pt-BR',
            'segments': [
                {
                    'start': 0,
                    'end': 15,
                    'text': f"INÍCIO: {file_name}"
                },
                {
                    'start': 15,
                    'end': 30,
                    'text': "CONTEÚDO PRINCIPAL"
                },
                {
                    'start': 30,
                    'end': 45,
                    'text': "CONCLUSÃO E FINAL"
                }
            ],
            'is_fallback': True,
            'note': 'Legenda demonstrativa gerada automaticamente'
        }