from bot import MondiBot
from dotenv import load_dotenv
import os

if __name__ == '__main__':
    load_dotenv()
    soundboard_bot = MondiBot(os.getenv("SOUNDS_DIR"))
    soundboard_bot.run(os.getenv("DISCORD_TOKEN"))