import os
from discord.ext import commands
import discord
import asyncio
from concurrent.futures import ThreadPoolExecutor

import logging
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

DEBUG = True

    
if DEBUG:
    
    # logging
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)
    
    # flood of data
    SUBCOMMAND = {"action":"sub","channel":"killstream"}
    SUBCOMMAND = {"action":"sub","channel":f"alliance:498125261"}
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


@bot.command(name="subKillfeed", help="Subscribes current channel to corp killfeed.")
async def subscribeChannel(context):
    if not context.author.name == "GibTiddy":
        return
    
    channel = context.message.channel
    channelID = channel.id
    
    subbedChannels = json.loads(readConfig("KILLMAILS", "SubscribedChannels"))
    
    if not channelID in subbedChannels:
        subbedChannels.append(channelID)
        writeConfig("KILLMAILS", "SubscribedChannels", json.dumps(subbedChannels))
        await channel.send(f"```Successfully subscribed channel [{channel.name}] to corp (ID: {CORPID}) killboard.```")
        
    else:
        subbedChannels.remove(channelID)
        writeConfig("KILLMAILS", "SubscribedChannels", json.dumps(subbedChannels))
        await channel.send(f"```Successfully unsubscribed channel [{channel.name}] from corp (ID: {CORPID}) killboard.```")  
        
        
@bot.command(name="subbedChannels", help="Shows all channels that are subscribed.")  
async def printChannels(context):
    if not context.author.name == "GibTiddy":
        return
    
    channel = context.message.channel
    
    subbedChannels = json.loads(readConfig("KILLMAILS", "SubscribedChannels"))
    
    responseMessage = "```Following channels are subscribed to a killfeed: \n"
    for i, chID in enumerate(subbedChannels):
        ch = bot.get_channel(chID)
        responseMessage += f"({i+1}) channel_server={ch.guild.name} | channel_name={ch.name} |  channel_id={chID}\n"

    responseMessage += "```"
    await channel.send(responseMessage)
    
    
@bot.command(name="66", help="\"Execute order 66.\"")
async def killBot(context):
    if context.author.name == "GibTiddy":
        await context.message.channel.send("Shutting off")
        await bot.close()



@bot.event
async def on_ready():
    print(f"{bot.user} is connected to the following guilds:")
    
    for guild in bot.guilds:
        print(f"{guild.name}(id: {guild.id})")
    
    
    await reportKillmails()
    
    
async def reportKillmails():
    async def listenToSocket(ws):
        # async listening websocket
        result = await asyncio.get_event_loop().run_in_executor(None, ws.recv)
        return result
    
    # connect up with zKillFeed
    ws = websocket.WebSocket()
    ws.connect("wss://zkillboard.com/websocket/")

    ws.send(json.dumps(SUBCOMMAND))

    while True:
        await asyncio.sleep(1)
        
        try:
            #print("connecting")
            # ping discord server so bot no crash?
            bot.is_closed()
            result = await listenToSocket(ws)
            
            if len(result) == 0:
                continue
            result = json.loads(result)
            
            
        except websocket.WebSocketTimeoutException:
            print("Timeout exception, thsi shouldn't happen.")
            continue
            
        except (ConnectionAbortedError, websocket.WebSocketConnectionClosedException) as e:
            print("Reconnnecting...")
            ws.connect("wss://zkillboard.com/websocket/")
            ws.send(json.dumps(SUBCOMMAND))
            continue
        
        """    
        except Exception as e:
            print("EXCEPTION1 NAME:")
            print(type(e).__name__)
            print("EXCEPTION1:")
            print(e)
            
            continue
        
        #print("JSON STRING:")
        #print("______________________________________________________")
        #print(result)
        #print("______________________________________________________")
        """
        
        channelIDs = json.loads(readConfig("KILLMAILS", "SubscribedChannels"))
        if len(channelIDs) == 0:
            continue
        
        
        for chID in channelIDs:
            channel = bot.get_channel(chID)

            message = ""
            
            #if result["victim"]["corporation_id"] == CORPID:
            if result["corporation_id"] == CORPID:
                message += random.choice(kilmailText["loss"])
                message += "\n"
                
            else:
                message += random.choice(kilmailText["win"])
                message += "\n"
            
            
            #message += result["zkb"]["url"]
            message += result["url"]
            
            await channel.send(message)
        



if __name__ == "__main__":
    
    bot.run(TOKEN)

   