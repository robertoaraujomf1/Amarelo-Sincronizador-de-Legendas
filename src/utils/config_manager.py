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
