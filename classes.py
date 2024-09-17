from dataclasses import dataclass, asdict


@dataclass
class SteamUser:
    def __init__ (self,
        steamid=0,
        personaname="",
        profileurl="",
        api_key="",
        bl_user="",
        bl_password="",
        avatar="",
        last_game_played=0,
        last_game_played_name="",
        last_playtime=0,
        games={}):
        pass
    
    steamid: int
    personaname: str
    profileurl: str
    api_key: str
    bl_user: str
    bl_password: str
    avatar: str
    last_game_played: int
    last_game_played_name: str
    last_playtime: int
    games: dict[int, dict]
    
    def to_dict(self):
        return asdict(self)
    def from_dict(self, user_dict: dict):
        for key, value in user_dict.items():
            setattr(self, key, value)
        return self

class SteamId(str):
    pass