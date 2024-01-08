# Ascension Discord Bot
![GitHub License](https://img.shields.io/github/license/dkoz/ascension-bot?style=flat-square) ![Discord](https://img.shields.io/discord/802778278200475658?style=flat-square&label=community) ![Discord](https://img.shields.io/discord/1009881575187566632?style=flat-square&label=support)

Discord bot for Ark: Survival Ascended

This bot was originally developed for the Newbz Evolved community. However, I've decided to make it open source. You are welcome to fork it, contribute to its code, or use it for your own server.

## Features
- **Remote RCON**: Control the server(s) directly from Discord.
- **Chat Logging**: 
  - Option to log in-game chat and commands to Discord.
- **Server Monitor**: 
  - Utilizes an EOS protocol to query the EOS API for information about your game server.
  - Embeds the information in a Discord channel of your choice.
- **Query Servers**: 
  - A general method to query game servers under the EOS API.
- **Link System**: 
  - Allows users to link their EOS IDs and SteamIDs with Discord.
  - Displays linked IDs on their profile under the bot.
- **EOS ID Search**: 
  - Since there's no direct way to search EOS IDs, a private database was created.
  - This database logs player names and IDs.
  - The bot can be used to search this database for EOS information.

## Installation (Linux)
>Requires Python 3.10+

1. Create a new user and switch to it.a
```
sudo adduser ascension
su - ascension
```
2. Clone the Arkon bot repository with the following commands
```
git clone https://github.com/dkoz/ascension-bot
cd ascension-bot
```
3. Now you need to create a virtual env and install the requirements.
```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```
4. Configure the environment variables.
```
cp .env.example .env
nano .env
```
5. Now run the bot.
```
python main.py
```
## Server Config
1. Created a `config.json` inside the data folder.

2. Contents of the `config.json`.
```
{
    "RCON_SERVERS": {
        "server1": {
            "RCON_HOST": "127.0.0.1",
            "RCON_PORT": 27020,
            "RCON_PASS": "rcon_password"
        },
        "server2": {
            "RCON_HOST": "127.0.0.1",
            "RCON_PORT": 27015,
            "RCON_PASS": "rcon_password"
        }
    }
}
```