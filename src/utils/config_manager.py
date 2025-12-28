import json
import os


class ConfigManager:
    def __init__(self):
        self.config_file = os.path.join(
            os.path.expanduser("~"),
            ".amarelo_config.json"
        )
        self.data = {}
        self.runtime = {}

    def load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}
        else:
            self.data = {}

    def save(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def set_runtime_value(self, key, value):
        self.runtime[key] = value

    def get_runtime_value(self, key, default=None):
        return self.runtime.get(key, default)

    # --- Métodos específicos para FFmpeg ---
    def get_ffmpeg_path(self) -> str:
        """Retorna o caminho salvo para o FFmpeg instalado localmente."""
        return self.get("ffmpeg_local_path", "")

    def set_ffmpeg_path(self, path: str):
        """Salva o caminho do FFmpeg instalado localmente."""
        self.set("ffmpeg_local_path", path)

    def get_ffmpeg_installed_flag(self) -> bool:
        """Retorna se o FFmpeg foi instalado localmente (pelo aplicativo)."""
        return self.get("ffmpeg_installed", False)

    def set_ffmpeg_installed_flag(self, installed: bool):
        """Marca se o FFmpeg foi instalado localmente."""
        self.set("ffmpeg_installed", installed)