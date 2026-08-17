import hashlib
import os
import requests
from sqlalchemy import select, update, func

from clap_dht.db import DB, Embedding

import logging

from clap_dht.utils.config import config
logger = logging.getLogger("NAVIDROME")

from tqdm import tqdm
import re
import time


class Navidrome:
    def __init__(self):
        pass

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
            "c": "clap_dht",
            "f": "json",
        }


    def query_navidrome(self, endpoint: str, extra_params: dict = None) -> dict:
        """Sends a query request to a specific Navidrome API endpoint."""
        url = f"{config.NAVIDROME_URL.rstrip('/')}/rest/{endpoint}"

        params = self.get_auth_params(config.NAVIDROME_USER, config.NAVIDROME_PASSWORD)
        if extra_params:
            params.update(extra_params)

        try:
            logger.debug(url)
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

    def album_iterator(self, size=500):
        offset = 0
        while True:
            albums = self.query_navidrome("getAlbumList", {"type": "newest", "size": size, "offset": offset})
            albumList = albums["albumList"]
            if "album" not in albumList:
                return
            albums_id = [a["id"] for a in albumList["album"]]
            for id in albums_id:
                album = self.query_navidrome("getAlbum", {"id": id})
                yield album["album"]
            offset += size

    def songs_iterator(self, size=2000):
        offset = 0
        while True:
            results = self.query_navidrome("search3", {"query": "", "artistCount": "0", "albumCount": "0", "songCount": size, "songOffset": offset})
            try:
                songs = results["searchResult3"]["song"]
                for song in songs:
                    yield song
            except:
                return None
            offset += size

    def update_ids(self, quick_scan=False, full_scan=False):
        if quick_scan or full_scan:
            self.scan(full_scan)

        logger.info("Updating ids")
        lookup_data = []

        libPath = "/music/"
        
        logger.info("Loading navidrome ids")
        for song in tqdm(self.songs_iterator()):
            relative_path = re.sub(rf"^{libPath}(.*)$", r"\1", song["path"])
            lookup_data.append({"path": relative_path, "songId": song["id"], "albumId": song["albumId"], "artistId": song["artistId"]})

        db = DB()
        with db as session:
            logger.info("Preparing update")
            paths = session.scalars(select(Embedding.path)).all()
            lookup_data = [r for r in lookup_data if r["path"] in paths]

            logger.info("Updating CLAP_DHT DB")
            session.execute(update(Embedding), lookup_data)
            session.commit()

            unmateched_count = session.scalar(select(func.count()).select_from(Embedding).where(Embedding.songId == None))
            total_count = session.scalar(select(func.count()).select_from(Embedding))
            logger.info(f"Unmatched: {unmateched_count}/{total_count}")

    def scan(self, full_scan=False):
        args = {}
        if full_scan:
            args |= { "fullScan": True}
        response = self.query_navidrome("startScan", args)
        logger.debug(f"startScan\n{response}")

        while True:
            time.sleep(0.95)
            response = self.query_navidrome("getScanStatus")
            logger.debug(f"getScanStatus\n{response}")
            status = response["scanStatus"]
            if status["scanning"] != True:
                return
            folderCount = status["folderCount"]
            elapsedTime = status["elapsedTime"]
            logger.info(f"Total Folders Scanned: {folderCount}, Elapsed Time: {int(elapsedTime/1e9)}s")