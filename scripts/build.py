#!/usr/bin/env python3
"""Build installable, reproducible Appearance Menu Mod packages."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import shutil
import stat
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "AppearanceMenuMod"
RUNTIME_ASSETS = ROOT / "assets" / "runtime" / "AppearanceMenuMod"
GAME_ASSETS = ROOT / "assets" / "game"
OPTIONAL_ASSETS = ROOT / "optional-assets"
MOD_DESTINATION = Path("bin/x64/plugins/cyber_engine_tweaks/mods/AppearanceMenuMod")
ZIP_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def copy_tree(source: Path, destination: Path) -> None:
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def write_zip(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in source.rglob("*") if item.is_file()):
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def normalized_version(value: str) -> str:
    version = value.removeprefix("v")
    if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z._+-]*", version):
        raise ValueError(f"invalid package version: {value!r}")
    return version


def calendar_version() -> str:
    now = dt.datetime.now(dt.timezone.utc)
    month_start = now.strftime("%Y-%m-01T00:00:00Z")
    result = subprocess.run(
        ["git", "rev-list", "--count", f"--since={month_start}", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    patch = result.stdout.strip() if result.returncode == 0 else "1"
    return f"{now.year}.{now.month}.{max(1, int(patch or '1'))}"


def package_name(name: str, version: str, development: bool) -> str:
    suffix = f"_{calendar_version()}" if development else ""
    return f"{name}_v{version}_windows_x64{suffix}.zip"


def build(version: str, build_dir: Path, dist_dir: Path, development: bool = False) -> list[Path]:
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    build_dir.mkdir(parents=True)
    dist_dir.mkdir(parents=True)

    main_stage = build_dir / "main"
    copy_tree(SOURCE, main_stage / MOD_DESTINATION)
    copy_tree(RUNTIME_ASSETS, main_stage / MOD_DESTINATION)
    copy_tree(GAME_ASSETS, main_stage)

    packages: list[tuple[str, Path]] = [
        ("AppearanceMenuMod", main_stage),
        ("AMM_4KPanamBody", OPTIONAL_ASSETS / "AMM_4KPanamBody"),
        ("AMM_Judy_ClubOutfit", OPTIONAL_ASSETS / "AMM_Judy_ClubOutfit"),
    ]

    lod_stage = build_dir / "basegame-lod-fix" / "archive" / "pc" / "mod"
    lod_stage.mkdir(parents=True)
    shutil.copy2(OPTIONAL_ASSETS / "basegame_lod_fix.archive", lod_stage)
    packages.append(("AMM_BasegameLodFix", build_dir / "basegame-lod-fix"))

    outputs: list[Path] = []
    for name, source in packages:
        destination = dist_dir / package_name(name, version, development)
        write_zip(source, destination)
        outputs.append(destination)

    checksum_file = dist_dir / "SHA256SUMS"
    checksum_file.write_text(
        "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in outputs),
        encoding="utf-8",
        newline="\n",
    )
    outputs.append(checksum_file)
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Package version, with or without a leading v")
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--development", action="store_true", help="Append the calendar build version")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    version = normalized_version(args.version)
    for output in build(version, args.build_dir.resolve(), args.output_dir.resolve(), args.development):
        print(output.relative_to(ROOT) if output.is_relative_to(ROOT) else output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
