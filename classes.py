from dataclasses import dataclass, asdict


@dataclass
class SteamUser:
    steamid: int
    personaname: str
    profileurl: str
    api_key: str
    avatar: str
    last_game_played: int
    last_game_played_name: str
    last_playtime: int
    games: dict[int, dict]
    
    def to_dict(self):
        return asdict(self)
    

class SteamId(str):
    pass