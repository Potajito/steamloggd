from dataclasses import dataclass, asdict


@dataclass
class SteamUser:
    steamid: int = 0
    personaname: str = ""
    profileurl: str = ""
    api_key: str = ""
    bl_user: str = ""
    bl_password: str = ""
    avatar: str = ""
    last_game_played: int = 0
    last_game_played_name: str = ""
    last_playtime: int = 0
    games: dict[int, dict] = None
    
    def to_dict(self):
        return asdict(self)
    def from_dict(self, user_dict: dict):
        for key, value in user_dict.items():
            setattr(self, key, value)
        return self

class SteamId(str):
    pass