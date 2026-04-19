# used by: utils\snv\net.py
from __future__ import annotations

import math
import re
from dataclasses import dataclass

from utils.snv.net import Net
from utils.snv.svg import SVG

"""
TODO:

 - Target layout -> nodes with smaller IDs 
   towards top-left, larger towards bottom-right
 - Change routing algorithm. See https://blog.disy.net/sugiyama-method/, 
   https://en.wikipedia.org/wiki/Layered_graph_drawing
 - Alternatively: Graph Neural Networks via Steiner Trees. https://arxiv.org/abs/2108.08368
   Explicitly used for VLSI (lol)
   
"""

GROUND = "0"


@dataclass
class _Pos:
    col: int
    row: int
    vertical: bool = False
    flipped: bool = False


def render(net: Net, cell: int = 100, color: str = "black") -> str:

    devices = list(net._DEVICE_MAP.values())
    if not devices:
        return '<svg xmlns="http://www.w3.org/2000/svg"/>'

    n2d = _node_to_devices(net)
    adj = _adjacency(n2d)
    grid = _place(devices, adj)
    _set_orientation(devices, grid, n2d)
    _set_flip(devices, grid, n2d)

    max_col = max(p.col for p in grid.values())
    max_row = max(p.row for p in grid.values())
    pad = cell // 2
    w = (max_col + 1) * cell + 2 * pad
    h = (max_row + 1) * cell + 2 * pad

    parts: list[str] = []

    for dev in devices:
        p = grid[dev.ID]
        raw = SVG.get(dev.component.name)
        if raw is None:
            continue
        inner = re.sub(r"^<svg[^>]*>", "", raw).replace("</svg>", "")
        x = p.col * cell + pad
        y = p.row * cell + pad
        tf = _transform(p)
        g_attr = f' transform="{tf}"' if tf else ""
        parts.append(
            f'<svg x="{x}" y="{y}" width="{cell}" height="{cell}" '
            f'viewBox="0 0 100 100"><g{g_attr}>{inner}</g></svg>'
        )
        parts.append(
            f'<text x="{x + cell // 2}" y="{y - 4}" '
            f'text-anchor="middle" font-size="11" fill="currentColor">'
            f"{dev.ID}</text>"
        )

    for node_name, devs in n2d.items():
        if node_name == GROUND or len(devs) < 2:
            continue
        ports = [_port_xy(d, node_name, grid[d.ID], cell, pad) for d in devs]
        for (x1, y1), (x2, y2) in _route(ports):
            parts.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
            )
        if len(ports) > 2:
            for px, py in ports:
                parts.append(f'<circle cx="{px}" cy="{py}" r="3" fill="currentColor"/>')

    for dev in devices:
        p = grid[dev.ID]
        for i, node in enumerate(dev.nodes):
            if node.name != GROUND:
                continue
            px, py = _port_xy(dev, GROUND, p, cell, pad)
            ddx, ddy = _port_dir(i, p)
            parts.append(_ground_at(px, py, ddx, ddy))

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'style="color:{color}">' + "".join(parts) + "</svg>"
    )


def _node_to_devices(net: Net) -> dict[str, list]:
    out: dict[str, list] = {}
    for dev in net._DEVICE_MAP.values():
        for node in dev.nodes:
            out.setdefault(node.name, []).append(dev)
    return out


def _adjacency(n2d: dict[str, list]) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {}
    for devs in n2d.values():
        for d in devs:
            adj.setdefault(d.ID, set())
    for name, devs in n2d.items():
        if name == GROUND:
            continue
        for i, d1 in enumerate(devs):
            for d2 in devs[i + 1 :]:
                adj[d1.ID].add(d2.ID)
                adj[d2.ID].add(d1.ID)
    return adj


def _place(devices: list, adj: dict[str, set[str]]) -> dict[str, _Pos]:
    n = len(devices)
    if n == 1:
        return {devices[0].ID: _Pos(0, 0)}

    pos: dict[str, list[float]] = {}
    for i, d in enumerate(devices):
        a = 2 * math.pi * i / n
        r = max(1.0, n * 0.3)
        pos[d.ID] = [math.cos(a) * r, math.sin(a) * r]

    k_rep, k_att, dt = 1.0, 1.0, 0.15
    for _ in range(300):
        fx: dict[str, float] = {d.ID: 0.0 for d in devices}
        fy: dict[str, float] = {d.ID: 0.0 for d in devices}

        # repulsion (all pairs)
        for i in range(n):
            for j in range(i + 1, n):
                id1, id2 = devices[i].ID, devices[j].ID
                dx = pos[id1][0] - pos[id2][0]
                dy = pos[id1][1] - pos[id2][1]
                dist = math.hypot(dx, dy) + 0.01
                f = k_rep / (dist * dist)
                ux, uy = dx / dist, dy / dist
                fx[id1] += f * ux
                fy[id1] += f * uy
                fx[id2] -= f * ux
                fy[id2] -= f * uy

        for d in devices:
            for nb in adj.get(d.ID, ()):
                dx = pos[nb][0] - pos[d.ID][0]
                dy = pos[nb][1] - pos[d.ID][1]
                dist = math.hypot(dx, dy) + 0.01
                f = k_att * dist
                ux, uy = dx / dist, dy / dist
                fx[d.ID] += f * ux
                fy[d.ID] += f * uy

        for d in devices:
            pos[d.ID][0] += fx[d.ID] * dt
            pos[d.ID][1] += fy[d.ID] * dt

        dt *= 0.985

    grid: dict[str, _Pos] = {}
    taken: set[tuple[int, int]] = set()
    ordered = sorted(devices, key=lambda d: (round(pos[d.ID][1]), round(pos[d.ID][0])))
    for d in ordered:
        c, r = round(pos[d.ID][0]), round(pos[d.ID][1])
        if (c, r) in taken:
            c, r = _nearest_free(c, r, taken)
        taken.add((c, r))
        grid[d.ID] = _Pos(c, r)

    mc = min(p.col for p in grid.values())
    mr = min(p.row for p in grid.values())
    for p in grid.values():
        p.col -= mc
        p.row -= mr

    return grid


