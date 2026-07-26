"""
Watches Cowrie's cowrie.json log file for new events, groups them by
session ID, and yields a completed session's event list once Cowrie
reports that session as closed.

Cowrie writes one JSON object per line ("JSON lines" format). Relevant
event ids include:
    cowrie.session.connect
    cowrie.login.failed
    cowrie.login.success
    cowrie.command.input
    cowrie.session.closed
"""
import json
import os
import time
from collections import defaultdict

from config import Config


class CowrieWatcher:
    def __init__(self, log_path=None, state_file=None):
        self.log_path = log_path or Config.COWRIE_LOG_PATH
        self.state_file = state_file or Config.STATE_FILE
        self.sessions = defaultdict(list)
        self._file_pos = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f).get("file_pos", 0)
            except (json.JSONDecodeError, OSError):
                return 0
        return 0

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump({"file_pos": self._file_pos}, f)

    def _read_new_lines(self):
        """Read any lines appended to cowrie.json since the last check."""
        if not os.path.exists(self.log_path):
            return []

        with open(self.log_path, "r") as f:
            f.seek(self._file_pos)
            new_lines = f.readlines()
            self._file_pos = f.tell()

        self._save_state()
        return new_lines

    def poll_once(self):
        """
        Process any new log lines. Returns a list of completed sessions,
        where each item is (session_id, list_of_events).
        """
        completed = []

        for line in self._read_new_lines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            session_id = event.get("session")
            if not session_id:
                continue

            self.sessions[session_id].append(event)

            if event.get("eventid") == "cowrie.session.closed":
                completed.append((session_id, self.sessions.pop(session_id)))

        return completed

    def watch_forever(self, on_session_complete, poll_interval=None):
        """Blocking loop: calls on_session_complete(session_id, events) for
        every session that closes."""
        interval = poll_interval or Config.POLL_INTERVAL
        print(f"[watcher] Monitoring {self.log_path} every {interval}s ...")
        while True:
            for session_id, events in self.poll_once():
                on_session_complete(session_id, events)
            time.sleep(interval)
