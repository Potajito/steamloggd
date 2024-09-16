import logging, os
from rich.logging import RichHandler
from rich.traceback import install
from dotenv import load_dotenv

from typing import Dict
import json

from cryptography.fernet import Fernet
from encryption import encrypt_api_key, decrypt_api_key

load_dotenv()

MY_API_KEY = os.getenv("MY_API_KEY")

from configuration import LOGLEVEL
from classes import SteamUser, SteamId

FORMAT = "%(message)s"
logging.basicConfig(level=LOGLEVEL,
                    format=FORMAT,
                    datefmt="[%X]",
                    handlers=[RichHandler(markup=True, rich_tracebacks=True)])
log = logging.getLogger("rich")


def init_steam_user (user_summary_json: str, user_recently_played_json) -> SteamUser:
    
    # Convert list of dictionaries to a dictionary with "appid" as the key, keeping "appid" inside the values
    games_dict = {
        int(game['appid']): game  # Converts the appid to an integer
        for game in user_recently_played_json['response']['games']
    }
    ## New user
    user = SteamUser(
        steamid= int(user_summary_json["response"]["players"][0]["steamid"]),
        personaname=user_summary_json["response"]["players"][0]["personaname"],
        profileurl=user_summary_json["response"]["players"][0]["profileurl"],
        api_key=encrypt_api_key(MY_API_KEY),
        avatar=user_summary_json["response"]["players"][0]["avatar"],
        last_game_played=0,
        last_game_played_name="",
        last_playtime=0,
        games=games_dict
    )
    try:
        with open('user_db.json', 'r+') as f:
            user_db:list[dict] = json.load(f)
            # Extract appid from db into a set for fast lookup
            app_ids_set = {g["steamid"] for g in user_db}
            if user.steamid not in app_ids_set:
                log.info (f"New user detected: {user.personaname}")
                user_db.append(user.to_dict())
                # Write back the updated list after adding a new user
                f.seek(0)  # Move file pointer to the start of the file
                json.dump(user_db, f, indent=4)
                f.truncate()  # In case the new data is smaller than the original
            else:
                log.info (f"Returning user: {user.personaname}")
    except FileNotFoundError:
        log.info ("user_db.json not found, creating it")
        with open('user_db.json', 'w') as f:
            user_db = []
            user_db:list[dict]
            user_db.append(user.to_dict())
            json.dump(user_db, f, indent=4)
            
    return user

def load_user_db() -> Dict[str, SteamUser]:
    with open('user_db.json', 'r') as f:
        user_db_list: list[dict] = json.load(f)  # Load JSON data which is a list of dictionaries

        users: Dict[int, SteamUser] = {}  # Change key type to int

        for user_data in user_db_list:
            steamid = int(user_data['steamid'])  # Ensure steamid is an integer
            
            # Convert game IDs to integers
            games = {
                int(game_id): game_info
                for game_id, game_info in user_data.get('games', {}).items()
            }
            # Create SteamUser instance with transformed games
            users[steamid] = SteamUser(
                steamid=steamid,
                personaname=user_data['personaname'],
                profileurl=user_data['profileurl'],
                api_key=encrypt_api_key(MY_API_KEY),
                avatar=user_data['avatar'],
                last_game_played=user_data['last_game_played'],
                last_game_played_name=user_data['last_game_played_name'],
                last_playtime=user_data['last_playtime'],
                games=games
            )
        return users


def update_user_db(user: SteamUser) -> None:
    with open('user_db.json', 'r+') as f:
        user_db: list[dict] = json.load(f)  # user_db is a list of dictionaries
        
        # Update the user info
        for u in user_db:
            if u.get("steamid") == user.steamid:
                u['last_game_played'] = user.last_game_played
                u['last_game_played_name'] = user.last_game_played_name
                u['last_playtime'] = user.last_playtime
                u['games'] = user.games
                #u["forever_playtime"] = user.forever_playtime
                break  # Exit the loop once the user is found

        # Move the file pointer to the beginning of the file
        f.seek(0)
        
        # Write the updated user_db back to the file
        json.dump(user_db, f, indent=4)
        
        # Truncate the file to the current size (in case the new data is shorter)
        f.truncate()


def check_latest_played_games (user: SteamUser, user_recently_played_json: dict,
                               user_last_played_times: dict) -> SteamId:
    log.info(f"Checking latest played games for {user.personaname}")
    user_db:list[SteamUser] = load_user_db()
    user.games = user_db[user.steamid].games.copy()
    last_games_played:list[SteamId] = []
    #last_playtime = user_db[user.steamid].last_playtime
    has_played = False
    # Step 1: Transform the list of games into a dictionary keyed by appid
    games_dict = {g["appid"]: g for g in user_last_played_times["response"]["games"]}
    

                
    for game in user_recently_played_json["response"]["games"]:
        last_games_played.append(game["appid"])
        if game["appid"] in games_dict:
            log.debug (f"{user.personaname} has played {game['name']}")
            # Init "last_playtime" key if not present
            if 'last_playtime' not in user_db[user.steamid].games.get(game['appid']):
                if user.last_playtime < games_dict[game["appid"]]["last_playtime"]:
                    user.last_game_played = game["appid"]
                    user.last_game_played_name = game["name"]
                    user.last_playtime = games_dict[game["appid"]]["last_playtime"]
                user.games[game['appid']]['last_playtime'] = games_dict[game["appid"]]["last_playtime"]
                update_user_db(user)
                user_db:list[SteamUser] = load_user_db()
            else:    
                # There has been a new session
                if user_db[user.steamid].last_playtime < games_dict[game["appid"]]["last_playtime"]:
                    log.info(f"New session detected: {game['name']}, playtime: {user_db[user.steamid].last_playtime}")
                    new_forever_playtime = games_dict[game["appid"]]["playtime_forever"]
                    previous_forever_playtime = user_db[user.steamid].games[game['appid']]['playtime_forever']
                    last_playtime_session = new_forever_playtime - previous_forever_playtime
                    
                    user.last_game_played = game["appid"]
                    user.last_game_played_name = game["name"]
                    user.last_playtime = games_dict[game["appid"]]["last_playtime"]
                    user.games[game['appid']]['playtime_forever'] = new_forever_playtime
                    user.games[game['appid']]['last_playtime'] = games_dict[game["appid"]]["last_playtime"]
                    #user.last_playtime = last_playtime
                    update_user_db(user)
                    user_db:list[SteamUser] = load_user_db()
                    has_played = True
            
    log.info (f"Last game played: {user_db[user.steamid].last_game_played_name}")
    if has_played:
        log.info (f"Last session playtime: {last_playtime_session} minutes for user {user.personaname}")
    else:
        log.info (f"All sessions logged for user {user.personaname}")