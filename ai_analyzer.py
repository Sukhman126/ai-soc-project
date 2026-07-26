"""
Turns a completed Cowrie session (list of raw events) into a structured
AI incident report by prompting a local Ollama model.
"""
import json
import requests

from config import Config

PROMPT_TEMPLATE = """You are a SOC (Security Operations Center) analyst assistant.
Analyze the following SSH honeypot session and respond ONLY with a JSON
object (no markdown, no commentary) using exactly these keys:

{{
  "threat_level": "Low | Medium | High | Critical",
  "summary": "1-3 sentence plain-English summary of what the attacker did",
  "mitre_technique": "MITRE ATT&CK technique ID and short name, e.g. T1110 Brute Force",
  "recommendation": "1-2 concrete, actionable recommendations"
}}

Session data:
Source IP: {source_ip}
Login attempts: {login_attempts}
Successful login: {login_success}
Commands executed: {commands}
Session duration (seconds): {duration}
"""


def _extract_session_summary(events):
    """Reduce raw Cowrie events into the fields our prompt needs."""
    source_ip = "unknown"
    login_attempts = []
    login_success = False
    commands = []
    start_ts, end_ts = None, None

    for e in events:
        eid = e.get("eventid", "")
        source_ip = e.get("src_ip", source_ip)

        if eid == "cowrie.login.failed":
            login_attempts.append(f"{e.get('username')}/{e.get('password')}")
        elif eid == "cowrie.login.success":
            login_attempts.append(f"{e.get('username')}/{e.get('password')}")
            login_success = True
        elif eid == "cowrie.command.input":
            commands.append(e.get("input", ""))
        elif eid == "cowrie.session.connect":
            start_ts = e.get("timestamp")
        elif eid == "cowrie.session.closed":
            end_ts = e.get("timestamp")

    duration = "unknown"
    # Cowrie timestamps are ISO strings; keep this simple/best-effort.
    if start_ts and end_ts:
        try:
            from datetime import datetime
            fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
            t1 = datetime.strptime(start_ts, fmt)
            t2 = datetime.strptime(end_ts, fmt)
            duration = str((t2 - t1).total_seconds())
        except ValueError:
            pass

    return {
        "source_ip": source_ip,
        "login_attempts": ", ".join(login_attempts) or "none",
        "login_success": login_success,
        "commands": ", ".join(commands) or "none",
        "duration": duration,
    }


def analyze_session(events):
    """
    Sends session data to Ollama and returns a dict with keys:
    threat_level, summary, mitre_technique, recommendation.
    Falls back to a safe default structure if the model output can't be parsed.
    """
    session_summary = _extract_session_summary(events)
    prompt = PROMPT_TEMPLATE.format(**session_summary)

    payload = {
        "model": Config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    try:
        resp = requests.post(
            f"{Config.OLLAMA_HOST}/api/generate", json=payload, timeout=60
        )
        resp.raise_for_status()
        raw_text = resp.json().get("response", "").strip()
        parsed = json.loads(raw_text)
        return {
            "threat_level": parsed.get("threat_level", "Unknown"),
            "summary": parsed.get("summary", "No summary produced."),
            "mitre_technique": parsed.get("mitre_technique", "Unmapped"),
            "recommendation": parsed.get("recommendation", "Review manually."),
            "source_ip": session_summary["source_ip"],
        }
    except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
        print(f"[ai_analyzer] Ollama analysis failed: {e}")
        return {
            "threat_level": "Unknown",
            "summary": (
                f"AI analysis failed. Raw session: {session_summary['login_attempts']} "
                f"login attempts, commands: {session_summary['commands']}."
            ),
            "mitre_technique": "Unmapped",
            "recommendation": "Investigate manually; AI service unavailable.",
            "source_ip": session_summary["source_ip"],
        }
