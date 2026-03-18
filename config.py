import os
from dotenv import load_dotenv

load_dotenv()

TBID_URL = os.environ["TBID_URL"]
TBID_USER_ID = os.environ["TBID_USER_ID"]
TBID_PASSWORD = os.environ["TBID_PASSWORD"]

SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 25))
NOTIFY_EMAILS = [e.strip() for e in os.environ["NOTIFY_EMAIL"].split(",")]
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "checkbid@localhost")
