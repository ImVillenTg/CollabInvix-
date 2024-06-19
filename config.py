import os

API_ID = API_ID = 9643564

API_HASH = os.environ.get("API_HASH", "06fc5cd597b2ba2cae0638716875e446")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "6806441353:AAHFq8DcDfMXD7z76ohDu7Nw_2NnjTQvTck")

PASS_DB = int(os.environ.get("PASS_DB", "721"))

OWNER = int(os.environ.get("OWNER", 5367287901))

LOG = -1001296608859

try:
    ADMINS=[]
    for x in (os.environ.get("ADMINS", "5367287901 1503980120 5770221234").split()):
        ADMINS.append(int(x))
except ValueError:
        raise Exception("Your Admins list does not contain valid integers.")
ADMINS.append(OWNER)


