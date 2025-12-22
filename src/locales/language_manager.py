import json
from pathlib import Path


class LanguageManager:
    def __init__(self, locales_path: Path, default_language: str = "pt_BR"):
        self.locales_path = locales_path
        self.default_language = default_language
        self.translations = {}
        self.current_language = default_language
        self.load_language(default_language)

    def available_languages(self) -> dict:
        languages = {}
        for file in self.locales_path.glob("*.json"):
            lang_code = file.stem
            languages[lang_code] = lang_code.replace("_", " ")
        return languages

    def load_language(self, language_code: str):
        lang_file = self.locales_path / f"{language_code}.json"

        if not lang_file.exists():
            lang_file = self.locales_path / f"{self.default_language}.json"
            self.current_language = self.default_language
        else:
            self.current_language = language_code

        with open(lang_file, "r", encoding="utf-8") as f:
            self.translations = json.load(f)

    def translate(self, key: str) -> str:
        return self.translations.get(key, key)
