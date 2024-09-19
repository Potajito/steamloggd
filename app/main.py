import logging, os, json
from pathlib import Path
import requests
from rich.logging import RichHandler
from rich.traceback import install
from configuration import LOGLEVEL
from steam_check import check_latest_played_games, get_steam_users
from steam.webapi import WebAPI
from apscheduler.schedulers.background import BackgroundScheduler

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


def steam_checker_scheduler_start(api: WebAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_latest_played_games, 'interval', minutes=2,
                  args=[api, get_steam_users()])

    scheduler.start()
    if scheduler.running:
        log.info("Steam Checker scheduler running")
    else:
        log.error("Steam Checker scheduler not running")

def main ():
    # Get the parent directory of the current working directory
    cwd = Path.cwd()
    # Define the path to the "db" folder in the parent directory
    db_folder = Path.joinpath(cwd, "db")
    user_db_path = Path.joinpath(db_folder, "user_db.json")
    if not db_folder.exists():
        db_folder.mkdir()
        log.info(f"Folder 'db' created at {db_folder}")
    else:
        log.info(f"Folder 'db' already exists at {db_folder}")
    if user_db_path.exists():
        log.info(f"File 'user_db.json' already exists at {user_db_path}")
    else:
        log.info ("user_db.json not found, creating it")
        with open(Path("db").joinpath("user_db.json"), 'w') as f:
            user_db = []
            user_db:list[dict]
            json.dump(user_db, f, indent=4)

    api = WebAPI(key=MY_API_KEY)
    steam_checker_scheduler_start(api)
    run_discord_bot(api)
main()