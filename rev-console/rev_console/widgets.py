"""Textual widgets for the rev-console watch panel."""

from typing import cast

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Label, Static

from rev_console.commands import CommandCallable


class _CloseButton(Static):
    """Clickable × label that closes its parent watch."""

    def __init__(self, watch_id: int) -> None:
        super().__init__("×", classes="close-btn")
        self._watch_id = watch_id

    def on_click(self, event: events.Click) -> None:
        event.stop()
        from rev_console.app import RevConsoleApp as _App  # local import breaks cycle

        cast(_App, self.app).close_watch(self._watch_id)


class WatchWidget(Static):
    """A single auto-refreshing value in the watch panel."""

    value: reactive[str] = reactive("—", init=False)

    def __init__(
        self, watch_id: int, label: str, reader: CommandCallable, rate: float
    ) -> None:
        super().__init__(id=f"watch-{watch_id}")
        self.watch_id = watch_id
        self._label = label
        self._reader = reader
        self._rate = rate

    def compose(self) -> ComposeResult:
        with Horizontal(classes="watch-header"):
            yield Label(f"[{self.watch_id}] {self._label}", classes="watch-name")
            yield _CloseButton(self.watch_id)
        yield Label("—", id=f"wv-{self.watch_id}", classes="watch-value")

    def on_mount(self) -> None:
        self.set_interval(1.0 / self._rate, self._poll)

    async def _poll(self) -> None:
        try:
            self.value = await self._reader()
        except Exception as e:
            self.value = f"err: {e}"

    def watch_value(self, val: str) -> None:
        try:
            self.query_one(f"#wv-{self.watch_id}", Label).update(val)
        except Exception:
            pass  # widget not yet mounted on first reactive fire


class WatchPanel(VerticalScroll):
    """Right-side panel containing all active watch widgets."""

    def compose(self) -> ComposeResult:
        yield Label("Watches", classes="panel-title")
