import logging, os, requests, copy
from rich.logging import RichHandler
from rich.traceback import install
from dotenv import load_dotenv
from steam.webapi import WebAPI
from backloggd_scrapper import log_game
from pathlib import Path

from typing import Dict, Union
import json

from cryptography.fernet import Fernet
from encryption import encrypt_key, decrypt_key

load_dotenv()

MY_API_KEY = os.getenv("MY_API_KEY")

from configuration import LOGLEVEL
from classes import SteamUser

FORMAT = "%(message)s"
logging.basicConfig(level=LOGLEVEL,
                    format=FORMAT,
                    datefmt="[%X]",
                    handlers=[RichHandler(markup=True, rich_tracebacks=True)])
log = logging.getLogger("rich")

if logging.root.level == logging.DEBUG:
    install(show_locals=True)
else:
    install(show_locals=False)


def get_steam_users(steam_ids: Union[int, list[int], None] = None) -> list[SteamUser]:
    requested_users:list[int] = []
    with open(Path("db").joinpath("user_db.json"), 'r') as f:
        user_db: list[dict] = json.load(f)

        # Convert user_db to a dictionary where keys are steamids
        user_dict = {user["steamid"]: user for user in user_db}
        
        # If no steam_ids provided, return all users
        if steam_ids is None:
            steam_users = [SteamUser().from_dict(user) for user in user_db]
            return steam_users
        
        # If a single integer is passed, convert it to a list
        if isinstance(steam_ids, int):
            steam_ids = [steam_ids]

        steam_users: list[SteamUser] = []
        
        for steam_id in steam_ids:
            if steam_id in user_dict:
                steam_user = SteamUser().from_dict(user_dict[steam_id])
                log.debug(f"Found user: {steam_user.personaname}")
                steam_users.append(steam_user)
                requested_users.append(steam_id)
            else:
                log.warning(f"User with steamid {steam_id} not found in the database")
        log.info(f"Requested users: {requested_users}")
        return steam_users

def init_steam_user (user_summary_json: str,
                     user_recently_played_json,
                     user_api_key: str,
                     bl_user: str,
                     bl_password: str) -> SteamUser:
    
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
        api_key=encrypt_key(user_api_key),
        bl_user=bl_user,
        bl_password=encrypt_key(bl_password),
        avatar=user_summary_json["response"]["players"][0]["avatar"],
        last_game_played=0,
        last_game_played_name="",
        last_playtime=0,
        games=games_dict
    )
    try:
        with open(Path("db").joinpath("user_db.json"), 'r+') as f:
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
        with open(Path("db").joinpath("user_db.json"), 'w') as f:
            user_db = []
            user_db:list[dict]
            user_db.append(user.to_dict())
            json.dump(user_db, f, indent=4)
            
    return user

def load_user_db() -> Dict[str, SteamUser]:
    with open(Path("db").joinpath("user_db.json"), 'r') as f:
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
                api_key=user_data['api_key'],
                bl_user=user_data['bl_user'],
                bl_password=user_data['bl_password'],
                avatar=user_data['avatar'],
                last_game_played=user_data['last_game_played'],
                last_game_played_name=user_data['last_game_played_name'],
                last_playtime=user_data['last_playtime'],
                games=games.copy()
            )
        return users

def update_user_db(user: SteamUser) -> None:
    with open(Path("db").joinpath("user_db.json"), 'r+') as f:
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

def add_game (user: SteamUser, game: dict):
    user.games[game.get("appid")] = game
    update_user_db(user)
    log.info(f"Added game {game.get("name")} to {user.personaname}")

def is_playing (api: WebAPI, user:SteamUser, game_name: str):
    ## Check if user is currently playing
    user_summary_json = api.call('ISteamUser.GetPlayerSummaries',
                        steamids=str(user.steamid))
    if user_summary_json.get("response").get("players")[0].get("gameextrainfo") == str(game_name):
        log.info(f"{user.personaname} is currently playing {game_name}")
        return True
    return False

def check_latest_played_games (api:WebAPI, users: Union[SteamUser, list[SteamUser]]):
    if isinstance(users, SteamUser):
        users = [users]
    
    for user in users:
        log.info(f"Checking latest played games for {user.personaname}")
        user_recently_played_json = api.call('IPlayerService.GetRecentlyPlayedGames',
                                            steamid=user.steamid, count=0)
        response = requests.get(f"https://api.steampowered.com/IPlayerService/ClientGetLastPlayedTimes/v1/?key={decrypt_key(user.api_key)}")
        user_last_played_times = response.json()
        user_db:list[SteamUser] = load_user_db()
        user.games = user_db[user.steamid].games.copy()
        last_games_played:list[int] = []
        #last_playtime = user_db[user.steamid].last_playtime
        has_played = False
        # Step 1: Transform the list of games into a dictionary keyed by appid
        games_dict = {g["appid"]: g for g in user_last_played_times["response"]["games"]}
                    
        for game in user_recently_played_json["response"]["games"]:
            game:dict
            last_games_played.append(game["appid"])
            if game["appid"] in games_dict:
                log.debug (f"{user.personaname} has played {game.get("name")}")
                # Init "last_playtime" key if not present
                if not user_db[user.steamid].games.get(game.get("appid")):
                    log.info(f"New game: {game.get("name")}")
                    add_game(user, game)
                    user_db[user.steamid].games = user.games.copy()
                if 'last_playtime' not in user_db[user.steamid].games.get(game['appid']):
                    if user.last_playtime < games_dict[game["appid"]]["last_playtime"]:
                        user.last_game_played = game["appid"]
                        user.last_game_played_name = game["name"]
                        user.last_playtime = games_dict[game["appid"]]["last_playtime"]
                    user.games[game['appid']]['last_playtime'] = games_dict[game["appid"]]["last_playtime"]
                    update_user_db(user)
                    user_db[user.steamid] = copy.deepcopy(user)
                    #user_db:list[SteamUser] = load_user_db()
                else:    
                    # There has been a new session
                    if user_db[user.steamid].last_playtime < games_dict[game["appid"]]["last_playtime"]:
                        log.info(f"New session detected: {game['name']}, playtime: {user_db[user.steamid].last_playtime}")
                        ## Check if user is currently playing
                        if is_playing(api, user, game["name"]):
                            continue
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
                        user_db[user.steamid] = copy.deepcopy(user)
                        #user_db:list[SteamUser] = load_user_db()
                        has_played = True
                
        log.info (f"Last game played: {user_db[user.steamid].last_game_played_name}")
        if has_played:
            if last_playtime_session > 4:
                log_game(user, user_db[user.steamid].last_game_played,last_playtime_session)
                log.info (f"Last session playtime: {last_playtime_session} minutes for user {user.personaname}")
            else:
                log.info (f"Short last session playtime: {last_playtime_session} minutes, not logging")
        else:
            log.info (f"All sessions logged for user {user.personaname}")