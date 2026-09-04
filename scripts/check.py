#!/usr/bin/env python3
"""Validate the Appearance Menu Mod source and runtime assets."""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
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

    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.lua")):
        if any(part in {"build", "dist"} for part in path.parts):
            continue
        result = subprocess.run([compiler, "-p", str(path)], capture_output=True, text=True, check=False)
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
