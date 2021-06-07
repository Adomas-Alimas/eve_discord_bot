import os
import discord
import asyncio

import websocket
import json
import random

from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

DEBUG = False

CORPID = 98655191

if DEBUG:
    #test server channel id
    CHANNELID = 851510724039540749
else:
    CHANNELID = 850158285008404531
    
if DEBUG:
    SUBCOMMAND = {"action":"sub","channel":"killstream"}
else:
    SUBCOMMAND = {"action":"sub","channel":f"corporation:{CORPID}"}


kilmailText = {"win": ["Something blew up, and it wasn't us \\o/: ",
                       "Get outta our hole: ",
                       "The Bob blessed us: ",
                       "Our killboard is turning greener \\o/:"],

               "loss": ["Ah well, you win some, you lose some: ",
                        "Fuck...: ",
                        "The Bob is angry:",
                        "Sweaty tryhards killing us:"]}


client = discord.Client()


@client.event
async def on_ready():
    print(f"{client.user} is connected to the following guild:")
    
    for guild in client.guilds:
        print(f"{guild.name}(id: {guild.id})")
    
    
    await listenToKillBoard()
    
    
async def listenToKillBoard():
    ws = websocket.WebSocket()
    ws.connect("wss://zkillboard.com/websocket/")

    # connect up to zKillFeed
    ws.send(json.dumps(SUBCOMMAND))

    while True:
        
        try:
            result = json.loads(ws.recv())
        except:
            continue
        channel = client.get_channel(CHANNELID)
        
        
        await asyncio.sleep(1)
        if result["victim"]["corporation_id"] == CORPID:
            await channel.send(random.choice(kilmailText["loss"]))
        else:
            await channel.send(random.choice(kilmailText["win"]))
        
        await channel.send(result["zkb"]["url"])
        

if __name__ == "__main__":
    client.run(TOKEN)