# Vaughn Discord Bot ChatGPT
 This is a simple program (created by ChatGPT through prompting, not written by myself) which notifies to specified channels on Discord when a specified Vaughn.live streamer goes live. I'm not claiming to have written the code myself, but am sharing it here in case anyone else might find it useful.

To use:

1. Create a Discord bot and get its token. 
2. Swap placeholder values in the code with ones you want, eg. your Discord channel IDs, streamer name, bot token, your own discord ID for the debug command permmissions
3. pip install discord asyncio websockets logging
4. pm2 start vaughnbot.py