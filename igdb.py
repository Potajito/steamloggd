import logging, os, requests
import re
from rich.logging import RichHandler
from rich.traceback import install
from dotenv import load_dotenv
from configuration import LOGLEVEL, HEADERS
import configuration


from exceptions import APIKeyNotValid
from classes import SteamUser


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


def auth_igdb ():
    url = f"https://id.twitch.tv/oauth2/token?client_id={IGDB_CLIENT_ID}&client_secret={IGDB_SECRET}&grant_type=client_credentials"
    # Make the POST request
    response = requests.post(url, headers=HEADERS)

# Check the status of the response
    if response.status_code == 200:
        log.info(f"IGDB Success: {response.json()}")  # If the response is JSON, you can use .json()
    else:
        log.error(f"IGDB Failed: {response.status_code} {response.text}")

auth_igdb()
