# Monitor Refresh Rate Changer for Flow Launcher

An easy-to-use Flow Launcher plugin to check and change your display monitor's refresh rate instantly using Python and the native Windows API.

![Icon](Images/app.png)

## Features

- **Check Current Rate:** Displays your current active monitor refresh rate.
- **List Available Rates:** Automatically queries Windows to discover all supported refresh rates for your primary display.
- **One-click Change:** Instantly switches the refresh rate when you select one from the list.
- **Display Settings Shortcut:** Includes a context menu shortcut (`Shift + Enter`) to quickly open the native Windows Display Settings panel.
- **Zero Configuration:** Automatically installs and references dependencies (`pywin32`) in a self-contained local folder.

---

## 🚀 Easy Installation (One-liner PowerShell)

To install or update the plugin on any PC, open **PowerShell** (as Administrator if required by your execution policies) and run this one-liner command:

```powershell
powershell -ExecutionPolicy Bypass -Command "iex (iwr -UseBasicParsing 'https://raw.githubusercontent.com/psycodess/hz-plugin/main/install.ps1')"
```

*This command automatically downloads the plugin, extracts it to the Flow Launcher plugins directory, and configures the required Python dependencies.*

---

## 🛠️ Usage

1. Open Flow Launcher (`Alt + Space`).
2. Type `hz` to view all available refresh rates.
3. Select a rate and press `Enter` to apply it.
4. Press `Shift + Enter` on any result to open Windows Display Settings.

---

## Technical Details

- **Language:** Python
- **Interface:** JSON-RPC (via Flow Launcher's Python helper)
- **Windows APIs:** Leverages Python's `pywin32` library to communicate with the OS using `win32api.EnumDisplaySettings` and `win32api.ChangeDisplaySettings`.
- **Self-contained:** Dependencies are installed into a local `./lib` directory to keep your global Python environment clean.
