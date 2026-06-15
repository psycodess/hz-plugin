import sys
import os
from pathlib import Path

import site

plugindir = Path(__file__).parent
site.addsitedir(str(plugindir / "lib"))
sys.path = [str(plugindir / p) for p in (".", "plugin")] + sys.path

from flowlauncher import FlowLauncher
import win32api
import win32con


class RefreshRatePlugin(FlowLauncher):
    def get_available_rates(self) -> list[int]:
        rates: set[int] = set()
        i = 0
        while True:
            try:
                devmode = win32api.EnumDisplaySettings(None, i)
                rates.add(devmode.DisplayFrequency)
                i += 1
            except:
                break
        return sorted(rates)

    def get_current_rate(self) -> int:
        devmode = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
        return devmode.DisplayFrequency

    def query(self, query: str) -> list[dict]:
        query = query.strip().lower()
        current = self.get_current_rate()
        available = self.get_available_rates()

        if query:
            filtered = [r for r in available if query in str(r)]
        else:
            filtered = available

        results = []
        for rate in filtered:
            subtitle = f"Current: {current}Hz"
            if rate == current:
                subtitle = "Already active"

            results.append({
                "title": f"Set refresh rate to {rate}Hz",
                "subTitle": subtitle,
                "icoPath": "Images/app.png",
                "jsonRPCAction": {
                    "method": "set_refresh_rate",
                    "parameters": [str(rate)]
                }
            })

        if not results:
            results.append({
                "title": "No matching refresh rates found",
                "subTitle": f"Available: {', '.join(map(str, available))}Hz",
                "icoPath": "Images/app.png"
            })

        return results

    def set_refresh_rate(self, rate: str) -> None:
        target = int(rate)
        current = self.get_current_rate()
        if target == current:
            return

        devmode = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
        devmode.DisplayFrequency = target
        result = win32api.ChangeDisplaySettings(devmode, 0)

        if result == win32con.DISP_CHANGE_SUCCESSFUL:
            title = f"Refresh rate changed to {target}Hz"
        elif result == win32con.DISP_CHANGE_RESTART:
            title = f"Restart required to apply {target}Hz"
        else:
            title = f"Failed to change refresh rate (error: {result})"

        from flowlauncher import FlowLauncherAPI
        FlowLauncherAPI.show_msg("Monitor Refresh Rate", title)

    def context_menu(self, data: str | None) -> list[dict]:
        return [
            {
                "title": "Open Display Settings",
                "subTitle": "Open Windows display settings panel",
                "icoPath": "Images/app.png",
                "jsonRPCAction": {
                    "method": "open_display_settings",
                    "parameters": []
                }
            }
        ]

    def open_display_settings(self) -> None:
        os.startfile("ms-settings:display")


if __name__ == "__main__":
    RefreshRatePlugin()
