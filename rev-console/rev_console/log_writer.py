"""Stdout redirect to Textual's RichLog widget."""

import io

from textual.widgets import RichLog


class LogWriter(io.RawIOBase):
    """Writes to a RichLog widget, buffering until newlines."""

    def __init__(self, log: RichLog) -> None:
        self._log = log
        self._buf = ""

    def write(self, b: bytes | str) -> int:  # type: ignore[override]
        text = b if isinstance(b, str) else b.decode(errors="replace")
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self._log.write(line)
        return len(b)

    def flush(self) -> None:
        if self._buf.strip():
            self._log.write(self._buf)
            self._buf = ""
