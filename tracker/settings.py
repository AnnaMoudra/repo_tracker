import tomllib

class Settings:
    def __init__(self, config_file="config.toml"):
        self.config_file = config_file
        self.data = self._load_config()

    def _load_config(self):
        with open(self.config_file, "rb") as f:
            return tomllib.load(f)

    @property
    def github_client_id(self):
        return self.data["github"]["client_id"]
    
    @property
    def github_client_secret(self):
        return self.data["github"]["client_secret"]

    @property
    def repositories(self):
        return self.data["database"]["repositories"]
    
    @property
    def events(self):
        return self.data["database"]["events"]

    @property
    def window_length(self):
        return self.data["settings"]["window_length"]

    @property
    def max_events(self):
        return self.data["settings"]["event_limit"]
