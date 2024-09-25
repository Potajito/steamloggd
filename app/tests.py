import logging, os, requests, json
from rich.logging import RichHandler
from rich.traceback import install
from dotenv import load_dotenv
from configuration import LOGLEVEL, HEADERS
import configuration
from encryption import decrypt_key

from exceptions import APIKeyNotValid
from classes import SteamUser
from backloggd_scrapper import log_game
from steam_check import get_steam_users

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


log_game(get_steam_users(76561197960277619)[0],2666510,10)