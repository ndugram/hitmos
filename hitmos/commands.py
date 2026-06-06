from dataclasses import dataclass
from enum import Enum


class CommandType(Enum):
    HELP = "help"
    CLEAR = "clear"
    RESET = "reset"
    MODEL = "model"
    EXIT = "exit"


@dataclass
class CommandResult:
    type: CommandType
    arg: str | None = None


class CommandHandler:
    _MAP: dict[str, CommandType] = {
        "/help": CommandType.HELP,
        "/clear": CommandType.CLEAR,
        "/reset": CommandType.RESET,
        "/model": CommandType.MODEL,
        "/exit": CommandType.EXIT,
        "/quit": CommandType.EXIT,
    }

    def parse(self, text: str) -> CommandResult | None:
        if not text.startswith("/"):
            return None
        parts = text.split(maxsplit=1)
        cmd_type = self._MAP.get(parts[0].lower())
        if cmd_type is None:
            return None
        arg = parts[1] if len(parts) > 1 else None
        return CommandResult(type=cmd_type, arg=arg)
