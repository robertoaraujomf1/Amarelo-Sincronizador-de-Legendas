import os


class SubtitleTranslator:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

    def translate_text(self, text: str, target_language: str) -> str:
        """
        Implementação simples usando OpenAI Chat Completions
        """
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY não definida")

        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Traduza o texto para {target_language}, mantendo sentido e naturalidade."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    def translate_srt(self, srt_content: str, target_language: str) -> str:
        subtitles = self.editor.parse(srt_content)

        for sub in subtitles:
            sub["text"] = self.translate_text(sub["text"], target_language)

        return self.editor.serialize(subtitles)
