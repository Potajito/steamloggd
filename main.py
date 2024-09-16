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
    print ("***")
    api = WebAPI(key=MY_API_KEY)
    
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