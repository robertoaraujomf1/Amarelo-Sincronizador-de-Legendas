import os
import logging
from typing import List, Dict, Optional

from src.core.subtitle_generator import SubtitleGenerator

logger = logging.getLogger(__name__)

class Translator:  # Renomeado de SubtitleTranslator para Translator
    def __init__(self, config=None):
        self.config = config or {}
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.generator = SubtitleGenerator(config)
        
    def translate_text(self, text: str, source_language: str, target_language: str) -> str:
        """
        Implementação simples usando OpenAI Chat Completions
        """
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY não definida")

        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        # Mapear códigos de idioma para nomes
        lang_names = {
            "pt_BR": "português brasileiro",
            "en_US": "inglês americano",
            "es_ES": "espanhol",
            "fr_FR": "francês",
            "de_DE": "alemão",
            "ja_JP": "japonês",
            "ko_KR": "coreano",
            "pt_PT": "português de Portugal",
            "pt": "português",
            "en": "inglês",
            "es": "espanhol",
            "fr": "francês",
            "de": "alemão",
            "ja": "japonês",
            "ko": "coreano"
        }
        
        source_name = lang_names.get(source_language, source_language)
        target_name = lang_names.get(target_language, target_language)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Você é um tradutor profissional. Traduza o texto de {source_name} para {target_name}, mantendo o sentido, naturalidade e contexto."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    def translate(self, srt_content: str, source_language: str, target_language: str) -> str:
        """
        Traduz conteúdo SRT de um idioma para outro.
        
        Args:
            srt_content: Conteúdo SRT como string
            source_language: Código do idioma de origem (ex: "pt_BR")
            target_language: Código do idioma de destino (ex: "en_US")
        
        Returns:
            Conteúdo SRT traduzido
        """
        if source_language == target_language:
            return srt_content

        # Parse do SRT
        subtitles = self.generator.parse_srt(srt_content)
        
        if not subtitles:
            return srt_content

        # Traduz cada legenda
        for sub in subtitles:
            if sub["text"].strip():
                sub["text"] = self.translate_text(
                    sub["text"],
                    source_language,
                    target_language
                )

        # Gera o SRT traduzido
        return self.generator.generate_from_segments(subtitles)
    
    def translate_subtitles(self, subtitles: List[Dict], source_lang: str, target_lang: str) -> List[Dict]:
        """
        Traduz uma lista de legendas no formato de dicionário.
        
        Args:
            subtitles: Lista de dicionários de legendas
            source_lang: Idioma de origem
            target_lang: Idioma de destino
            
        Returns:
            Lista de legendas traduzidas
        """
        if source_lang == target_lang:
            return subtitles
        
        translated_subtitles = []
        
        for subtitle in subtitles:
            translated_sub = subtitle.copy()
            original_text = subtitle.get('text', '')
            
            if original_text.strip():
                try:
                    translated_text = self.translate_text(
                        original_text, 
                        source_lang, 
                        target_lang
                    )
                except Exception as e:
                    logger.error(f"Erro ao traduzir texto: {e}")
                    translated_text = f"[ERRO DE TRADUÇÃO] {original_text}"
            else:
                translated_text = original_text
            
            translated_sub['text'] = translated_text
            translated_sub['original_text'] = original_text
            translated_subtitles.append(translated_sub)
        
        return translated_subtitles
    
    def detect_language(self, text: str) -> str:
        """
        Detecta o idioma do texto.
        
        Args:
            text: Texto para detectar idioma
            
        Returns:
            Código do idioma detectado
        """
        # Implementação básica de detecção
        # Em uma implementação real, usaríamos uma biblioteca como langdetect
        
        text_lower = text.lower()
        
        # Palavras comuns em diferentes idiomas
        pt_words = ['e', 'o', 'a', 'de', 'do', 'da', 'em', 'que', 'é', 'á', 'ã', 'õ', 'ç']
        en_words = ['the', 'and', 'to', 'of', 'a', 'in', 'that', 'is', 'it', 'for']
        es_words = ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'por', 'con']
        fr_words = ['le', 'la', 'de', 'et', 'à', 'en', 'un', 'une', 'des', 'que']
        
        pt_count = sum(1 for word in pt_words if word in text_lower)
        en_count = sum(1 for word in en_words if word in text_lower)
        es_count = sum(1 for word in es_words if word in text_lower)
        fr_count = sum(1 for word in fr_words if word in text_lower)
        
        counts = {
            'pt': pt_count,
            'en': en_count,
            'es': es_count,
            'fr': fr_count
        }
        
        # Retornar o idioma com mais correspondências
        detected = max(counts.items(), key=lambda x: x[1])
        
        # Se não houver correspondências significativas, usar inglês como padrão
        if detected[1] < 1:
            return 'en'
        
        return detected[0]