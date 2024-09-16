import logging, os, random, datetime, requests
import re
from rich.logging import RichHandler
from rich.traceback import install
from dotenv import load_dotenv
from steam.webapi import WebAPI
from configuration import LOGLEVEL
import configuration


from exceptions import APIKeyNotValid
from classes import SteamUser
from steam_check import init_steam_user, check_latest_played_games

import discord
from discord.ext import commands, tasks


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
try:
    DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
    GUILD_ID = os.environ['GUILD_ID']
    CHANNEL_ID = int(os.environ['CHANNEL_ID'])
except:
    DISCORD_TOKEN = configuration.DISCORD_TOKEN
    GUILD_ID = configuration.GUILD_ID
    CHANNEL_ID = configuration.CHANNEL_ID
    
class UpdatesClient(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg_sent = False
        self.synced = False

    async def on_ready(self):
        channel = self.get_channel(CHANNEL_ID)  # replace with channel ID that you want to send to
        synced = await self.tree.sync()  # Syncs the slash commands with Discord
        log.debug(f"Synced {len(synced)} command(s)")
        if not self.synced:  # check if slash commands have been synced
            await self.tree.sync(guild=discord.Object(
                id=GUILD_ID))  # guild specific: leave blank if global (global registration can take 1-24 hours)
            self.synced = True
            log.info(f"Successfully logged and synced in as {self.user}")
        await self.timer.start(channel)
        
    @tasks.loop(minutes=15)
    async def timer(self, channel, force_check=False):
        #global reviews
        rand_debug = random.randrange(0,4)
        log.debug(f":stopwatch: Starting timer... Random:{rand_debug} :stopwatch:")
        log.debug(f"Is sync? {self.synced}")
        current_time = datetime.datetime.now()
        #if rand_debug == 1: # Uncomment to test
        #if (current_time.minute == 0 or current_time.minute == 15 
        #    or current_time.minute == 30 or current_time.minute == 45
        #    or force_check):
        #if (not self.msg_sent) or force_check:
        log.info (f":books: Starting review check... :books:")
        try:
            pass
        except KeyError:
            log.warning("Json file is empty")
        #reviews = rsh.get_reviews(users)
    
          
def run_discord_bot(api: WebAPI) -> None:
    

    logging.debug(f"Channel ID: {CHANNEL_ID}")
    intents = discord.Intents.default()
    intents.message_content = True
    # Connecting with Discord
        
    client = UpdatesClient(command_prefix='/', intents=discord.Intents().all())
    #channel = client.get_channel(CHANNEL_ID)
    
    tree = client.tree
    @tree.command(guild=discord.Object(id=GUILD_ID), name='add_steam_user', description='Add Steam User')  # guild specific
    async def add_user(interaction: discord.Interaction, user_input_api_key: str, user_url: str):
        
        try:
            steam_user: SteamUser = get_user(api,user_url.strip(),user_input_api_key.strip())
            await interaction.response.send_message("¡Añadido!", ephemeral=True)
        except APIKeyNotValid:
            log.error(f"Error 1: on API Key {user_input_api_key} or URL {user_url}!")
            await interaction.response.send_message("Error on API Key or URL!", ephemeral=True)
            return
                                    
        
        log.info (f"User {steam_user.personaname} added!")
        #log.info (f"New user list: {}")

        if not steam_user:
            await interaction.response.send_message("Error 2: on API Key {user_input_api_key} or URL {user_url}!", ephemeral=True)
            return
    
    @tree.command(guild=discord.Object(id=GUILD_ID), name='sync_steam', description='Sync bot (dev)')  # guild specific
    async def sync_bot(interaction: discord.Interaction):
        await tree.sync(guild=discord.Object(id=GUILD_ID))
        await interaction.response.send_message("Bot synced!", ephemeral=True)
        log.info (f"Bot synced!") 
        
    client.run(DISCORD_TOKEN)
    
    
def get_user(api:WebAPI, user_url:str, user_api_key:str) -> SteamUser:
    vanity_url_match = re.search(r'/id/([^/]+)/?$', user_url)
    if vanity_url_match:
        vanity_url = vanity_url_match.group(1)
    else:
        raise APIKeyNotValid
    
    user_api = WebAPI(key=user_api_key)
    response:dict = user_api.call('ISteamUser.ResolveVanityURL', vanityurl=vanity_url, url_type=1)
    response:dict = response.get("response")
    try:
        if response.get("success") == 1:
            user_steam_id = response["steamid"]
    except:
        raise APIKeyNotValid
    
    user_summary_json = api.call('ISteamUser.GetPlayerSummaries',
                                 steamids=user_steam_id)
    user_recently_played_json = api.call('IPlayerService.GetRecentlyPlayedGames',
                                         steamid=user_steam_id, count=0)
    
    response = requests.get(f"https://api.steampowered.com/IPlayerService/ClientGetLastPlayedTimes/v1/?key={user_api_key}")
    user_last_played_times = response.json()
    steam_user = init_steam_user(user_summary_json, user_recently_played_json)
    #user_last_played_times = api.call('IPlayerService.ClientGetLastPlayedTimes',
    #                                  steamid='76561197960277619')
    
    check_latest_played_games(steam_user,user_recently_played_json,
                              user_last_played_times)
    return steam_user
    