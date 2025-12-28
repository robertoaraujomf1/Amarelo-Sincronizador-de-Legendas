import os
from typing import Optional

from src.core.subtitle_generator import SubtitleGenerator


class SubtitleTranslator:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.generator = SubtitleGenerator()

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
            "pt_PT": "português de Portugal"
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
