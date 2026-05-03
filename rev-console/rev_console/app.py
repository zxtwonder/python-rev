"""RevConsoleApp — Textual TUI for rev-console."""

import asyncio
import shlex
import sys
from typing import Any

from textual import events, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Input, RichLog

from rev_core.expansion_hub import ExpansionHub

from rev_console.commands import (
    AnalogCommand,
    BatteryCommand,
    BulkInputCommand,
    Command,
    CommandCallable,
    DigitalBusCurrentCommand,
    DigitalCommand,
    DistanceCommand,
    FailsafeCommand,
    GetLedCommand,
    GetPatternCommand,
    HelpCommand,
    I2cCurrentCommand,
    LedSetCommand,
    LogCommand,
    LoglevelCommand,
    MotorCommand,
    PatternCommand,
    QueryCommand,
    ServoCommand,
    ServoCurrentCommand,
    TemperatureCommand,
    Voltage5vCommand,
    VersionCommand,
    WatchCommand,
)
from rev_console.history import load_history, save_history
from rev_console.log_writer import LogWriter
from rev_console.widgets import WatchPanel, WatchWidget, _APP_CSS


class RevConsoleApp(App[None]):
    CSS = _APP_CSS

    BINDINGS = [
        Binding("ctrl+c", "cancel_command", "Cancel", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    def __init__(self, hub: ExpansionHub) -> None:
        super().__init__()
        self.hub = hub
        self._watches: dict[int, WatchWidget] = {}
        self._next_watch_id = 1
        self._history: list[str] = []
        self._history_pos = 0
        self._cmd_lock = asyncio.Lock()
        self._continuous_task: asyncio.Task[Any] | None = None
        self._command_registry = self._build_command_registry()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main"):
            with Vertical(id="left"):
                yield RichLog(id="output", wrap=True, highlight=True, markup=True)
                yield Input(placeholder="rev-hub> ", id="cmd-input")
            yield WatchPanel(id="watch-panel")

    def on_mount(self) -> None:
        log = self.query_one("#output", RichLog)
        sys.stdout = LogWriter(log)  # type: ignore[assignment]
        self._output = log
        self.hub.on("error", lambda e: self.write(f"[red]Hub error: {e}[/red]"))
        self._history = load_history()
        self._history_pos = len(self._history)
        self.query_one("#cmd-input").focus()
        self.write(
            "[bold]Connected.[/bold] Type [cyan]help[/cyan] for commands, "
            "[cyan]Ctrl+Q[/cyan] to quit."
        )

    def on_unmount(self) -> None:
        sys.stdout = sys.__stdout__
        save_history(self._history)

    # ── Output ────────────────────────────────────────────────────────────────

    def write(self, text: str) -> None:
        self._output.write(text)

    # ── Input handling ────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        line = event.value.strip()
        event.input.clear()
        if not line:
            return
        if not self._history or self._history[-1] != line:
            self._history.append(line)
        self._history_pos = len(self._history)
        self._run_command(line)

    def on_key(self, event: events.Key) -> None:
        inp = self.query_one("#cmd-input", Input)
        if self.focused is not inp:
            return
        if event.key == "up":
            event.prevent_default()
            if self._history_pos > 0:
                self._history_pos -= 1
                inp.value = self._history[self._history_pos]
                inp.cursor_position = len(inp.value)
        elif event.key == "down":
            event.prevent_default()
            if self._history_pos < len(self._history) - 1:
                self._history_pos += 1
                inp.value = self._history[self._history_pos]
            else:
                self._history_pos = len(self._history)
                inp.value = ""
            inp.cursor_position = len(inp.value)

    def action_cancel_command(self) -> None:
        if self._continuous_task and not self._continuous_task.done():
            self._continuous_task.cancel()
        else:
            self.write("[dim]^C[/dim]")

    async def action_quit(self) -> None:
        self.exit()

    # ── Command worker ────────────────────────────────────────────────────────

    @work(exclusive=False)
    async def _run_command(self, line: str) -> None:
        self.write(f"[dim]> {line}[/dim]")
        try:
            tokens = shlex.split(line)
        except ValueError as e:
            self.write(f"[red]Parse error: {e}[/red]")
            return
        if tokens[0] in ("exit", "quit"):
            self.exit()
            return
        async with self._cmd_lock:
            try:
                await self._dispatch(tokens)
            except Exception as e:
                self.write(f"[red]Error: {e}[/red]")

    # ── Command execution ─────────────────────────────────────────────────────

    async def _execute_action(self, call: CommandCallable) -> None:
        """Run call() as a cancellable task. Ctrl+C cancels long-running calls."""
        task: asyncio.Task[Any] = asyncio.create_task(call())
        self._continuous_task = task
        try:
            result = await task
            if result:
                print(result)
        except asyncio.CancelledError:
            print("(stopped)")
        finally:
            self._continuous_task = None

    # ── Watch management ──────────────────────────────────────────────────────

    async def add_watch(self, label: str, reader: CommandCallable, rate: float) -> int:
        watch_id = self._next_watch_id
        self._next_watch_id += 1
        widget = WatchWidget(watch_id, label, reader, rate)
        panel = self.query_one("#watch-panel", WatchPanel)
        await panel.mount(widget)
        panel.display = True
        self._watches[watch_id] = widget
        return watch_id

    def close_watch(self, watch_id: int) -> str:
        widget = self._watches.pop(watch_id, None)
        if widget is None:
            return f"No watch [{watch_id}]."
        widget.remove()
        if not self._watches:
            self.query_one("#watch-panel", WatchPanel).display = False
        return f"Watch [{watch_id}] closed."

    # ── Command registry ──────────────────────────────────────────────────────

    def _build_command_registry(self) -> dict[str, Command]:
        hub = self.hub
        reg: dict[str, Command] = {
            "temperature": TemperatureCommand(hub),
            "5vRailVoltage": Voltage5vCommand(hub),
            "i2c-current": I2cCurrentCommand(hub),
            "digital-current": DigitalBusCurrentCommand(hub),
            "servo-current": ServoCurrentCommand(hub),
            "bulkInput": BulkInputCommand(hub),
            "analog": AnalogCommand(hub),
            "battery": BatteryCommand(hub),
            "digital": DigitalCommand(hub),
            "motor": MotorCommand(hub),
            "servo": ServoCommand(hub),
            "distance": DistanceCommand(hub),
            "led": LedSetCommand(hub),
            "get-led": GetLedCommand(hub),
            "pattern": PatternCommand(hub),
            "get-pattern": GetPatternCommand(hub),
            "version": VersionCommand(hub),
            "query": QueryCommand(hub),
            "log": LogCommand(hub),
            "loglevel": LoglevelCommand(hub),
            "failsafe": FailsafeCommand(hub),
        }
        reg["watch"] = WatchCommand(
            registry=reg,
            add_fn=self.add_watch,
            close_fn=self.close_watch,
            watches=self._watches,
        )
        reg["help"] = HelpCommand(registry=reg)
        return reg

    async def _dispatch(self, tokens: list[str]) -> None:
        cmd_name = tokens[0]
        command = self._command_registry.get(cmd_name)
        if command is None:
            self.write(
                f"Unknown command: [yellow]{cmd_name!r}[/yellow]. "
                f"Type [cyan]help[/cyan] for a list."
            )
            return
        action = command.parse(tokens[1:])
        if not action.valid:
            self.write(action.error or command.help_text)
            return
        assert action.call is not None
        await self._execute_action(action.call)
