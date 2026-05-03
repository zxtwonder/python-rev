"""Command history persistence."""

import os

_HISTORY_FILE = os.path.expanduser("~/.rev_console_history")
_HISTORY_MAX = 500


def load_history() -> list[str]:
    try:
        with open(_HISTORY_FILE) as f:
            return [ln for ln in (line.rstrip("\n") for line in f) if ln]
    except FileNotFoundError:
        return []


def save_history(history: list[str]) -> None:
    try:
        with open(_HISTORY_FILE, "w") as f:
            for line in history[-_HISTORY_MAX:]:
                f.write(line + "\n")
    except OSError:
        pass
