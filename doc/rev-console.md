# rev-console Design

## Overview

`rev-console` is an interactive full-screen TUI for REV Robotics Expansion Hubs
built on [Textual](https://textual.textualize.io/). A single `RevConsoleApp`
instance owns the hub connection for the entire session; the Textual event loop
keeps the hub keep-alive task running across all commands.

## Package relationship

```
rev-console
    └── rev-hub-cli          (command modules + _get_expansion_hub)
            ├── rev-expansion-hub
            │       ├── rev-core
            │       └── rev-rhsplib
            └── rev-distance-sensor
```

`rev-console` imports `rev_hub_cli.command.*` modules directly to reuse hub
logic without duplication. `_get_expansion_hub` is imported from
`rev_hub_cli.__main__` to share hub-selection (serial / parent / child flags,
auto-detection, error messages).

## Module structure

| Module | Responsibility |
|---|---|
| `__main__.py` | Click CLI entry points (`list`, `connect`) |
| `app.py` | `RevConsoleApp` — Textual app, input handling, command dispatch |
| `commands.py` | Command objects, `CommandAction`, registry factories |
| `widgets.py` | `WatchWidget`, `WatchPanel`, `_CloseButton`, CSS |
| `history.py` | Command history persistence (`~/.rev_console_history`) |
| `log_writer.py` | `LogWriter` — redirects stdout to the Textual `RichLog` widget |

## Command object pattern

Every top-level command is a `Command` subclass defined in `commands.py`:

```python
class Command(ABC):
    help_text: str = ""

    @abstractmethod
    def parse(self, rest: list[str]) -> CommandAction: ...
```

`parse()` receives the token list after the command name, validates arguments,
and returns a `CommandAction`:

```python
@dataclass(frozen=True)
class CommandAction:
    valid: bool
    watchable: bool
    call: CommandCallable | None   # None only when valid=False
    error: str = ""
```

- `valid=False, error=""` — dispatcher shows `command.help_text`
- `valid=False, error=<msg>` — dispatcher shows the specific error message
- `valid=True, watchable=True` — `call()` returns a `str`; can be pinned to the watch panel
- `valid=True, watchable=False` — `call()` runs to completion (action or continuous loop)

`CommandCallable = Callable[[], Awaitable[str]]`

### Factory helpers

| Helper | Returns |
|---|---|
| `_create_valid_action(call)` | `CommandAction(valid=True, watchable=False, call=call)` |
| `_create_error_action(error)` | `CommandAction(valid=False, watchable=False, call=None, error=error)` |
| `_create_read_action(read, continuous)` | watchable action, or infinite-loop action when `continuous=True` |

### Flag parsing

| Helper | Purpose |
|---|---|
| `_parse_flag(rest, flag)` | Strip a specific flag, return `(found, remaining)` |
| `_parse_continuous_flag(rest)` | Shorthand for `_parse_flag(rest, "--continuous")` |

### Base classes

`_NoArgRead` provides a `parse()` implementation for zero-argument readable
commands. Subclasses only implement `async _read(self) -> str`.

Commands with arguments implement `parse()` directly, typically with a `match`
on the remaining token list.

## Command registry

`RevConsoleApp._build_registry()` constructs a `dict[str, Command]` mapping
command names to instances. The registry is built once at app startup and stored
as `self._registry`.

`WatchCommand` and `HelpCommand` receive the registry dict directly — since
Python dicts are mutable and passed by reference, entries added after
construction (including `watch` and `help` themselves) are visible through the
same object.

## Dispatch

`RevConsoleApp._dispatch(tokens)`:

1. Look up `tokens[0]` in `self._registry`.
2. Call `command.parse(tokens[1:])` to get a `CommandAction`.
3. If `not action.valid`: display `action.error` or `command.help_text`.
4. Otherwise: `await self._execute_action(action.call)`.

`_execute_action` wraps `call()` in an `asyncio.Task` stored as
`self._continuous_task`. This makes every command — one-shot or continuous —
cancellable via **Ctrl+C** (`action_cancel_command` calls `task.cancel()`).
If the task returns a non-empty string it is printed to the output log.

## Ctrl+C handling

Textual maps **Ctrl+C** to the `cancel_command` action binding. If a task is
running, `task.cancel()` is called; the `CancelledError` is caught in
`_execute_action` and `(stopped)` is printed. If no task is running, `^C` is
echoed to the log. The hub connection is never interrupted.

## Watch panel

`watch add [--rate <hz>] <command...>` parses the remainder as a sub-command,
calls `command.parse()`, and checks that the resulting `CommandAction` is both
`valid` and `watchable`. If so, a `WatchWidget` is mounted in the
`WatchPanel` with the extracted `call` as its polling function.

`WatchWidget` uses `set_interval(1.0 / rate, self._poll)` to call the reader
and update a `reactive[str]` value. The panel hides itself when no watches
remain.

## Continuous vs. one-shot commands

`_create_read_action(read, continuous)`:

- `continuous=False` → returns a watchable `CommandAction` whose `call` is `read` directly.
- `continuous=True` → wraps `read` in an infinite `async def _loop()` that
  `print()`s each result. The loop is cancellable via **Ctrl+C**.

## Motor position

`motor position` uses `rev_hub_cli.command.motor.run_motor_to_position`, which
sets REGULATED_POSITION mode, starts the motor, and polls
`hub.get_motor_at_target()` (each poll yields to the event loop via serial I/O)
until the encoder reaches the target. Unlike other fire-and-return motor
commands, `motor position` awaits completion before returning to the prompt.

## Distance sensor

`DistanceCommand.parse()` constructs a `DistanceSensor(hub, ch)` and performs
lazy `await sensor.setup()` on first poll. `rev_distance_sensor` is an optional
dependency imported inside `parse()` to avoid a hard import failure when the
package is not installed.

## stdout redirection

On mount, `sys.stdout` is replaced with a `LogWriter` instance that buffers
text and flushes complete lines to the `RichLog` widget. This allows all
`print()` calls inside command coroutines to appear in the output log without
any changes to the `rev_hub_cli` command functions. The original `sys.stdout`
is restored on unmount.

## Command history

`load_history()` / `save_history()` in `history.py` read and write
`~/.rev_console_history` (capped at 500 entries). History is loaded on mount
and saved on unmount. Up/Down arrow navigation is handled in `on_key`.
