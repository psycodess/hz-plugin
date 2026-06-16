# CHANGELOG

All notable changes to this project are documented in this file.
This project follows [Semantic Versioning](https://semver.org/).

---

## [v0.2.0] – 2026-06-16 – Multi-Monitor & Quality Overhaul

### Added
- **Multi-monitor support** — users can now control any monitor independently:
  - `hz` or `hz1` → primary monitor (same as before)
  - `hz2` → second monitor
  - `hz3` → third monitor (and so on)
- **Structured logging** — all operations are logged to `hz-plugin.log` in the plugin folder for easier debugging.
- **Full ChangeDisplaySettings error handling** — all 8 known Windows API return codes are mapped to human-readable messages:
  - `DISP_CHANGE_SUCCESSFUL`, `DISP_CHANGE_RESTART`, `DISP_CHANGE_FAILED`, `DISP_CHANGE_BADMODE`, `DISP_CHANGE_NOTUPDATED`, `DISP_CHANGE_BADFLAGS`, `DISP_CHANGE_BADPARAM`, `DISP_CHANGE_BADDUALVIEW`
- **Input validation** — non-numeric query input now shows a friendly error instead of crashing.
- **Type hints** on all functions for better code clarity and IDE support.
- **Test suite** (`tests/test_main.py`) with 19 unit tests using `pytest` and `unittest.mock`:
  - keyword parsing, monitor enumeration, rate validation, ChangeDisplaySettings routing, query filtering.
- **CHANGELOG.md** (this file).

### Changed
- Bare `except:` clauses replaced with `except Exception` and properly logged.
- `set_refresh_rate()` now raises `ValueError` for unsupported rates rather than silently failing.
- Secondary monitors use `ChangeDisplaySettingsEx()` instead of `ChangeDisplaySettings()`.
- Active refresh rate now shown with a `✓` checkmark in the query results.
- `setup.ps1` now prints verbose step summaries with timing information.

### Fixed
- Plugin no longer crashes when no display modes can be enumerated.
- Invalid action keyword suffixes (e.g. `hzXYZ`) now gracefully fall back to primary monitor.

---

## [v0.1.0-alpha] – 2026-06-16 – Initial Public Release

### Added
- First working release of the hz-plugin for Flow Launcher.
- Single-monitor refresh rate listing and switching via `win32api`.
- Display Settings shortcut on `Shift+Enter`.
- `install.ps1` one-liner installer.
- `setup.ps1` for local development setup.
- Pre-packaged `hz-plugin.zip` bundled with all dependencies.
- Auto-open Instagram profile after installation.
- README with PowerShell and manual installation instructions.
