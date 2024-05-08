from dataclasses import dataclass

@dataclass
class Pin:
    id: bytes
    pintype: Optional[item.data(1, 0)]
    name: str
    desc: str