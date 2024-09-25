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
        
        # Locate the third <div> with the class 'fc-row fc-week fc-widget-content'
        third_div = page.locator('div.fc-row.fc-week.fc-widget-content:nth-of-type(3)')

        # Inside that <div>, find <tbody>
        tbody = third_div.locator('tbody')

        # Inside <tbody>, find <tr>
        tr = tbody.locator('tr')

        # Inside <tr>, find the 4th <td> with the class 'fc-event-container'
        fourth_td = tr.locator('td.fc-event-container:nth-of-type(4)')

        # Inside that <td>, find the <a> button
        played_button = fourth_td.locator('a.fc-day-grid-event.fc-h-event.fc-event.fc-start.fc-end.fc-draggable.fc-resizable')
        if played_button.is_visible():
            log.debug("Already logged sessions, trying to update session")
            played_button.click()
            minutes_field = page.wait_for_selector('input[id="play_date_minutes"]', state='visible')
            old_time = int(minutes_field.input_value())
            minutes_field.fill(str(time+old_time))
            page.click('button[class="btn btn-main py-1"]')
            page.click('button[class="btn btn-main save-log w-100"]')
        else:
            log.debug("Newly played game today")
            today_cell = page.wait_for_selector('td.fc-today')
            #today_cell = page.query_selector('//td[contains(@class, "fc-today")]') # xpath version
            log.debug(today_cell.inner_html())
            today_cell.click(force=True)
            #new_span = page.wait_for_selector('span[class="fc-title"]', state='visible')
            #new_span.click()
            minutes_field = page.wait_for_selector('input[id="play_date_minutes"]', state='visible')
            minutes_field.fill(str(time))
            page.click('button[class="btn btn-main py-1"]')
            page.click('button[class="btn btn-main save-log w-100"]')

        log.info(f"Backloggd log done for {game_name} for {time}.")
        log.info(f"Total today logged: {time+old_time}")

    #page.wait_for_timeout(5000)
    
    browser.close()