$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/psycodess/hz-plugin/raw/main/hz-plugin.zip"
$TempZip = "$env:TEMP\hz-plugin.zip"

# 1. Determine Flow Launcher plugins folder
$flUserPath = "$env:APPDATA\FlowLauncher\Plugins"
$flPluginsPath = "$env:LOCALAPPDATA\FlowLauncher\Plugins"
$TargetDir = $null
if (Test-Path $flPluginsPath) { $TargetDir = $flPluginsPath }
elseif (Test-Path $flUserPath) { $TargetDir = $flUserPath }

if (-not $TargetDir) {
    Write-Error "Flow Launcher plugins directory not found. Please ensure Flow Launcher is installed."
    exit 1
}

$DestDir = "$TargetDir\hz-plugin"

# 2. Download ZIP
Write-Host "Downloading pre-packaged plugin from GitHub..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $RepoUrl -OutFile $TempZip -UseBasicParsing

# 3. Extract ZIP directly to the destination directory
Write-Host "Installing to Flow Launcher..." -ForegroundColor Cyan
if (Test-Path $DestDir) { Remove-Item -Recurse -Force $DestDir }
New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
Expand-Archive -Path $TempZip -DestinationPath $DestDir -Force

# 4. Clean up temp files
Remove-Item -Path $TempZip -Force

# 5. Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "Python detected: $pyVersion" -ForegroundColor Green
} catch {
    Write-Warning "Python is not installed or not in PATH! Please install Python from https://python.org to run this plugin."
}

Write-Host "=== Installation Successful! ===" -ForegroundColor Green
Write-Host "Please restart Flow Launcher and trigger with 'hz'." -ForegroundColor Yellow

# Open Instagram Profile
Start-Process "https://instagram.com/pfychowhoqustionmark"
