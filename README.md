# AI-Powered Security Operations Center (SOC)

Automatically detects, analyzes, and reports attacks against an SSH honeypot
using Cowrie, a local LLM (via Ollama), and Telegram alerts.

```
Kali VM (attacker) --SSH--> Cowrie (Docker) --logs--> cowrie.json
                                                          |
                                                     monitor.py
                                                          |
                                                    Ollama (llama3.2)
                                                          |
                                                    Telegram Bot API
                                                          |
                                                 Security Administrator
```


<img width="2720" height="3008" alt="ai_soc_architecture" src="https://github.com/user-attachments/assets/a7c3fe25-da29-496e-b9ef-281c73351be6" />


## 1. Prerequisites

- Docker Desktop (or Docker Engine) installed and running
- Python 3.9+
- [Ollama](https://ollama.com) installed on the host
- A Telegram bot token (create one via [@BotFather](https://t.me/BotFather))
- Optional: a Kali Linux VM (or any machine) to act as the attacker

## 2. Setup

### a. Clone / place the project files

Make sure you have this structure:

```
ai-soc-project/
├── docker-compose.yml
├── monitor.py
├── config.py
├── cowrie_watcher.py
├── ai_analyzer.py
├── telegram_notifier.py
├── requirements.txt
├── .env.example
└── README.md
```

### b. Install Python dependencies

```bash
pip install -r requirements.txt
```

### c. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

- `TELEGRAM_BOT_TOKEN` — from @BotFather
- `TELEGRAM_CHAT_ID` — message [@userinfobot](https://t.me/userinfobot) to get your chat ID
  (or add the bot to a group and use the group's chat ID)

### d. Start Ollama and pull the model

```bash
ollama serve          # if not already running as a service
ollama pull llama3.2
```

### e. Start the Cowrie honeypot container

```bash
docker compose up -d
```

This starts Cowrie listening on `localhost:2222` (fake SSH) and writes logs to
`./cowrie-data/log/cowrie.json` on the host, which `monitor.py` reads.

Check it's running:

```bash
docker compose ps
docker compose logs -f cowrie
```

### f. Start the monitor

```bash
python monitor.py
```

You should see:

```
[monitor] Monitoring ./cowrie-data/log/cowrie.json every 5s ...
```




<img width="704" height="269" alt="Terminal running monitor py" src="https://github.com/user-attachments/assets/c038f98e-af7f-40f6-8d4d-d8e7d57c8bea" />


## 3. Generating a test attack

From another machine (e.g. a Kali VM) or the same host:

```bash
ssh root@<docker-host-ip> -p 2222
```

Enter any username/password — Cowrie will accept it as a fake login, log the
session, and let the "attacker" run commands in a sandboxed fake filesystem.


<img width="775" height="429" alt="The SSH attack in progress" src="https://github.com/user-attachments/assets/b4226e7f-a1da-4478-95ed-1a57e15938a4" />

Once the session ends (or times out), `monitor.py` will:

1. Detect the closed session in `cowrie.json`
2. Send the session details to Ollama for analysis
3. Post a formatted incident report to your Telegram chat, e.g.:

```
🚨 Security Incident Detected

🟠 Threat Level: High
Source IP: 203.0.113.5
Session: abc123


![Uploading The Telegram alert itself.png…]()


Summary:
Attacker brute-forced SSH credentials, logged in as root,
and inspected system files.

MITRE ATT&CK: T1110 Brute Force

Recommendation:
Block source IP and enforce key-based SSH auth.
```

## 4. How it works (file by file)

| File | Role |
|---|---|
| `docker-compose.yml` | Runs the Cowrie honeypot container and persists its logs to the host |
| `config.py` | Loads all settings from `.env` |
| `cowrie_watcher.py` | Tails `cowrie.json`, groups events by session ID, yields completed sessions. Remembers its file position across restarts (`monitor_state.json`) so it never reprocesses old logs |
| `ai_analyzer.py` | Builds a structured prompt from a session's events and asks Ollama for a JSON incident report (threat level, summary, MITRE technique, recommendation) |
| `telegram_notifier.py` | Formats the AI's analysis into a readable message and posts it via the Telegram Bot API |
| `monitor.py` | Orchestrates the above in a continuous loop |

## 5. Security considerations

- **Never expose Cowrie or Ollama to the public internet** — run this in an
  isolated lab/VM network only.
- Keep your `.env` file out of version control (already covered by
  `.gitignore` below) — it contains your Telegram bot token.
- Rotate your Telegram bot token if it's ever committed or leaked.
- Keep Cowrie and Ollama images/models updated.

Add a `.gitignore` with at least:

```
.env
cowrie-data/
monitor_state.json
__pycache__/
```

## 6. Future improvements

- Web dashboard (Flask) for browsing past incidents
- VirusTotal / AbuseIPDB / GeoIP enrichment of source IPs
- PDF incident reports
- Database storage (SQLite/Postgres) instead of flat-file state
- Multiple honeypot types (Dionaea, Glutton, etc.) feeding the same pipeline
- Email alerting alongside Telegram

## 7. Skills demonstrated

Cybersecurity, honeypots, SSH, incident response, SOC operations, threat
detection, MITRE ATT&CK mapping, log analysis, Python, REST APIs, JSON,
LLM prompting and integration, Docker, Git/GitHub.
