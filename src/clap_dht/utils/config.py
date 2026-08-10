from pathlib import Path
from platformdirs import user_config_dir
from decouple import Config, RepositoryIni
import logging

logger = logging.getLogger("CONFIG")

class Configuration:
    def __init__(self):
        config_dir = Path(user_config_dir(appname="clap_dht", appauthor=False))
        config_dir.mkdir(parents=True, exist_ok=True)
        self.ini_file_path = config_dir / "config.ini"
        if not self.ini_file_path.exists():
            open(self.ini_file_path, "w").write("[settings]\n")
        self.config = Config(RepositoryIni(self.ini_file_path))
        logger.debug(f"loading config: {self.ini_file_path}")

    # --- DHT ---
    @property
    def DHT_BOOTSTRAP(self) -> str:
        return self.config("DHT_BOOTSTRAP", default="")

    @property
    def DHT_NETWORK(self) -> str:
        return self.config("DHT_NETWORK", default="61395318")

    # --- POSTGRES ---
    @property
    def POSTGRES_USER(self) -> str:
        return self.config("POSTGRES_USER", default="user")

    @property
    def POSTGRES_PASSWORD(self) -> str:
        return self.config("POSTGRES_PASSWORD", default="password")

    @property
    def POSTGRES_DB(self) -> str:
        return self.config("POSTGRES_DB", default="db")

    @property
    def POSTGRES_HOST(self) -> str:
        return self.config("POSTGRES_HOST", default="127.0.0.1:5432")

    # --- DATA ---
    @property
    def DATA_ROOTDIR(self) -> str:
        return self.config("DATA_ROOTDIR", default="/music")

    # --- NAVIDROME ---
    @property
    def NAVIDROME_URL(self) -> str:
        return self.config("NAVIDROME_URL", default="http://127.0.0.1:4533/")

    @property
    def NAVIDROME_USER(self) -> str:
        return self.config("NAVIDROME_USER", default="user")

    @property
    def NAVIDROME_PASSWORD(self) -> str:
        return self.config("NAVIDROME_PASSWORD", default="password")

    @property
    def NAVIDROME_DB(self) -> str:
        return self.config("NAVIDROME_DB", default="/navidrome.db")


config = Configuration()