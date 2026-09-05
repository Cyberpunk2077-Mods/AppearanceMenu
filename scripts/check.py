#!/usr/bin/env python3
"""Validate the Appearance Menu Mod source and runtime assets."""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "AppearanceMenuMod"
DATABASE = ROOT / "assets" / "runtime" / "AppearanceMenuMod" / "db.sqlite3"
REQUIRED = (
    SOURCE / "init.lua",
    SOURCE / "Modules",
    SOURCE / "Localization" / "en_US.lua",
    ROOT / "assets" / "game" / "archive" / "pc" / "mod" / "AMM_PlayerBodyTag.xl",
    DATABASE,
)
FORBIDDEN_SOURCE_SUFFIXES = {".archive", ".rar", ".sqlite3", ".zip"}


def validate_required_files() -> list[str]:
    return [f"missing required path: {path.relative_to(ROOT)}" for path in REQUIRED if not path.exists()]


def validate_source_boundaries() -> list[str]:
    return [
        f"generated or binary asset found in src/: {path.relative_to(ROOT)}"
        for path in SOURCE.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SOURCE_SUFFIXES
    ]


def validate_json() -> list[str]:
    errors: list[str] = []
    for path in sorted(SOURCE.rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            errors.append(f"invalid JSON {path.relative_to(ROOT)}: {error}")
    return errors


def validate_database() -> list[str]:
    try:
        uri = f"file:{DATABASE.as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()
        if result != ("ok",):
            return [f"SQLite integrity check failed: {result!r}"]
    except sqlite3.Error as error:
        return [f"cannot validate {DATABASE.relative_to(ROOT)}: {error}"]
    return []


def validate_lua() -> list[str]:
    compiler = next((path for name in ("luac5.4", "luac54", "luac") if (path := shutil.which(name))), None)
    if compiler is None:
        print("warning: Lua compiler not found; skipped Lua syntax validation", file=sys.stderr)
        return []

    # CET accepts C-style integer suffixes (1ULL, 0xFU); stock luac5.4 does not.
    # Normalize only for syntax checking — source files are left unchanged.
    uint64_max_re = re.compile(r"\b18446744073709551615U?LL\b")
    suffix_re = re.compile(r"(?<=\d)(?:U?LL|U)\b")

    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.lua")):
        if any(part in {"build", "dist"} for part in path.parts):
            continue
        try:
            source = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            errors.append(f"invalid Lua {path.relative_to(ROOT)}: {error}")
            continue

        normalized = uint64_max_re.sub("-1", source)
        normalized = suffix_re.sub("", normalized)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".lua", delete=False) as handle:
            handle.write(normalized)
            temp_path = Path(handle.name)

        try:
            result = subprocess.run(
                [compiler, "-p", str(temp_path)],
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            temp_path.unlink(missing_ok=True)

        if result.returncode:
            errors.append(f"invalid Lua {path.relative_to(ROOT)}: {result.stderr.strip()}")
    return errors


def main() -> int:
    errors = (
        validate_required_files()
        + validate_source_boundaries()
        + validate_json()
        + validate_database()
        + validate_lua()
    )
    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
