from dataclasses import dataclass
from enum import Enum, auto, unique

from pynitrokey.nk3.secrets_app import (
    CCIDInstruction,
    SecretsApp,
    SelectResponse,
)


class pin_check:
    def check(self) -> SelectResponse:
        check = SecretsApp.select()
        return check


# @classmethod
# def check(cls, CCID: CCIDInstruction) -> SelectResponse:
#     SecretsApp.select(cls, CCID)

# @dataclass
# class Pin:
#    id: bytes
#    pintype: Optional[item.data(1, 0)]
#    name: str
#    desc: str

# cls, secrets: SelectResponse
