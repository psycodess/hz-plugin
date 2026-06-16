"""
hz-plugin: Flow Launcher plugin to change monitor refresh rates.

Supports multi-monitor setups:
  - "hz"  → controls the primary (first) monitor
  - "hz1" → controls monitor 1 (first monitor)
  - "hz2" → controls monitor 2 (second monitor)
  - etc.

Author: SIFAT (psycodess)
"""
import sys
import os
import logging
from pathlib import Path
from typing import Optional

import site

# ---------------------------------------------------------------------------
# Bootstrap local library directory (pywin32, flowlauncher)
# ---------------------------------------------------------------------------
plugindir = Path(__file__).parent
site.addsitedir(str(plugindir / "lib"))
sys.path = [str(plugindir / p) for p in (".", "plugin")] + sys.path

from flowlauncher import FlowLauncher  # noqa: E402
from flowlauncher import FlowLauncherAPI  # noqa: E402
import win32api  # noqa: E402
import win32con  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log_file = plugindir / "hz-plugin.log"
logging.basicConfig(
    filename=str(log_file),
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("hz-plugin")

# ---------------------------------------------------------------------------
# ChangeDisplaySettings result-code map
# ---------------------------------------------------------------------------
DISP_CHANGE_CODES: dict[int, str] = {
    win32con.DISP_CHANGE_SUCCESSFUL:  "Refresh rate changed successfully",
    win32con.DISP_CHANGE_RESTART:     "Restart required to apply the new rate",
    win32con.DISP_CHANGE_FAILED:      "Failed: driver rejected the settings",
    win32con.DISP_CHANGE_BADMODE:     "Failed: mode is not supported by the driver",
    win32con.DISP_CHANGE_NOTUPDATED:  "Failed: unable to write to the registry",
    win32con.DISP_CHANGE_BADFLAGS:    "Failed: invalid combination of flags",
    win32con.DISP_CHANGE_BADPARAM:    "Failed: invalid parameter passed",
    win32con.DISP_CHANGE_BADDUALVIEW: "Failed: invalid dual-view mode",
}


def _disp_change_message(code: int) -> str:
    """Translate a ChangeDisplaySettings return code into a human-readable string."""
    return DISP_CHANGE_CODES.get(code, f"Unknown error (code {code})")


# ---------------------------------------------------------------------------
# Monitor enumeration helpers
# ---------------------------------------------------------------------------

def get_display_device_names() -> list[str]:
    """
    Return a list of active display device names (e.g. '\\\\.\\DISPLAY1').
    Only devices that are currently attached to the desktop are included.
    """
    devices: list[str] = []
    i = 0
    while True:
        try:
            dev = win32api.EnumDisplayDevices(None, i)
            # DISPLAY_DEVICE_ATTACHED_TO_DESKTOP = 0x1
            if dev.StateFlags & 0x1:
                devices.append(dev.DeviceName)
            i += 1
        except Exception:
            break
    logger.debug("Found %d active display devices: %s", len(devices), devices)
    return devices


def get_available_rates(device_name: Optional[str]) -> list[int]:
    """
    Return all unique refresh rates supported by *device_name*.
    Pass None to query the default (primary) monitor.
    """
    rates: set[int] = set()
    i = 0
    while True:
        try:
            devmode = win32api.EnumDisplaySettings(device_name, i)
            rates.add(devmode.DisplayFrequency)
            i += 1
        except Exception:
            break
    return sorted(rates)


def get_current_rate(device_name: Optional[str]) -> int:
    """Return the current active refresh rate for *device_name*."""
    devmode = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)
    return devmode.DisplayFrequency


def set_refresh_rate(device_name: Optional[str], target: int) -> str:
    """
    Change the refresh rate for *device_name* to *target* Hz.

    Returns a human-readable result message.
    Raises ValueError if the target rate is not in the supported list.
    """
    available = get_available_rates(device_name)
    if target not in available:
        msg = f"{target}Hz is not supported. Available: {', '.join(map(str, available))}Hz"
        logger.warning("Rejected: %s", msg)
        raise ValueError(msg)

    current = get_current_rate(device_name)
    if target == current:
        logger.info("Already at %dHz on %s – no change needed.", target, device_name)
        return f"Already at {target}Hz"

    devmode = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)
    devmode.DisplayFrequency = target

    if device_name is not None:
        # Use device-specific change; CDS_UPDATEREGISTRY | CDS_NORESET = 5
        result = win32api.ChangeDisplaySettingsEx(device_name, devmode, 0)
    else:
        result = win32api.ChangeDisplaySettings(devmode, 0)

    message = _disp_change_message(result)
    log_fn = logger.info if result == win32con.DISP_CHANGE_SUCCESSFUL else logger.error
    log_fn("ChangeDisplaySettings(%s → %dHz) → %d: %s", device_name, target, result, message)
    return message


# ---------------------------------------------------------------------------
# Query / keyword parsing
# ---------------------------------------------------------------------------

