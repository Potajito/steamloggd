import logging, os, requests, copy, re
from requests import Session
from rich.logging import RichHandler
from rich.traceback import install
from playwright.sync_api import sync_playwright, Playwright, Page, ElementHandle, Browser
import traceback

from dotenv import load_dotenv
from igdb_steamloggd import match_non_steam_game_name_to_igdb

load_dotenv()

MY_API_KEY = os.getenv("MY_API_KEY")
STEAM_USERNAME = os.getenv("STEAM_USERNAME")
STEAM_PASSWORD = os.getenv("STEAM_PASSWORD")

from configuration import LOGLEVEL, SCHEDULER_INTERVAL, HEADERS
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
    
import requests
from bs4 import BeautifulSoup

def steam_login (page: Page) -> Page:
    login_url = "https://steamcommunity.com/login/home"
    try:      
        #page = browser.new_page()  # Open a new page
    
            # Navigate to the login page
        page.goto(login_url)
        # Fill out the login form using the IDs from the HTML
        # Locate the input field using text selector
        username_div = page.get_by_text("Sign in with account name")
        user_input_field = username_div.locator('xpath=following-sibling::input')
        password_div = page.get_by_text("Password")
        password_input_field = password_div.locator('xpath=following-sibling::input')
        
        # Interact with the input field (e.g., type text)
        user_input_field.fill(STEAM_USERNAME)
        password_input_field.fill(STEAM_PASSWORD)
        page.click('button[type="submit"]')
        #page.wait_for_timeout(3000)
        #page.close()
        return page
    except:
        log.error("Error logging in Steam")
        log.error(traceback.format_exc())
        return None
    

def extract_game_name(page: Page, url: str) -> str:

    # Send a GET request to the page
    page.goto(url)

    # Find the div with class "profile_in_game"
    #profile_ingame: ElementHandle = page.query_selector('div', class_='profile_in_game persona in-game')
    non_steam_game: ElementHandle = page.query_selector('div.profile_in_game_header')
    if non_steam_game and non_steam_game.text_content() == 'In non-Steam game': 
        game_name_div: ElementHandle = page.query_selector('div.profile_in_game_name')
        game_name = game_name_div.text_content().strip()
        log.info(f"Game name: {game_name}")
        return game_name
    else:
        log.error("Not in a non-Steam game page")
        return None

def _start_non_steam_check():
    with sync_playwright() as playwright:
        if LOGLEVEL == logging.DEBUG:
            browser = playwright.chromium.launch(headless=False)  # Launch browser
        else:
            browser = playwright.chromium.launch(headless=True)  # Launch browser
        page = steam_login(browser)
        if page:
            non_steam_game_name = extract_game_name(page, "https://steamcommunity.com/id/potajito/")
            if isinstance(non_steam_game_name, str):
                igdb_game_dict = match_non_steam_game_name_to_igdb(non_steam_game_name)
                log.debug(igdb_game_dict)
        else:
            log.error("Error logging in Steam")

def start_non_steam_check(page: Page, user: SteamUser):
        page = steam_login(page)
        if page:
            non_steam_game_name = extract_game_name(page, user.profileurl)
            if isinstance(non_steam_game_name, str):
                igdb_game_dict = match_non_steam_game_name_to_igdb(non_steam_game_name)
                log.debug(igdb_game_dict)
        else:
            log.error("Error logging in Steam")
               
#start_non_steam_browser()

