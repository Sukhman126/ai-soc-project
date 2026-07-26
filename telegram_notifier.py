"""
Sends formatted security incident alerts to Telegram via the Bot API.
"""
import requests

from config import Config

THREAT_EMOJI = {
    "Low": "🟢",
    "Medium": "🟡",
    "High": "🟠",
    "Critical": "🔴",
    "Unknown": "⚪",
}


def format_alert(analysis, session_id):
    emoji = THREAT_EMOJI.get(analysis["threat_level"], "⚪")
    return (
        f"🚨 *Security Incident Detected*\n\n"
        f"{emoji} *Threat Level:* {analysis['threat_level']}\n"
        f"*Source IP:* `{analysis['source_ip']}`\n"
        f"*Session:* `{session_id}`\n\n"
        f"*Summary:*\n{analysis['summary']}\n\n"
        f"*MITRE ATT&CK:* {analysis['mitre_technique']}\n\n"
        f"*Recommendation:*\n{analysis['recommendation']}"
    )


def send_telegram_alert(analysis, session_id):
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        print("[telegram] Skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        return False

    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": Config.TELEGRAM_CHAT_ID,
        "text": format_alert(analysis, session_id),
        "parse_mode": "Markdown",
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        print("[telegram] Alert sent.")
        return True
    except requests.RequestException as e:
        print(f"[telegram] Failed to send alert: {e}")
        return False
