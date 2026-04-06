# used by:
import sys
import ast
from pathlib import Path

from tools.gen_init import main as gen_init_main

VENV_NAMES = {"venv", "env", ".venv", ".env"}

# spaghetti code


def build_reexport_map(py_files, base_dir, module_map):
    reexport_map = {}
    for f in py_files:
        if f.name != "__init__.py":
            continue
        pkg_name = f.parent.name
        if pkg_name not in module_map:
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level > 0 and node.module:
                sub = node.module.split(".")[-1]
                if sub in module_map:
                    for alias in node.names:
                        reexport_map[(pkg_name, alias.name)] = sub
    return reexport_map


def find_local_imports(file_path, module_map, reexport_map):
    imports = set()
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                for part in reversed(parts):
                    if part in module_map:
                        imports.add(part)
                        break

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                parts = node.module.split(".")
            else:
                parts = []

            if node.level > 0:
                for alias in node.names:
                    if alias.name in module_map:
                        imports.add(alias.name)
                for part in reversed(parts):
                    if part in module_map:
                        imports.add(part)
                        break
            else:
                if not parts:
                    continue

                if len(parts) > 1:
                    for part in reversed(parts):
                        if part in module_map:
                            imports.add(part)
                            break
                else:
                    pkg = parts[0]
                    if pkg not in module_map:
                        continue
                    is_package = any(
                        Path(p).name == "__init__.py" for p in module_map[pkg]
                    )
                    if not is_package:
                        imports.add(pkg)
                        continue
                    resolved_any = False
                    for alias in node.names:
                        if alias.name in module_map:
                            imports.add(alias.name)
                            resolved_any = True
                        elif (pkg, alias.name) in reexport_map:
                            imports.add(reexport_map[(pkg, alias.name)])
                            resolved_any = True
                    if not resolved_any:
                        imports.add(pkg)

    return imports


def detect_line_ending(text):
    if "\r\n" in text:
        return "\r\n"
    if "\r" in text:
        return "\r"
    return "\n"


def build_module_map(py_files, base_dir):
    module_map = {}

    for f in py_files:
        if f.name == "__init__.py":
            mod_name = f.parent.name
        elif f.name.startswith("__"):
            continue
        else:
            mod_name = f.stem

        rel = str(f.relative_to(base_dir))
        module_map.setdefault(mod_name, []).append(rel)

    return module_map


def update_used_by_comments(base_dir):
    base_dir = base_dir.resolve()
    py_files = sorted(
        f
        for f in base_dir.rglob("*.py")
        if not any(part in VENV_NAMES for part in f.parts)
    )

    module_map = build_module_map(py_files, base_dir)
    reexport_map = build_reexport_map(py_files, base_dir, module_map)

    all_rels = {rel for paths in module_map.values() for rel in paths}
    usages = {rel: [] for rel in all_rels}

    for f in py_files:
        if f.name.startswith("__"):
            continue
        importer = str(f.relative_to(base_dir))
        for mod in find_local_imports(f, module_map, reexport_map):
            for target_rel in module_map[mod]:
                if target_rel != importer:
                    usages[target_rel].append(importer)

    for f in py_files:
        if f.name.startswith("__"):
            continue

        rel = str(f.relative_to(base_dir))
        users = sorted(usages.get(rel, []))
        comment_line = f"# used by: {', '.join(users)}" if users else "# used by:"

        original = f.read_text(encoding="utf-8")
        line_ending = detect_line_ending(original)

        has_trailing_newline = original.endswith(("\n", "\r"))

        lines = original.splitlines()
        has_shebang = bool(lines) and lines[0].startswith("#!")
        insert_at = 1 if has_shebang else 0

        if len(lines) > insert_at and lines[insert_at].startswith("# used by:"):
            lines[insert_at] = comment_line
        else:
            lines.insert(insert_at, comment_line)

        new_text = line_ending.join(lines)
        if has_trailing_newline:
            new_text += line_ending
        f.write_text(new_text, encoding="utf-8")


def main():
    if len(sys.argv) > 2:
        print("Usage: python gen_usages.py")
        print("       python gen_usages.py <directory>")
        sys.exit(1)

    base_dir = Path.cwd()
    if len(sys.argv) == 2:
        base_dir = Path(sys.argv[1])
        if not base_dir.is_dir():
            print(f"Error: {base_dir} is not a directory")
            sys.exit(1)

    for init in sorted(base_dir.rglob("__init__.py")):
        pkg_dir = init.parent
        if not any(part in VENV_NAMES for part in pkg_dir.parts):
            gen_init_main(pkg_dir)

    update_used_by_comments(base_dir)
    print(f"Updated usage comments recursively in {base_dir}")


if __name__ == "__main__":
    main()
