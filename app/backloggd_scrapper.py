import logging, os, requests, json
import re
from rich.logging import RichHandler
from rich.traceback import install
from configuration import LOGLEVEL, HEADERS
from encryption import decrypt_key
from igdb_steamloggd import steam_id_to_backloggd_url
from classes import SteamUser
from playwright.sync_api import sync_playwright, Playwright
import traceback


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

def log_game (user: SteamUser, game_name: str, time: int) -> bool:
    
    try:
        with sync_playwright() as playwright:
            log_game_web(playwright, user.bl_user, decrypt_key(user.bl_password), game_name, time)
            return True
    except:
        log.error("Error logging game on backloggd")
        log.error(traceback.format_exc())
        return False
    

def log_game_web(playwright:Playwright, bl_user: str, bl_password: str, game_name: str, time: int):
    old_time:int = 0
    url = 'https://www.backloggd.com/users/sign_in/'

    if LOGLEVEL == logging.DEBUG:
        browser = playwright.chromium.launch(headless=False)  # Launch browser
    else:
        browser = playwright.chromium.launch(headless=True)  # Launch browser    
    
    page = browser.new_page()  # Open a new page
        
        # Navigate to the login page
    page.goto(url)
    # Fill out the login form using the IDs from the HTML
    page.fill('#user_login', f'{bl_user}')
    page.fill('#user_password', f'{bl_password}')  

     # Click the login button using the name attribute
    page.click('button[name="commit"]')
    
    page.wait_for_timeout(2000)
    
    backloggd_game_urls = steam_id_to_backloggd_url(game_name)
    log.debug(f"Trying to log game on urls: {backloggd_game_urls}")
    for url in backloggd_game_urls:
        page.goto(url)
        page.click('button[id="open-game-log-modal-btn"]')
        page.click('div[id="journal-nav"]')
        
        prev_played_buttons = page.query_selector_all('span.fc-title:has-text("Played")')
        today_cell = page.wait_for_selector('td.fc-today')
        #today_cell = page.query_selector('//td[contains(@class, "fc-today")]') # xpath version
        today_cell.click(force=True)
        page.wait_for_timeout(1000)  # short wait to give time for dynamic content to load
        current_played_buttons = page.query_selector_all('span.fc-title:has-text("Played")')
        if len(current_played_buttons) > len(prev_played_buttons): #hasn't played today
            log.debug("Newly played game today")
            played_button = current_played_buttons[-1]  # Get the last added button
            played_button.click(force=True)
            
        # Already played today, user already in log minutes screen
        minutes_field = page.wait_for_selector('input[id="play_date_minutes"]', state='visible')

        if minutes_field.input_value() == "":
            minutes_field.fill(str(time))
        else:
            old_time = int(minutes_field.input_value())
            minutes_field.fill(str(time+old_time))
        #minutes_field.fill(str(time))
        save_session_button = page.wait_for_selector('button[id="play-date-update"]')
        save_session_button.click()
        save_journal_button = page.wait_for_selector('button[class="btn btn-main save-log w-100"]')
        #page.click('button[class="btn btn-main py-1"]')
        save_journal_button.click()

        log.info(f"Backloggd log done for {game_name} for {time}.")
        log.info(f"Total today logged: {time+old_time}")

    #page.wait_for_timeout(5000)
    
    browser.close()