"""
Central configuration for the AI-Powered SOC project.
Loads settings from a .env file (see .env.example) with sane fallbacks.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    # Ollama
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

    # Cowrie
    COWRIE_LOG_PATH = os.getenv("COWRIE_LOG_PATH", "./cowrie-data/log/cowrie.json")
    POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))

    # Where monitor.py remembers its last read position, so restarts
    # don't re-process the entire log file from the beginning.
    STATE_FILE = os.getenv("STATE_FILE", "./monitor_state.json")

    @classmethod
    def validate(cls):
        missing = []
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.TELEGRAM_CHAT_ID:
            missing.append("TELEGRAM_CHAT_ID")
        if missing:
            print(
                "[config] Warning: missing values in .env: "
                + ", ".join(missing)
                + ". Telegram alerts will fail until these are set."
            )
