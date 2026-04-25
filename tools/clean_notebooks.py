# used by:
import json
import sys
import hashlib
import subprocess
from pathlib import Path

VENV_NAMES = {"venv", "env", ".venv", ".env"}

CANONICAL_KERNELSPEC = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}

NOTEBOOK_META_STRIP = {"language_info"}

CELL_META_KEEP: set[str] = set()


def is_empty_cell(cell: dict) -> bool:
    source = cell.get("source", "")
    if isinstance(source, list):
        source = "".join(source)
    return not source.strip()


def _source_text(cell: dict) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return str(source)


def _cell_fingerprint(cell: dict) -> str:
    payload = f"{cell.get('cell_type', 'unknown')}\n{_source_text(cell)}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _load_previous_ids_from_git(path: Path, base_dir: Path) -> dict[str, list[str]]:
    try:
        rel = path.resolve().relative_to(base_dir.resolve()).as_posix()
    except ValueError:
        return {}

    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{rel}"],
            cwd=str(base_dir),
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
        )
    except (FileNotFoundError, OSError):
        return {}

    if result.returncode != 0 or not result.stdout.strip():
        return {}

    try:
        old_nb = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}

    id_map: dict[str, list[str]] = {}
    for cell in old_nb.get("cells", []):
        old_id = cell.get("id")
        if not isinstance(old_id, str) or not old_id:
            continue
        fp = _cell_fingerprint(cell)
        id_map.setdefault(fp, []).append(old_id)

    return id_map


def _take_previous_id(
    cell: dict,
    previous_ids_by_fp: dict[str, list[str]],
    used_ids: set[str],
) -> str | None:
    fp = _cell_fingerprint(cell)
    candidates = previous_ids_by_fp.get(fp)
    if not candidates:
        return None

    current_id = cell.get("id")
    if isinstance(current_id, str) and current_id and current_id not in used_ids:
        try:
            idx = candidates.index(current_id)
        except ValueError:
            idx = -1
        if idx >= 0:
            candidates.pop(idx)
            used_ids.add(current_id)
            return current_id

    while candidates:
        previous_id = candidates.pop(0)
        if previous_id not in used_ids:
            used_ids.add(previous_id)
            return previous_id

    return None


def _take_current_id(cell: dict) -> str | None:
    current_id = cell.get("id")
    if not isinstance(current_id, str) or not current_id:
        return None
    return current_id


def clean_cell(cell: dict, cell_id: str) -> dict:
    cell_type = cell.get("cell_type")

    cleaned: dict = {
        "cell_type": cell_type,
        "id": cell_id,
        "metadata": {},
        "source": cell["source"],
    }

    if cell_type == "code":
        cleaned["execution_count"] = None
        cleaned["outputs"] = []

    return cleaned


def clean_notebook(path: Path, base_dir: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    nb = json.loads(raw)

    original_cell_count = len(nb["cells"])

    meta = nb.get("metadata", {})
    for key in NOTEBOOK_META_STRIP:
        meta.pop(key, None)

    if "kernelspec" in meta:
        meta["kernelspec"] = CANONICAL_KERNELSPEC
    else:
        meta["kernelspec"] = CANONICAL_KERNELSPEC

    nb["metadata"] = meta

    cleaned_cells = []
    removed_empty = 0
    cleared_outputs = 0
    used_ids = set()
    previous_ids_by_fp = _load_previous_ids_from_git(path, base_dir)

    for cell in nb["cells"]:
        if is_empty_cell(cell):
            removed_empty += 1
            continue

        had_output = (
            bool(cell.get("outputs")) or cell.get("execution_count") is not None
        )
        cell_id = _take_previous_id(cell, previous_ids_by_fp, used_ids)
        if cell_id is None:
            cell_id = _take_current_id(cell)
        if cell_id is None:
            raise ValueError(f"Cell without id in {path}")
        cleaned_cells.append(clean_cell(cell, cell_id))
        if had_output and cell.get("cell_type") == "code":
            cleared_outputs += 1

    nb["cells"] = cleaned_cells

    cleaned_json = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"

    if cleaned_json != raw:
        path.write_text(cleaned_json, encoding="utf-8")

    return {
        "path": path,
        "cells_before": original_cell_count,
        "cells_after": len(cleaned_cells),
        "removed_empty": removed_empty,
        "cleared_outputs": cleared_outputs,
        "changed": cleaned_json != raw,
    }


def find_notebooks(base_dir: Path) -> list[Path]:
    return sorted(
        f
        for f in base_dir.rglob("*.ipynb")
        if not any(part in VENV_NAMES for part in f.parts)
        and ".ipynb_checkpoints" not in f.parts
    )


def main():
    if len(sys.argv) > 2:
        print("Usage: python -m tools.clean_notebooks")
        print("       python -m tools.clean_notebooks <directory>")
        sys.exit(1)

    base_dir = Path.cwd()
    if len(sys.argv) == 2:
        base_dir = Path(sys.argv[1])
        if not base_dir.is_dir():
            print(f"Error: {base_dir} is not a directory")
            sys.exit(1)

    notebooks = find_notebooks(base_dir)

    if not notebooks:
        print("No notebooks found.")
        return

    total_changed = 0
    total_removed_empty = 0
    total_cleared_outputs = 0

    for nb_path in notebooks:
        result = clean_notebook(nb_path, base_dir)
        rel = nb_path.relative_to(base_dir)

        parts = []
        if result["removed_empty"]:
            parts.append(f"{result['removed_empty']} empty cell(s) removed")
        if result["cleared_outputs"]:
            parts.append(f"{result['cleared_outputs']} output(s) cleared")
        if result["changed"] and not parts:
            parts.append("metadata cleaned")

        if result["changed"]:
            total_changed += 1
            total_removed_empty += result["removed_empty"]
            total_cleared_outputs += result["cleared_outputs"]
            print(f"  cleaned  {rel}  ({', '.join(parts)})")
        else:
            print(f"  ok       {rel}")

    print()
    print(
        f"{total_changed}/{len(notebooks)} notebook(s) modified; {total_removed_empty} empty cell(s) removed, {total_cleared_outputs} output cleared."
    )


if __name__ == "__main__":
    main()
