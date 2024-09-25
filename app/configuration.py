import logging, os
from dotenv import load_dotenv

load_dotenv()

#.ENVS

if (os.getenv("LOGLEVEL") is None) or int(os.getenv("LOGLEVEL")) == 10:
    LOGLEVEL=logging.DEBUG
    SCHEDULER_INTERVAL= 5
else:
    LOGLEVEL = int(os.getenv("LOGLEVEL"))
    SCHEDULER_INTERVAL= 120
    ### LOGLEVELS

    #CRITICAL = 50
    #FATAL = CRITICAL
    #ERROR = 40
    #WARNING = 30
    #WARN = WARNING
    #INFO = 20
    #DEBUG = 10
    #NOTSET = 0
    
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept-Language': 'en-US,en;q=0.9'
}

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN_ENV")
GUILD_ID = os.getenv("GUILD_ID") # string
CHANNEL_ID = os.getenv("CHANNEL_ID") # int