def _parse_keyword(action_keyword: str) -> tuple[int, Optional[str]]:
    """
    Parse the action keyword string from plugin.json / Flow Launcher into a
    zero-based monitor index and device name.

    "hz"  → index 0 (primary)
    "hz1" → index 0
    "hz2" → index 1
    ...

    Returns (monitor_index, device_name_or_None).
    device_name is None when the primary display is requested so that the
    win32api fallback to the primary monitor is used transparently.
    """
    keyword = action_keyword.strip().lower()
    devices = get_display_device_names()

    if keyword == "hz" or keyword == "hz1":
        idx = 0
    else:
        try:
            suffix = int(keyword[2:])
            idx = suffix - 1  # "hz2" → index 1
        except (ValueError, IndexError):
            idx = 0

    if not devices:
        return 0, None

    idx = max(0, min(idx, len(devices) - 1))
    # For the primary monitor, pass None so win32api picks it up correctly
    device_name: Optional[str] = None if idx == 0 else devices[idx]
    return idx, device_name


# ---------------------------------------------------------------------------
# Flow Launcher plugin class
# ---------------------------------------------------------------------------

class RefreshRatePlugin(FlowLauncher):
    """Flow Launcher plugin that manages monitor refresh rates."""

    # ------------------------------------------------------------------
    # query → called every time the user types after the keyword
    # ------------------------------------------------------------------
    def query(self, query: str) -> list[dict]:
        """
        Build the result list shown in Flow Launcher.

        The action keyword is embedded in the query string as the first
        token.  For example, if the user types "hz2 144" Flow Launcher
        passes "144" here and sets self.rpc_request["keyword"] = "hz2".
        We read the keyword from the RPC request to resolve the monitor.
        """
        try:
            raw_keyword: str = (
                getattr(self, "rpc_request", {}).get("keyword", "hz") or "hz"
            )
            _, device_name = _parse_keyword(raw_keyword)

            query = query.strip()

            # Input validation: only digits/empty allowed
            if query and not query.isdigit():
                return [self._error_result(
                    "Invalid input",
                    "Please type a number to filter refresh rates (e.g. 144)"
                )]

            current = get_current_rate(device_name)
            available = get_available_rates(device_name)

            if not available:
                return [self._error_result(
                    "No display modes found",
                    "Could not enumerate display settings for this monitor"
                )]

            filtered = [r for r in available if query in str(r)] if query else available

            results: list[dict] = []
            monitor_label = "primary" if device_name is None else device_name.strip("\\.")
            for rate in filtered:
                is_active = rate == current
                subtitle = "✓ Currently active" if is_active else f"Current: {current}Hz  |  Monitor: {monitor_label}"
                results.append({
                    "title": f"{'✓ ' if is_active else ''}Set to {rate}Hz",
                    "subTitle": subtitle,
                    "icoPath": "Images/app.png",
                    "jsonRPCAction": {
                        "method": "change_rate",
                        "parameters": [raw_keyword, str(rate)]
                    }
                })

            if not results:
                return [self._error_result(
                    f"No {query}Hz mode found",
                    f"Available rates: {', '.join(map(str, available))}Hz"
                )]

            return results

        except Exception as exc:
            logger.exception("query() raised an unexpected error")
            return [self._error_result("Plugin error", str(exc))]

    # ------------------------------------------------------------------
    # change_rate → called when the user selects a result
    # ------------------------------------------------------------------
    def change_rate(self, keyword: str, rate_str: str) -> None:
        """Validate input and apply the new refresh rate."""
        try:
            # Validate rate is a positive integer
            if not rate_str.isdigit() or int(rate_str) <= 0:
                logger.warning("Invalid rate value received: %r", rate_str)
                FlowLauncherAPI.show_msg("Invalid Rate", f"'{rate_str}' is not a valid refresh rate.")
                return

            target = int(rate_str)
            _, device_name = _parse_keyword(keyword)
            label = "Primary Monitor" if device_name is None else device_name.strip("\\.")

            message = set_refresh_rate(device_name, target)
            FlowLauncherAPI.show_msg(f"[{label}] Refresh Rate", message)

        except ValueError as exc:
            logger.warning("ValueError in change_rate: %s", exc)
            FlowLauncherAPI.show_msg("Unsupported Rate", str(exc))
        except Exception as exc:
            logger.exception("change_rate() raised an unexpected error")
            FlowLauncherAPI.show_msg("Error", str(exc))

    # ------------------------------------------------------------------
    # context_menu → Shift+Enter on any result
    # ------------------------------------------------------------------
    def context_menu(self, data: object) -> list[dict]:
        """Return context menu items (shown on Shift+Enter)."""
        return [
            {
                "title": "Open Display Settings",
                "subTitle": "Open the Windows Display Settings panel",
                "icoPath": "Images/app.png",
                "jsonRPCAction": {
                    "method": "open_display_settings",
                    "parameters": []
                }
            }
        ]

    def open_display_settings(self) -> None:
        """Open the Windows Display Settings page."""
        os.startfile("ms-settings:display")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _error_result(title: str, subtitle: str) -> dict:
        return {
            "title": title,
            "subTitle": subtitle,
            "icoPath": "Images/app.png",
        }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    RefreshRatePlugin()
