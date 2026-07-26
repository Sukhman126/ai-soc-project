"""
monitor.py - Entry point for the AI-Powered SOC.

Watches Cowrie's cowrie.json, and for every completed attacker session:
  1. Extracts the attack details (source IP, credentials tried, commands run)
  2. Sends them to a local Ollama model for analysis
  3. Sends the resulting incident report to Telegram

Usage:
    python monitor.py
"""
import sys

from config import Config
from cowrie_watcher import CowrieWatcher
from ai_analyzer import analyze_session
from telegram_notifier import send_telegram_alert


def handle_session(session_id, events):
    print(f"[monitor] New session closed: {session_id} ({len(events)} events)")
    analysis = analyze_session(events)
    print(
        f"[monitor] Threat level: {analysis['threat_level']} | "
        f"IP: {analysis['source_ip']}"
    )
    send_telegram_alert(analysis, session_id)


def main():
    Config.validate()
    watcher = CowrieWatcher()
    try:
        watcher.watch_forever(handle_session)
    except KeyboardInterrupt:
        print("\n[monitor] Stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
