import os
from discord.ext import commands
import discord
import asyncio

import logging
import configparser

import websockets
import json
import random

from dotenv import load_dotenv


# scp "C:\Users\Ripe Boi\Desktop\Programavimas\Python_learning\eve_discord_bot\main.py" admin@192.168.1.199:/C:/Users/admin/Desktop/discordBot
# scp "C:\Users\Ripe Boi\Desktop\launchDiscordBot.bat" admin@192.168.1.199:/C:/Users/admin/Desktop/

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))


def readConfig(section, key):
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
                        "**We will remember this: **"]}


@bot.command(name="subKillfeed", help="Subscribes current channel to corp killfeed")
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
        
        
@bot.command(name="subbedChannels", help="Shows all channels that are subscribed")  
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
    
    
@bot.command(name="66", help="\"Execute order 66\"")
async def killBot(context):
    if context.author.name == "GibTiddy":
        await context.message.channel.send("Shutting off")
        await bot.close()



@bot.event
async def on_ready():
    print(f"{bot.user} is connected to the following guilds:")
    
    for guild in bot.guilds:
        print(f"{guild.name}(id: {guild.id})")
    
    await bot.change_presence(activity=discord.Game("EVE Online"))
    
    await reportKillmails()
    
    
async def reportKillmails():
    # connect up with zKillFeed websocket
    while True:
        #outer loop restarted when connection fails
        
        async with websockets.connect("wss://zkillboard.com/websocket/") as websocket:
            await websocket.send(json.dumps(SUBCOMMAND))
            
            while True:
                #listener loop
                
                try:
                    # ping discord server so bot doesn't crash?
                    bot.is_closed()
                    
                    print("Receiving killmail")
                    killMail = await asyncio.wait_for(websocket.recv(), timeout=43200)
                
                except (asyncio.TimeoutError):
                    print("Connection timeout, restarting socket")
                    break
                    
                except Exception as e:
                    print(e)
                
                    #TODO DEBUG    
                    with open(os.path.join(CURRENT_PATH, "debug.txt"), "a+") as f:
                        f.write("\nCONNECTION_ERROR___________________________________")
                        f.write(repr(e))
                    print("Connection lost, restarting socket")
                    
                    break
        
        
                print("Killmail received, sending disocrd message")
                
                killMail = json.loads(kill)


                message = ""    
                if int(killMail["corporation_id"]) == int(CORPID):
                    message += random.choice(kilmailText["loss"])
                    message += "\n"
                else:
                    message += random.choice(kilmailText["win"])
                    message += "\n"
                
                message += killMail["url"]
                
                channelIDs = json.loads(readConfig("KILLMAILS", "SubscribedChannels"))
                if len(channelIDs) == 0:
                    continue
                for chID in channelIDs:
                    channel = bot.get_channel(chID)
                    await channel.send(message)
                



if __name__ == "__main__":    
    bot.run(TOKEN)

   