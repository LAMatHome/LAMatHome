from dotenv import load_dotenv
import os

load_dotenv()

RH_ACCESS_TOKEN = os.getenv("RH_ACCESS_TOKEN")
FB_EMAIL = os.getenv("FB_EMAIL")
FB_PASS = os.getenv("FB_PASS")
DC_EMAIL = os.getenv("DC_EMAIL")
DC_PASS = os.getenv("DC_PASS")
G_HOME_EMAIL = os.getenv("G_HOME_EMAIL")
G_HOME_PASS = os.getenv("G_HOME_PASS")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OI_API_KEY = os.getenv("OI_API_KEY")
