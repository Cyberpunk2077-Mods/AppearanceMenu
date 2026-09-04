# Appearance Menu Mod

Appearance Menu Mod (AMM) is a Cyber Engine Tweaks mod for Cyberpunk 2077. This repository keeps editable source files and immutable runtime assets separate from generated installation packages.

## Repository layout

```text
src/AppearanceMenuMod/       Lua source, localization, themes, and templates
assets/runtime/              Runtime data copied beside the Lua source
assets/game/                 Files copied to the game directory root
optional-assets/             Optional add-ons, stored in installable layouts
scripts/build.py             Reproducible package builder
scripts/check.py             Source and asset validation
build/                       Generated staging files (ignored)
dist/                        Generated ZIP packages (ignored)
```

`src/` is the canonical location for editable AMM code. Do not edit generated files under `build/` or `dist/`.

The SQLite database and `.archive` files are retained as runtime assets because their editable upstream sources are not present in the original repository. They are copied unchanged during packaging.

## Requirements

- Python 3.9 or newer for validation and packaging
- Lua 5.4 or `luac` 5.4 for optional Lua syntax validation
- Cyber Engine Tweaks to run the mod in Cyberpunk 2077

## Validate

```bash
python scripts/check.py
```

The validator checks JSON syntax, required project files, SQLite integrity, and source-tree boundaries. If a Lua compiler is installed, it also compiles every Lua file without producing output.

## Build

```bash
python scripts/build.py --version 1.0.0
```

Generated packages are written to `dist/`:

```text
AppearanceMenuMod_v1.0.0_windows_x64.zip
AMM_4KPanamBody_v1.0.0_windows_x64.zip
AMM_Judy_ClubOutfit_v1.0.0_windows_x64.zip
AMM_BasegameLodFix_v1.0.0_windows_x64.zip
SHA256SUMS
```

Development builds add a calendar suffix after the architecture, for example `AppearanceMenuMod_v1.0.0_windows_x64_2026.9.3.zip`.

The main archive expands directly into the Cyberpunk 2077 game directory and recreates the original `bin/` and `archive/` layout.

## Development workflow

1. Change Lua, localization, theme, or template files under `src/AppearanceMenuMod/`.
2. Keep opaque runtime assets under `assets/` and optional add-ons under `optional-assets/`.
3. Run `python scripts/check.py`.
4. Run `python scripts/build.py --version <version>` and inspect the ZIP files under `dist/`.
5. Test the generated package in the game before publishing.

Pushing a branch or opening a pull request runs validation and packaging in GitHub Actions. Pushing a tag builds the same packages and creates a draft GitHub Release for manual approval.

## License

This repository mirrors Appearance Menu Mod. Refer to the original mod page and upstream project for licensing and redistribution terms.
