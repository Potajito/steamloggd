import logging, os

import requests
from rich.logging import RichHandler
from rich.traceback import install
import configuration
from datetime import datetime
from classes import SteamUser, SteamId
from configuration import LOGLEVEL
from steam_check import init_steam_user, check_latest_played_games
from steam.webapi import WebAPI

from dotenv import load_dotenv
from discord_steamloggd import run_discord_bot
load_dotenv()

MY_API_KEY = os.getenv("MY_API_KEY")

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


def main ():

    api = WebAPI(key=MY_API_KEY)
    run_discord_bot(api)
    #recently_played = api.call('IPlayerService.GetRecentlyPlayedGames', steamid='76561197960277619', count=0)
    #user_summary = api.call('ISteamUser.GetPlayerSummaries', steamids='76561197960277619')
    
    user_summary_json = api.call('ISteamUser.GetPlayerSummaries',
                                 steamids='76561197960277619')
    user_recently_played_json = api.call('IPlayerService.GetRecentlyPlayedGames',
                                         steamid='76561197960277619', count=0)
    response = requests.get(f"https://api.steampowered.com/IPlayerService/ClientGetLastPlayedTimes/v1/?key={MY_API_KEY}")
    user_last_played_times = response.json()
    steam_user = init_steam_user(user_summary_json, user_recently_played_json)
    check_latest_played_games(steam_user,user_recently_played_json,
                              user_last_played_times)
    
    #api.call('ISteamUser.ResolveVanityURL', vanityurl="valve", url_type=2)
    #api.ISteamUser.ResolveVanityURL(vanityurl="valve", url_type=2)
    #api.ISteamUser.ResolveVanityURL_v1(vanityurl="valve", url_type=2)
    
main()