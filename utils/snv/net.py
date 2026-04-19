# used by: utils\snv\layout.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from pathlib import Path
from utils.snv.component import ComponentType

_SPICE_SUFFIXES = {
    "f": 1e-15,
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "m": 1e-3,
    "k": 1e3,
    "meg": 1e6,
    "g": 1e9,
    "t": 1e12,
}


class Net:

    def __init__(self):
        self._NETID = 0
        self._NODE_MAP = {}
        self._DEVICE_MAP = {}

    @dataclass
    class Node:
        ID: int
        name: str

    @dataclass
    class Device:
        ID: str
        component: ComponentType
        nodes: list[Net.Node]
        value: float | str | None = None
        model: str | None = None
        params: dict[str, Any] = field(default_factory=dict)

    def create_node(self, name: str) -> Node:
        node = Net.Node(ID=self._NETID, name=name)
        self._NETID += 1
        self._NODE_MAP[name] = node
        return node

    def get_node(self, name: str) -> Node:
        if name in self._NODE_MAP.keys():
            return self._NODE_MAP[name]
        return self.create_node(name)

    def _parse_one(self, line: str):
        tokens = line.split()
        if not tokens:
            return None

        device_id = tokens[0].upper()
        letter = device_id[0]

        component = ComponentType.from_string(letter)
        if component is None:
            return None

        node_tokens, rest = tokens[1:3], tokens[3:]
        nodes = [self.get_node(n) for n in node_tokens]

        value: float | str | None = None
        model: str | None = None
        params: dict[str, Any] = {}

        for token in rest:
            if "=" in token:
                key, _, raw = token.partition("=")
                params[key.upper()] = (
                    _parse_value(raw) if _parse_value(raw) is not None else raw
                )
            else:
                parsed = _parse_value(token)
                if parsed is not None:
                    value = parsed
                elif model is None:
                    model = token

        return Net.Device(
            ID=device_id,
            component=component,
            nodes=nodes,
            value=value,
            model=model,
            params=params,
        )

    @staticmethod
    def from_file(path: str | Path):
        net = Net()
        try:
            with Path(path).open() as file:
                for i, line in enumerate(file):
                    if i == 0:
                        continue
                    if not line:
                        continue
                    if line.startswith("*"):
                        continue
                    if line.lower().startswith(".end"):
                        break
                    if line.startswith("."):
                        continue

                    device = net._parse_one(line)
                    if device is not None:
                        net._DEVICE_MAP[device.ID] = device

        except OSError as e:
            raise RuntimeError(f"Could not open netlist '{path}'") from e

        return net

    def to_svg(self, cell: int = 100, color: str = "black") -> str:
        from utils.snv.layout import render

        return render(self, cell, color)


def _parse_value(token: str):
    token = token.strip().lower()
    for suffix, scale in sorted(_SPICE_SUFFIXES.items(), key=lambda x: -len(x[0])):
        if token.endswith(suffix):
            try:
                return float(token[: -len(suffix)]) * scale
            except ValueError:
                return None
    try:
        return float(token)
    except ValueError:
        return None
