import discord
import asyncio
import websockets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Discord bot token
DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"

# Channel IDs to send live notifications
DISCORD_CHANNEL_IDS = [YOUR_CHANNEL_ID_HERE, YOUR_CHANNEL_ID_HERE_2]

# Vaughn live user to monitor
VAUGHN_USERNAME = "YOUR_VAUHGN_USERNAME_HERE"

# WebSocket server for Vaughn
VAUGHN_WEBSOCKET_URL = "wss://sapi-ws-1x01.vaughnsoft.net/mvn"

# Keep WebSocket connection alive
KEEPALIVE_INTERVAL = 30  # seconds
STREAM_CHECK_INTERVAL = 5  # seconds

# Initialize the Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Global flag to track live status
last_live_status = False


async def monitor_vaughn():
    """Monitor Vaughn live WebSocket for user status."""
    global last_live_status
    while True:
        try:
            async with websockets.connect(VAUGHN_WEBSOCKET_URL, ping_interval=None) as websocket:
                logging.info("Connected to Vaughn live WebSocket")

                # Send initial load command
                await websocket.send(f"MVN LOAD3 #vl-{VAUGHN_USERNAME} guest guest\n\0")
                
                # Task to send PONG messages regularly
                async def send_keepalive():
                    while True:
                        try:
                            logging.debug("Sending PONG to keep connection alive")
                            await websocket.send("PONG\n\0")
                            await asyncio.sleep(KEEPALIVE_INTERVAL)
                        except Exception as e:
                            logging.warning(f"Keepalive error: {e}")
                            break

                # Task to periodically check stream status
                async def check_stream_status():
                    while True:
                        try:
                            logging.debug("Requesting stream status")
                            await websocket.send(f"MVN STREAM3 #vl-{VAUGHN_USERNAME}\n\0")
                            await asyncio.sleep(STREAM_CHECK_INTERVAL)
                        except Exception as e:
                            logging.warning(f"Stream status error: {e}")
                            break

                # Start tasks
                keepalive_task = asyncio.create_task(send_keepalive())
                status_check_task = asyncio.create_task(check_stream_status())

                while True:
                    message = await websocket.recv()
                    message = message.replace("\n", "").replace("\0", "")
                    logging.debug(f"Received WebSocket message: {message}")

                    if message.startswith("STREAM3 "):
                        # Parse the response
                        parts = message.split(" ")[1].split(";")
                        if len(parts) > 9:
                            is_live = parts[6] == "1"  # Check if the stream is live
                            if is_live and not last_live_status:
                                last_live_status = True
                                await send_discord_notifications(
                                    f"🔴 {VAUGHN_USERNAME} is now live on Vaughn! Check it out: https://vaughn.live/{VAUGHN_USERNAME}"
                                )
                            elif not is_live and last_live_status:
                                last_live_status = False
                    elif message == "PING":
                        # Respond to server PING
                        logging.info("Responding to server PING")
                        await websocket.send("PONG\n\0")
        except Exception as e:
            logging.error(f"Error in Vaughn monitor: {e}")
            await asyncio.sleep(5)  # Wait and reconnect on error


async def send_discord_notifications(message):
    """Send live notification to Discord channels."""
    for channel_id in DISCORD_CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                await channel.send(message)
            except Exception as e:
                logging.error(f"Failed to send message to channel {channel_id}: {e}")


@bot.event
async def on_ready():
    """Start monitoring Vaughn when the bot is ready."""
    logging.info(f"Logged in as {bot.user}")
    bot.loop.create_task(monitor_vaughn())


@bot.event
async def on_message(message):
    """Handle incoming messages."""
    # Restrict the ~debugvaughn command to a specific user
    if message.content == "~debugvaughn":
        if message.author.id != YOUR_DISCORD_USER_ID_HERE:
            await message.channel.send("⚠️ You do not have permission to use this command.")
            logging.warning(f"Unauthorized access attempt by user {message.author.id}")
            return
        
        embed = discord.Embed(
            title="🔴 STREAMERNAME is Live!",
            description="This is a test message. Streamername is not actually live.",
            url=f"https://vaughn.live/{VAUGHN_USERNAME}",
            color=0xFF0000
        )
        for channel_id in DISCORD_CHANNEL_IDS:
            channel = bot.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(embed=embed)
                    logging.info(f"Debug embed sent to channel {channel_id}")
                except Exception as e:
                    logging.error(f"Failed to send embed to channel {channel_id}: {e}")



# Run the Discord bot
bot.run(DISCORD_TOKEN)
