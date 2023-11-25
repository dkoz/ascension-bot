# Arkon Bot
Discord bot for Ark: Survival Ascended

Not sure if this will ever be made public.

# Features
- Remote RCON: You can control the server(s) directly from discord.
- Chat Logging: Option to log in-game chat and commands to the discord.
- Server Monitor: Created an EOS protocol that queries the EOS API for information on your game server. The information is embeded on a channel of your choice.
- Query Servers: Just a general way to query game servers under EOS API.
- Link System: Will allow people to link their EOS IDs and SteamIDs with discord and display it on their profile under the bot.
 - Since there isn't an actual way to search up EOS IDs, I had to create a private database that logs players names/ids then you can utilize the bot to search that database for your EOS information.

# Installation (Linux)
>Requires Python 3.10+

1. Create a new user and switch to it.
```
sudo adduser arkon
su - arkon
```
2. Clone the Arkon bot repository with the following commands
```
git clone https://github.com/dkoz/arkon
cd arkon
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