def _nearest_free(c: int, r: int, taken: set[tuple[int, int]]) -> tuple[int, int]:
    for radius in range(1, 50):
        for dc in range(-radius, radius + 1):
            for dr in range(-radius, radius + 1):
                if max(abs(dc), abs(dr)) == radius and (c + dc, r + dr) not in taken:
                    return c + dc, r + dr
    return c, r


def _set_orientation(devices, grid, n2d):
    for dev in devices:
        p = grid[dev.ID]
        nn = [n.name for n in dev.nodes if n.name != GROUND]
        if not nn:
            continue

        def _centroid(node_name):
            pts = [
                (grid[o.ID].col, grid[o.ID].row)
                for o in n2d.get(node_name, [])
                if o.ID != dev.ID
            ]
            if not pts:
                return p.col, p.row
            return (
                sum(x for x, _ in pts) / len(pts),
                sum(y for _, y in pts) / len(pts),
            )

        if len(nn) >= 2:
            c0 = _centroid(nn[0])
            c1 = _centroid(nn[1])
            p.vertical = abs(c1[1] - c0[1]) > abs(c1[0] - c0[0])
        else:
            c = _centroid(nn[0])
            p.vertical = abs(c[1] - p.row) > abs(c[0] - p.col)


def _set_flip(devices, grid, n2d):
    for dev in devices:
        p = grid[dev.ID]
        cn = _flip_cost(dev, p, False, grid, n2d)
        cf = _flip_cost(dev, p, True, grid, n2d)
        p.flipped = cf < cn


def _flip_cost(dev, pos, flipped, grid, n2d):
    total = 0.0
    for i, node in enumerate(dev.nodes):
        if node.name == GROUND:
            continue
        px, py = _approx_port(i, pos, flipped)
        for other in n2d.get(node.name, []):
            if other.ID == dev.ID:
                continue
            op = grid[other.ID]
            total += abs(px - op.col - 0.5) + abs(py - op.row - 0.5)
    return total


def _approx_port(idx, pos, flipped):
    if not pos.vertical:
        if (idx == 0) != flipped:
            return pos.col, pos.row + 0.5
        return pos.col + 1, pos.row + 0.5
    if (idx == 0) != flipped:
        return pos.col + 0.5, pos.row
    return pos.col + 0.5, pos.row + 1


def _transform(p: _Pos) -> str:
    if p.vertical and p.flipped:
        return "rotate(-90 50 50)"
    if p.vertical:
        return "rotate(90 50 50)"
    if p.flipped:
        return "scale(-1,1) translate(-100,0)"
    return ""


def _port_xy(dev, node_name: str, pos: _Pos, cell: int, pad: int):
    idx = next(i for i, n in enumerate(dev.nodes) if n.name == node_name)
    x = pos.col * cell + pad
    y = pos.row * cell + pad
    h = cell // 2

    if not pos.vertical:
        if (idx == 0) != pos.flipped:
            return x, y + h
        return x + cell, y + h
    if (idx == 0) != pos.flipped:
        return x + h, y
    return x + h, y + cell


def _port_dir(idx: int, pos: _Pos):
    if not pos.vertical:
        return (-1, 0) if (idx == 0) != pos.flipped else (1, 0)
    return (0, -1) if (idx == 0) != pos.flipped else (0, 1)


def _route(ports: list[tuple[float, float]]):
    if len(ports) < 2:
        return

    if len(ports) == 2:
        (x1, y1), (x2, y2) = ports
        if x1 == x2 or y1 == y2:
            yield (x1, y1), (x2, y2)
        else:
            yield (x1, y1), (x2, y1)
            yield (x2, y1), (x2, y2)
        return

    xs = [p[0] for p in ports]
    ys = [p[1] for p in ports]

    if (max(xs) - min(xs)) >= (max(ys) - min(ys)):
        ty = sorted(ys)[len(ys) // 2]
        yield (min(xs), ty), (max(xs), ty)
        for x, y in ports:
            if y != ty:
                yield (x, y), (x, ty)
    else:
        tx = sorted(xs)[len(xs) // 2]
        yield (tx, min(ys)), (tx, max(ys))
        for x, y in ports:
            if x != tx:
                yield (x, y), (tx, y)


def _ground_at(px, py, dx, dy) -> str:
    parts: list[str] = []

    if dy == 1:
        _gnd_down(parts, px, py)
    elif dy == -1:
        _gnd_up(parts, px, py)
    else:
        sx = px + dx * 12
        parts.append(f'<line x1="{px}" y1="{py}" x2="{sx}" y2="{py}"/>')
        parts.append(f'<line x1="{sx}" y1="{py}" x2="{sx}" y2="{py + 25}"/>')
        _gnd_down(parts, sx, py + 25)

    return (
        '<g fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round">' + "".join(parts) + "</g>"
    )


def _gnd_down(parts: list[str], x, y):
    parts.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + 8}"/>')
    for i, hw in enumerate((10, 6, 2)):
        ly = y + 8 + i * 5
        parts.append(f'<line x1="{x - hw}" y1="{ly}" x2="{x + hw}" y2="{ly}"/>')


def _gnd_up(parts: list[str], x, y):
    parts.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y - 8}"/>')
    for i, hw in enumerate((10, 6, 2)):
        ly = y - 8 - i * 5
        parts.append(f'<line x1="{x - hw}" y1="{ly}" x2="{x + hw}" y2="{ly}"/>')
