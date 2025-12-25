import os
from dotenv import load_dotenv

load_dotenv()
print(f"DEBUG: URI is {os.getenv('DATABASE_URI')}")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MQTT_BROKER = os.getenv("MQTT_BROKER")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    AUDIO_PATH = os.getenv("AUDIO_PATH", "./local/audio")