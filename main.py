import os
from discord.ext import commands
import discord
import asyncio
import configparser

import websocket
import json
import random

from dotenv import load_dotenv


# scp "C:\Users\Ripe Boi\Desktop\Programavimas\Python_learning\eve_discord_bot\main.py" admin@192.168.1.199:/C:/Users/admin/Desktop/discordBot
# scp "C:\Users\Ripe Boi\Desktop\launchDiscordBot.bat" admin@192.168.1.199:/C:/Users/admin/Desktop/

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

def readConfig(section=None, key=None):
    if section == None and key == None:
        return
    filePath = os.path.join(CURRENT_PATH, "config.ini")
    
    config = configparser.ConfigParser()
    config.optionxform = str    # makes all the keys in config file not turn to lowercase
    config.read(filePath, encoding='utf-8')   # encoding for lithuanian letters
    
    return config.get(section, key)

def writeConfig(section, key, value):
    filePath = os.path.join(CURRENT_PATH, "config.ini")
    
    config = configparser.ConfigParser()
    config.optionxform = str    # makes all the keys in config file not turn to lowercase
    config.read(filePath, encoding='utf-8')   # encoding for lithuanian letters
    config.set(section, key, value)
    
    with open(filePath, 'w', encoding='utf8') as file:   #save file
        config.write(file)

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CORPID = readConfig('KILLMAILS', 'CorpID')

bot = commands.Bot(command_prefix="-")

DEBUG = False

    
if DEBUG:
    # flood of data
    
    SUBCOMMAND = {"action":"sub","channel":"killstream"}
    #SUBCOMMAND = {"action":"sub","channel":f"corporation:{CORPID}"}
else:
    # corp kilboard
    SUBCOMMAND = {"action":"sub","channel":f"corporation:{CORPID}"}


kilmailText = {"win": ["Something blew up, and it wasn't us \\o/: ",
                       "Get outta our hole: ",
                       "Bob blessed us: ",
                       "Our killboard is turning greener \\o/: ",
                       "Get blaped: ",
                       "Booyah! Another one bites the dust: ",
                       "Back to Jita you go: "],

               "loss": ["Oh well, you win some, you lose some: ",
                        "Fuck...: ",
                        "The Bob is angry: ",
                        "Sweaty tryhards killing us: ",
                        "Clearly an unfair fight: ",
                        "Not cool: ",
                        "**Catgirl will remember this: **"]}


@bot.command(name="subKillfeed", help="Subscribes current channel to corp killfeed")
async def subscribeChannel(context):
    print(context.author.name)
    if not context.author.name == "GibTiddy":
        return
    
    channel = context.message.channel
    channelID = channel.id
    
    channels = json.loads(readConfig("KILLMAILS", "SubscribedChannels"))
    
    if not channelID in channels:
        channels.append(channelID)
        writeConfig("KILLMAILS", "SubscribedChannels", json.dumps(channels))
        await channel.send(f"Successfully subscribed channel [{channel.name}] to corp (ID: {CORPID}) killboard.")
        
    else:
        channels.remove(channelID)
        writeConfig("KILLMAILS", "SubscribedChannels", json.dumps(channels))
        await channel.send(f"Successfully unsubscribed channel [{channel.name}] from corp (ID: {CORPID}) killboard.")    


@bot.event
async def on_message(message):
    if message.guild is None and message.author != bot.user and message.content == "66":
        await message.channel.send("Shutting off")
        await bot.close()
        
    await bot.process_commands(message)


@bot.event
async def on_ready():
    print(f"{bot.user} is connected to the following guilds:")
    
    for guild in bot.guilds:
        print(f"{guild.name}(id: {guild.id})")
    
    
    await reportKillmails()
    
    
async def reportKillmails():
    ws = websocket.WebSocket()
    ws.connect("wss://zkillboard.com/websocket/", timeout=10)

    # connect up to zKillFeed
    ws.send(json.dumps(SUBCOMMAND))
    #channel = bot.get_channel(CHANNELID)

    while True:
        await asyncio.sleep(1)
        
        try:
            result = ws.recv()
            result = json.loads(result)
        except websocket.WebSocketTimeoutException:
            continue
        except (ConnectionAbortedError, websocket.WebSocketConnectionClosedException) as e:
            ws.connect("wss://zkillboard.com/websocket/", timeout=10)
            ws.send(json.dumps(SUBCOMMAND))
            continue
            
        except Exception as e:
            print(e)
            print(type(e).__name__)
            continue
        
        channelIDs = json.loads(readConfig("KILLMAILS", "SubscribedChannels"))
        if len(channelIDs) == 0:
            continue
        
        #print(result["killmail_time"])
        #print(result["zkb"]["url"])
        
        
        for chID in channelIDs:
            channel = bot.get_channel(chID)
        
            if result["victim"]["corporation_id"] == CORPID:
                await channel.send(random.choice(kilmailText["loss"]))
            else:
                await channel.send(random.choice(kilmailText["win"]))
            
            
            await channel.send(result["zkb"]["url"])
        



if __name__ == "__main__":
    bot.run(TOKEN)
    
       