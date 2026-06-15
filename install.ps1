$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/psycodess/hz-plugin/archive/refs/heads/main.zip"
$TempZip = "$env:TEMP\hz-plugin.zip"
$ExtractPath = "$env:TEMP\hz-plugin-extract"

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
Write-Host "Downloading plugin from GitHub..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $RepoUrl -OutFile $TempZip -UseBasicParsing

# 3. Extract ZIP
Write-Host "Extracting files..." -ForegroundColor Cyan
if (Test-Path $ExtractPath) { Remove-Item -Recurse -Force $ExtractPath }
Expand-Archive -Path $TempZip -DestinationPath $ExtractPath -Force

# 4. Move to Flow Launcher plugins folder
Write-Host "Installing to Flow Launcher..." -ForegroundColor Cyan
if (Test-Path $DestDir) { Remove-Item -Recurse -Force $DestDir }
Move-Item -Path "$ExtractPath\hz-plugin-main" -Destination $DestDir -Force

# 5. Clean up temp files
Remove-Item -Path $TempZip -Force
Remove-Item -Recurse -Force $ExtractPath

# 6. Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
try {
    $pyVersion = python --version 2>&1
    Write-Host "Python detected: $pyVersion" -ForegroundColor Green
} catch {
    Write-Warning "Python is not installed or not in PATH! Please install Python from https://python.org to run this plugin."
    exit 0
}

# Run pip to install dependencies to lib folder
& pip install -r "$DestDir\requirements.txt" -t "$DestDir\lib" --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "=== Installation Successful! ===" -ForegroundColor Green
    Write-Host "Please restart Flow Launcher and trigger with 'hz'." -ForegroundColor Yellow
} else {
    Write-Warning "Failed to install Python dependencies automatically. You may need to run: pip install -r '$DestDir\requirements.txt' -t '$DestDir\lib'"
}
