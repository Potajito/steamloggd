import logging, os, requests, json
from apscheduler.schedulers.background import BackgroundScheduler
from igdb.wrapper import IGDBWrapper
import re
from rich.logging import RichHandler
from rich.traceback import install
from dotenv import load_dotenv
from configuration import LOGLEVEL, HEADERS
import configuration
from typing import Union

from exceptions import APIKeyNotValid
from classes import SteamUser
import sys


FORMAT = "%(message)s"
logging.basicConfig(level=LOGLEVEL,
                    format=FORMAT,
                    datefmt="[%X]",
                    handlers=[RichHandler(markup=True, rich_tracebacks=True)])
log = logging.getLogger("rich")

# Show Tracebacks if DEBUG
if logging.root.level == logging.DEBUG:
    install(show_locals=True)
else:
    install(show_locals=False)
    
# Importing keys
IGDB_CLIENT_ID= os.getenv("IGDB_CLIENT_ID")
IGDB_SECRET= os.getenv("IGDB_SECRET")


def auth_igdb (retries:int = 3) -> str:
    """Auth to igdb, returns access token

    Returns:
        str: access_token
    """    
    url = f"https://id.twitch.tv/oauth2/token?client_id={IGDB_CLIENT_ID}&client_secret={IGDB_SECRET}&grant_type=client_credentials"
    # Make the POST request
    response = requests.post(url, headers=HEADERS)
    
# Check the status of the response
    if response.status_code == 200:
        log.info(f"IGDB Success: {response.json()}")  # If the response is JSON, you can use .json()
        # valid for around 64 days
        return response.json()['access_token']
    else:
        log.error(f"IGDB Failed: {response.status_code} {response.text}. Retrying...")
        auth_igdb(retries-1)
        sys.exit(1)
    
def igdb_scheduler_start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(auth_igdb, 'interval', days=30)
    scheduler.start()
    if scheduler.running:
        log.info("IGDB Auth scheduler running")
    else:
        log.error("IGDB Auth scheduler not running")

def decode_api_response(byte_array: bytes) -> list[dict]:
    response_str = byte_array.decode('utf-8')
    response_dict = json.loads(response_str)
    return response_dict

def steam_id_to_backloggd_url(steam_ids: Union[int, list[int]]) -> list[str]:
    return _steam_id_to_backloggd_url(steam_ids, wrapper)

def _steam_id_to_backloggd_url(steam_ids: Union[int, list[int]], wrapper: IGDBWrapper) -> list[str]:
    if isinstance(steam_ids, int):
        steam_ids = [steam_ids]
    
    backloggd_urls = []
    steam_ids_str = ",".join(f'"{str(id)}"' for id in steam_ids)
    steam_ids_str = f"({steam_ids_str})"
    igdb_gameids_from_steam = decode_api_response(wrapper.api_request(
            'external_games',
            f'fields game, name; where uid={steam_ids_str} & category = 1;'
          ))
    
    game_list = [d['game'] for d in igdb_gameids_from_steam]
    igdb_game_ids_str = ",".join(map(str, game_list))
    igdb_game_ids_str = f"({igdb_game_ids_str})"
    log.debug(igdb_game_ids_str)

    responses = decode_api_response(wrapper.api_request(
            'games',
            f'fields url, slug; where id={igdb_game_ids_str};'
            ))
    for response in responses:
        backloggd_urls.append(f"https://www.backloggd.com/games/{response.get('slug')}")    
    return backloggd_urls

access_token = auth_igdb()  # Run it immediately
igdb_scheduler_start()
api_headers = {
    'Client-ID': IGDB_CLIENT_ID,          # Replace with your actual Client ID
    'Authorization': f'Bearer {access_token}'
}
wrapper = IGDBWrapper(IGDB_CLIENT_ID, access_token)
#backloggd_urls = steam_id_to_backloggd_url([427520,1363080],wrapper)

#log.info(backloggd_urls)


