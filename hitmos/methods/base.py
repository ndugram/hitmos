import re
from abc import abstractmethod

from pydantic import BaseModel


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


class BaseMethod(BaseModel):
    @abstractmethod
    def call(self) -> str: ...

    @classmethod
    def as_tool(cls) -> dict:
        schema = cls.model_json_schema()
        params = {
            "type": "object",
            "properties": {
                k: {kk: vv for kk, vv in v.items() if kk != "title"}
                for k, v in schema.get("properties", {}).items()
            },
            "required": schema.get("required", []),
        }
        return {
            "type": "function",
            "function": {
                "name": _snake(cls.__name__),
                "description": (cls.__doc__ or "").strip(),
                "parameters": params,
            },
        }
