# Steamloggd	

**Steamloggd** is an app that tracks users on Steam and posts their play sessions on [backloggd](https://www.backloggd.com/) journal.
To interface with the bot (add or remove users) it uses a Discord bot that asks the user their Steam Web API and backloggd user and password (sadly, I don't think there is a safe way to do this without asking these credentials, but as you are supposed to self-host this, shouldn't be a big deal).  

## Packages
There is a provided docker package that builds with each master git commit, you only need to setup the env variables on the compose file.

## To-do
- Remove users
- Better error handling
- Optimize multiple user logging on backloggd
