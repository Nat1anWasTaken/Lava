import json
import uuid
from pathlib import Path

class Playlist:
    def __init__(self, name: str = "", user_id: int = -1, public: bool = False) -> None:
        self.name = name
        self.user_id = user_id
        self.public = public

    def is_valid_uuid(val):
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False

    @classmethod
    def get_item(cls, uid: str):
        if cls.is_valid_uuid(uid):
            playlist_dir = Path("playlist")
            for file_path in playlist_dir.glob("*.json"):
                filename = file_path.stem

                with file_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                for title, playlist_data in data.items():
                    if uuid.UUID(uid) == uuid.uuid5(uuid.NAMESPACE_DNS, str(filename) + title):
                        user_id = int(filename)
                        public = playlist_data.get("public", False)
                        return title, user_id, public

    def __str__(self) -> str:
        return f"<Playlist name={self.name} uuid={self.user_id} public={self.public}>"

    @classmethod
    def from_uuid(cls, uid: str):
        if cls.is_valid_uuid(uid):
            playlist_info = cls.get_item(uid)
            title, user_id, public = playlist_info
            return cls(title, user_id, public)