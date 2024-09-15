import logging
from typing import Dict
import pprint, json, requests
from rich.logging import RichHandler
from rich.traceback import install
import configuration
from datetime import datetime
from classes import SteamUser, SteamId
from configuration import LOGLEVEL

from steam.webapi import WebAPI

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

def init_steam_user (user_summary_json: str, user_recently_played_json) -> SteamUser:
    
    # Convert list of dictionaries to a dictionary with "appid" as the key, keeping "appid" inside the values
    games_dict = {
        int(game['appid']): game  # Converts the appid to an integer
        for game in user_recently_played_json['response']['games']
    }
    user = SteamUser(
        steamid= int(user_summary_json["response"]["players"][0]["steamid"]),
        personaname=user_summary_json["response"]["players"][0]["personaname"],
        profileurl=user_summary_json["response"]["players"][0]["profileurl"],
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
        '''# First time checking, we load all recent games
        if user.last_game_played == 0:
            user.last_game_played = game["appid"]
            user.last_game_played_name = game["name"]
            user.games = user_recently_played_json["response"]["games"]
            #= games_dict[game["appid"]]["last_playtime"]
            #user.forever_playtime = games_dict[game["appid"]]["playtime_forever"]
            #last_playtime = user.last_playtime
            update_user_db(user)
            user_db = load_user_db()
        else:
        '''  
        last_games_played.append(game["appid"])
        if game["appid"] in games_dict:
            log.info (f"{user.personaname} has played {game['name']}")
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
                    #user_db[user.steamid].games.get(game['appid'])['last_playtime']
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
                    has_played = True
            
    log.info (last_games_played)
    log.info (f"Last game played: {user_db[user.steamid].last_game_played_name}")
    if has_played:
        log.info (f"Last session playtime: {last_playtime_session} minutes")
    else:
        log.info ("All sessions logged.")
def main ():
    print ("***")
    api = WebAPI(key="4B7D4B9B79B961A1698F1E2FBAD000E2")
    
    #recently_played = api.call('IPlayerService.GetRecentlyPlayedGames', steamid='76561197960277619', count=0)
    #user_summary = api.call('ISteamUser.GetPlayerSummaries', steamids='76561197960277619')
    user_summary_json = api.call('ISteamUser.GetPlayerSummaries',
                                 steamids='76561197960277619')
    user_recently_played_json = api.call('IPlayerService.GetRecentlyPlayedGames',
                                         steamid='76561197960277619', count=0)
    response = requests.get("https://api.steampowered.com/IPlayerService/ClientGetLastPlayedTimes/v1/?key=4B7D4B9B79B961A1698F1E2FBAD000E2")
    user_last_played_times = response.json()
    steam_user = init_steam_user(user_summary_json, user_recently_played_json)
    #user_last_played_times = api.call('IPlayerService.ClientGetLastPlayedTimes',
    #                                  steamid='76561197960277619')
    
    check_latest_played_games(steam_user,user_recently_played_json,
                              user_last_played_times)
    print (steam_user.personaname)
    
    #api.call('ISteamUser.ResolveVanityURL', vanityurl="valve", url_type=2)
    #api.ISteamUser.ResolveVanityURL(vanityurl="valve", url_type=2)
    #api.ISteamUser.ResolveVanityURL_v1(vanityurl="valve", url_type=2)
    
main()