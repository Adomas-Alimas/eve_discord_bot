import asyncio
import json
import logging
import os
import random
import time

import discord
import websockets
from discord.ext import commands
from dotenv import load_dotenv
from websockets import ConnectionClosedError

# TODO remove
# scp "C:\Users\Ripe Boi\Desktop\Programavimas\Python_learning\eve_discord_bot\main.py" admin@192.168.1.199:/C:/Users/admin/Desktop/discordBot
# scp "C:\Users\Ripe Boi\Desktop\launchDiscordBot.bat" admin@192.168.1.199:/C:/Users/admin/Desktop/

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))


# loads .env file
load_dotenv()

# const settings
TOKEN = os.getenv("DISCORD_TOKEN")
CORPID = 98655191
KILLMAILCHANNELID = 850158285008404531

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
    SUBCOMMAND = {"action": "sub", "channel": "killstream"}
    SUBCOMMAND = {"action": "sub", "channel": "alliance:498125261"}
else:
    # corp kilboard
    SUBCOMMAND = {"action": "sub", "channel": f"corporation:{CORPID}"}


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
    
    
@bot.command(name="restart", help="\"Restart hosting server\"")
async def restartServer(ctx):
    # restarts server
    if ctx.author.name == "GibTiddy":
        await ctx.message.channel.send("Restarting server")
        await bot.close()
        os.system("shutdown /r")
        

@bot.command(name="66", help="\"Execute order 66\"")
async def killBot(ctx):
    # Kills bot
    if ctx.author.name == "GibTiddy":
        await ctx.message.channel.send("Shutting off")
        await bot.close()


@bot.event
async def on_ready():
    # On startup, check status, start listening for killmails
    print(f"{bot.user} is connected to the following guilds:")
    
    for guild in bot.guilds:
        print(f"{guild.name}(id: {guild.id})")
    
    await bot.change_presence(activity=discord.Game("EVE Online"))
    
    await reportKillmails()
    
    
async def reportKillmails():
    # Listener loop for getting newest killmails and
    # outputting them into subscribed channels
    
    # killmail url cache for dupe prevention
    sentUrlCache = []
    # last kill checking
    lastKillIsLoss = False
    # last killmail message ID
    lastMessageId = 0
    
    # connect up with zKillFeed websocket
    while True:
        # outer loop restarted when connection fails
        try:
            async with websockets.connect("wss://zkillboard.com/websocket/") as websocket:
                await websocket.send(json.dumps(SUBCOMMAND))
                
                while True:
                    # listener loop
                    
                    try:
                        # ping discord server so bot doesn't crash?
                        bot.is_closed()
                        
                        print("Waiting for killmail")
                        
                        loggingTimeStart = time.time()
                        killMail = await asyncio.wait_for(websocket.recv(), timeout=3600)
                    
                    except (asyncio.TimeoutError):
                        break
                        
                    except (ConnectionClosedError):
                        
                        loggingTimeEnd = time.time()
                    
                        # with open(os.path.join(CURRENT_PATH, "debug.txt"), "a+") as f:
                        #    f.write("\n\n\nCONNECTION_ERROR_1006________________________________")
                        #    f.write(f"\nTIME FROM OPEN CONN RECEIVING TO EXCEPTION [{loggingTimeEnd-loggingTimeStart}]\n")
                        #    f.write(repr(e))
                            
                        print("Connection lost, restarting socket [err 1006, good exception]")
                        break
                        
                    except Exception as e:
                        # TODO DEBUG
                        print(e)
                        
                        loggingTimeEnd = time.time()
                    
                        with open(os.path.join(CURRENT_PATH, "debug.txt"), "a+") as f:
                            f.write("\n\n\nCONNECTION_ERROR_BAD__________________________________")
                            f.write(f"\nTIME FROM OPEN CONN RECEIVING TO EXCEPTION [{loggingTimeEnd-loggingTimeStart}]\n")
                            f.write(repr(e))
                            
                        print("Connection lost, restarting socket [unknown exception, check logs]")
                        break
            
                    try:
                        killMail = json.loads(killMail)

                        # check if killmail is duplicate, if not add it to cache
                        if killMail['url'] in sentUrlCache:
                            print("Duplicate killmail, skipping discord message")
                            continue
                        else:
                            sentUrlCache.append(killMail['url'])
                            
                            # trim down cache if it gets too big
                            if len(sentUrlCache) > 10:
                                sentUrlCache.pop(0)
                                
                        print("Killmail received, sending discord message")
                        
                        # get latest message in channel id
                        channel = bot.get_channel(KILLMAILCHANNELID)
                        newestMessageId = channel.last_message_id
                        
                        # assemble message
                        message = ""
                        
                        # if previous killmails were loss dont repeat loss line, same with wins
                        # if someone excluding bot wrote a message into channel repeat loss or win line for better clarity
                        if (int(killMail["corporation_id"]) == int(CORPID)) and (lastKillIsLoss is False or not newestMessageId == lastMessageId):
                            lastKillIsLoss = True
                            
                            message += random.choice(kilmailText["loss"])
                            message += "\n"
                        elif not (int(killMail["corporation_id"]) == int(CORPID)) and (lastKillIsLoss is True or not newestMessageId == lastMessageId):
                            lastKillIsLoss = False
                            
                            message += random.choice(kilmailText["win"])
                            message += "\n"
                        
                        message += killMail["url"]
                        
                        # sending message to debuging channel
                        await bot.get_channel(851536539187019867).send(message)
                        lastMessage = await channel.send(message)
                        lastMessageId = lastMessage.id
                            
                    except Exception as e:
                        # TODO DEBUG
                        print(e)
                        
                        with open(os.path.join(CURRENT_PATH, "debug.txt"), "a+") as f:
                            f.write("\n\n\nKILLMAIL_SENDING_ERROR___________________________________\n")
                            f.write(repr(e))
                            
                        print("Error while sending killmail, restarting socket")
                        break
                    
        except Exception as e:
            # TODO DEBUG
            print(e)
            
            with open(os.path.join(CURRENT_PATH, "debug.txt"), "a+") as f:
                f.write("\n\n\nSERVER_CONNECTION_ERROR___________________________________\n")
                f.write(repr(e))
                            
            print("Error while connecting with server")
            continue
                    
                                    
if __name__ == "__main__":
    # TODO DEBUG
    open(os.path.join(CURRENT_PATH, "debug.txt"), "w").close()
    with open(os.path.join(CURRENT_PATH, "debug.txt"), "a+") as f:
        f.write("\n\n\n\n\n___________________________________")
        f.write("\n###########_NEW_SESSION_###########")
        f.write("\n___________________________________")

    bot.run(TOKEN)
