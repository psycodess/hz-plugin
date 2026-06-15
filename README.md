# Monitor Refresh Rate Changer for Flow Launcher

An easy-to-use Flow Launcher plugin to check and change your display monitor's refresh rate instantly using Python and the native Windows API.

![Icon](Images/app.png)

## Features

- **Check Current Rate:** Displays your current active monitor refresh rate.
- **List Available Rates:** Automatically queries Windows to discover all supported refresh rates for your primary display.
- **One-click Change:** Instantly switches the refresh rate when you select one from the list.
- **Display Settings Shortcut:** Includes a context menu shortcut (`Shift + Enter`) to quickly open the native Windows Display Settings panel.
- **Self-contained:** Pre-packaged with all required libraries (`pywin32` and `flowlauncher`), so no setup or pip installs are needed.

---

## 🚀 Installation Options

### Option 1: PowerShell Method (Recommended)

1. Open **PowerShell Administrator** (Right-click PowerShell and select "Run as administrator").
2. Paste and run the following command to download and install the plugin automatically:

```powershell
iex (iwr -UseBasicParsing 'https://raw.githubusercontent.com/psycodess/hz-plugin/main/install.ps1')
```

---

### Option 2: Manual Method

1. Download the pre-packaged [**`hz-plugin.zip`**](https://github.com/psycodess/hz-plugin/raw/main/hz-plugin.zip) from this repository.
2. Extract the contents of the ZIP file.
3. Paste the extracted folder into the Flow Launcher plugins directory:
   * Press `Win + R`, type `%APPDATA%\FlowLauncher\Plugins` (or `%LOCALAPPDATA%\FlowLauncher\Plugins`), and press Enter.
   * Create a folder named `hz-plugin` and paste all extracted files inside.
4. Restart Flow Launcher.

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
