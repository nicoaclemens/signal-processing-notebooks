# used by: utils\snv\net.py
from enum import Enum


class ComponentType(Enum):
    R = "R"
    C = "C"
    L = "L"
    D = "D"
    VC = "V"
    CC = "I"

    @classmethod
    def from_string(cls, name: str) -> "ComponentType | None":
        return cls._value2member_map_.get(name)
