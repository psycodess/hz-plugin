param(
    [switch]$InstallToFlowLauncher
)

$ErrorActionPreference = "Stop"
$PluginDir = $PSScriptRoot

Write-Host "=== hz Plugin Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "[OK] Python: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Python not found. Install Python from https://python.org" -ForegroundColor Red
    exit 1
}

# Step 2: Install dependencies into ./lib
Write-Host ""; Write-Host "Installing dependencies to .\lib..." -ForegroundColor Yellow
pip install -r "$PluginDir\requirements.txt" -t "$PluginDir\lib" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] pip install failed" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Dependencies installed" -ForegroundColor Green

# Step 3: Verify main.py loads
Write-Host ""; Write-Host "Verifying plugin code..." -ForegroundColor Yellow
try {
    $pyPath = $PluginDir.Replace("\", "/")
    python -c "import ast; ast.parse(open('$pyPath/main.py', encoding='utf-8').read())"
    Write-Host "[OK] Syntax check passed" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Syntax error in main.py: $_" -ForegroundColor Red
    exit 1
}

# Step 4: Optional - copy to Flow Launcher
if ($InstallToFlowLauncher) {
    $flUserPath = "$env:APPDATA\FlowLauncher\Plugins"
    $flPluginsPath = "$env:LOCALAPPDATA\FlowLauncher\Plugins"

    $target = $null
    if (Test-Path $flPluginsPath) { $target = $flPluginsPath }
    elseif (Test-Path $flUserPath) { $target = $flUserPath }

    if ($target) {
        $dest = "$target\hz-plugin"
        if (Test-Path $dest) {
            Remove-Item -Recurse -Force "$dest\*"
        } else {
            New-Item -ItemType Directory -Path $dest -Force | Out-Null
        }
        Copy-Item -Recurse -Force "$PluginDir\*" -Destination $dest -Exclude ".git"
        Write-Host "[OK] Plugin copied to $dest" -ForegroundColor Green
        Write-Host "Restart Flow Launcher to load the plugin." -ForegroundColor Yellow
    } else {
        Write-Host "[WARN] Flow Launcher Plugins folder not found" -ForegroundColor Yellow
        Write-Host "Looked in: $flPluginsPath and $flUserPath" -ForegroundColor Yellow
        Write-Host "Copy the plugin folder manually." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
Write-Host "Usage: Open Flow Launcher (Alt+Space), type: hz" -ForegroundColor White
