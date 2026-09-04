# Repository guidelines

- Treat `src/AppearanceMenuMod` as the canonical location for editable Lua code, localization, themes, and templates.
- Keep opaque runtime files under `assets`; do not modify `assets/runtime/AppearanceMenuMod/db.sqlite3` directly.
- Keep optional add-ons in installable game-directory layouts under `optional-assets`.
- Never commit generated content from `build` or `dist`.
- Preserve Lua 5.4 compatibility. Run `python scripts/check.py` after source changes; when `luac` is installed, this validates every Lua file.
- Run `python scripts/build.py --version <version>` after packaging changes and inspect the generated archives.
- Preserve the package root layout expected by Cyberpunk 2077 (`bin/x64/...` and `archive/pc/mod/...`).
- Use descriptive commit messages and document any required binary database or archive changes instead of editing opaque assets without their source projects.
