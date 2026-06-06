import orjson

from .base import BaseMethod, _snake
from .delete_file import DeleteFile
from .edit_file import EditFile
from .list_directory import ListDirectory
from .read_file import ReadFile
from .run_command import RunCommand
from .write_file import WriteFile

ALL_METHODS: list[type[BaseMethod]] = [
    WriteFile,
    ReadFile,
    EditFile,
    DeleteFile,
    ListDirectory,
    RunCommand,
]

ALL_TOOLS: list[dict] = [m.as_tool() for m in ALL_METHODS]

_METHOD_MAP: dict[str, type[BaseMethod]] = {
    _snake(m.__name__): m for m in ALL_METHODS
}


def dispatch(name: str, arguments: str | dict) -> str:
    """Parse arguments and execute the named method."""
    cls = _METHOD_MAP.get(name)
    if cls is None:
        return f"Unknown method: {name}"
    if isinstance(arguments, str):
        arguments = orjson.loads(arguments)
    return cls.model_validate(arguments).call()


__all__ = [
    "BaseMethod",
    "WriteFile",
    "ReadFile",
    "EditFile",
    "DeleteFile",
    "ListDirectory",
    "RunCommand",
    "ALL_METHODS",
    "ALL_TOOLS",
    "dispatch",
]
