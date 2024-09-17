import logging, os, requests, json
import re
from rich.logging import RichHandler
from rich.traceback import install
from dotenv import load_dotenv
from configuration import LOGLEVEL, HEADERS
import configuration


from exceptions import APIKeyNotValid
from classes import SteamUser

import requests
from playwright.sync_api import sync_playwright, Playwright


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
    

def log_game(playwright:Playwright, bl_user: str, bl_password: str, game_name: str, time: int):
    url = 'https://www.backloggd.com/users/sign_in/'

    browser = playwright.chromium.launch(headless=False)  # Launch browser
    page = browser.new_page()  # Open a new page
        
        # Navigate to the login page
    page.goto(url)
    # Fill out the login form using the IDs from the HTML
    page.fill('#user_login', f'{bl_user}')
    page.fill('#user_password', f'{bl_password}')  

     # Click the login button using the name attribute
    page.click('button[name="commit"]')
    
    page.wait_for_timeout(2000)
    
    page.goto(f"https://www.backloggd.com/games/{game_name}/")
    page.click('button[id="open-game-log-modal-btn"]')
    page.click('div[id="journal-nav"]')
    page.click('td[class="fc-day fc-widget-content fc-tue fc-today "]')
    
    # Wait for the new span element to appear
    # This assumes the new span will be the only visible one after the click
    new_span = page.wait_for_selector('span[class="fc-title"]', state='visible')
    
    new_span.click()
    minutes_field = page.wait_for_selector('input[id="play_date_minutes"]', state='visible')
    minutes_field.fill(str(time))
    page.click('button[class="btn btn-main py-1"]')

    
    # Check if login was successful
    #page.wait_for_timeout(5000)
    
    browser.close()
    
#with sync_playwright() as playwright:
#    log_game(playwright,"satisfactory",30)