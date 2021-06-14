# 2 8,10,13,16,19,21 * * * cd bot/like_bot/ && pipenv run python like_bot.py --min_loc 12 --max_loc 16

import argparse
import os
import random
import time

import sentry_sdk
from dotenv import load_dotenv

from core_bot import Bot
from db import DbWrapper
from xpath import xpath

load_dotenv()

# Init sentry
if os.environ.get("SENTRY_SDK_URL") and os.environ.get("ENVIRONMENT") != "developement":
    sentry_sdk.init(
        os.environ.get("SENTRY_SDK_URL"),
        traces_sample_rate=1.0,
        environment=os.environ.get("ENVIRONMENT"),
    )

# Get args
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--fast", action="store_true", help="Run script now")
parser.add_argument("-d", "--headless", action="store_true", help="Run script headless")
parser.add_argument("--min_loc", required=True, help="Min locations")
parser.add_argument("--max_loc", required=True, help="Max locations")
args = parser.parse_args()

# Wait to be more human
if not args.fast:
    time.sleep(random.randint(33, 1800))  # seconds

# Open database
base_path = os.path.dirname(os.path.realpath(__file__))
db = DbWrapper(base_path, "database.db")

if os.environ.get("ENVIRONMENT") == "production" or args.headless:
    headless = True
else:
    headless = False

# Get Discord Webhook
discord_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

# Init bot
bot = Bot(headless, db, discord_webhook_url)

# Get Instagram credentials
insta_username = os.environ.get("INSTA_USERNAME")
insta_password = os.environ.get("INSTA_PASSWORD")

# Log in Instagram
bot.login(insta_username, insta_password)


# Like cat on Instagram
bot.run(int(args.min_loc), int(args.max_loc))

bot.quit()
db.close()
