import hashlib
import os
import requests
from sqlalchemy import bindparam, select, update, func

from clap_dht.db import DB, Embedding

import logging
logger = logging.getLogger()


import sqlite3


class Navidrome:
    def __init__(self):
        self.uri = f"file:{os.getenv("NAVIDROME_DB")}?mode=ro&immutable=1"
        self.con = sqlite3.connect(self.uri, uri=True)

    def get_auth_params(self, username: str, password: str) -> dict:
        """
        Generates Subsonic-compatible MD5 token authentication parameters.
        token = md5(password + salt)
        """
        salt = os.urandom(6).hex()  # Generate random salt
        token_str = f"{password}{salt}"
        token = hashlib.md5(token_str.encode("utf-8")).hexdigest()

        return {
            "u": username,
            "t": token,
            "s": salt,
            "v": "1.16.1",
            "c": "python-script",
            "f": "json",
        }


    def query_navidrome(self, endpoint: str, extra_params: dict = None) -> dict:
        """Sends a query request to a specific Navidrome API endpoint."""
        url = f"{os.getenv("NAVIDROME_URL").rstrip('/')}/rest/{endpoint}"

        params = self.get_auth_params(os.getenv("NAVIDROME_USER"), os.getenv("NAVIDROME_PASSWORD"))
        if extra_params:
            params.update(extra_params)

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            subsonic_response = data.get("subsonic-response", {})

            if subsonic_response.get("status") == "ok":
                return subsonic_response
            else:
                error = subsonic_response.get("error", {})
                logger.error(f"API Error ({error.get('code')}): {error.get('message')}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP Request failed: {e}")
            return None

    def song_iterator(self):
        offset = 0
        size = 500
        while True:
            albums = self.query_navidrome("getAlbumList", {"type": "newest", "size": size, "offset": offset})
            albumList = albums["albumList"]
            if "album" not in albumList:
                return
            albums_id = [a["id"] for a in albumList["album"]]
            for id in albums_id:
                album = self.query_navidrome("getAlbum", {"id": id})
                for song in album["album"]["song"]:
                    yield song
            offset += size

    def update_ids(self):
        cur = self.con.cursor()

        logger.info("Loading Navidrome DB")
        res = cur.execute("SELECT id, path FROM media_file")
        result = res.fetchall()
        lookup_data = [{"path": path, "external_id": id} for id, path in result]

        db = DB()
        with db as session:
            logger.info("Preparing update")
            paths = session.scalars(select(Embedding.path)).all()
            lookup_data = [r for r in lookup_data if r["path"] in paths]

            logger.info("Updating CLAP_DHT DB")
            session.execute(update(Embedding), lookup_data)
            session.commit()

            unmateched_count = session.scalar(select(func.count()).select_from(Embedding).where(Embedding.external_id == None))
            total_count = session.scalar(select(func.count()).select_from(Embedding))
            logger.info(f"Unmatched: {unmateched_count}/{total_count}")