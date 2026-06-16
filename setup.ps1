param(
    [switch]$InstallToFlowLauncher
)

$ErrorActionPreference = "Stop"
$PluginDir  = $PSScriptRoot
$StepCount  = if ($InstallToFlowLauncher) { 5 } else { 4 }
$StepNum    = 0
$StartTime  = Get-Date

function Write-Step {
    param([string]$Text)
    $script:StepNum++
    Write-Host ""
    Write-Host "[$script:StepNum/$StepCount] $Text" -ForegroundColor Cyan
}

function Write-OK   ([string]$msg) { Write-Host "  [OK]   $msg" -ForegroundColor Green  }
function Write-Fail ([string]$msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red    }
function Write-Info ([string]$msg) { Write-Host "  [INFO] $msg" -ForegroundColor White  }
function Write-Warn ([string]$msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow }

# ──────────────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     hz-plugin  ·  Setup Script       ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "  Plugin directory: $PluginDir" -ForegroundColor DarkGray
Write-Host ""

# ──────────────────────────────────────────────────────────────────────────────
# Step 1 – Python
# ──────────────────────────────────────────────────────────────────────────────
Write-Step "Checking Python installation"
try {
    $pyVersion = python --version 2>&1
    Write-OK "Python found: $pyVersion"
}
catch {
    Write-Fail "Python not found. Install Python 3.9+ from https://python.org"
    Write-Info "Make sure 'Add Python to PATH' is checked during installation."
    exit 1
}

# ──────────────────────────────────────────────────────────────────────────────
# Step 2 – Install dependencies into ./lib
# ──────────────────────────────────────────────────────────────────────────────
Write-Step "Installing dependencies into .\lib"
Write-Info "Running: pip install -r requirements.txt -t .\lib"
pip install -r "$PluginDir\requirements.txt" -t "$PluginDir\lib" --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Fail "pip install failed (exit code $LASTEXITCODE)."
    Write-Info "Try running: pip install -r requirements.txt -t .\lib"
    exit 1
}
$libItems = (Get-ChildItem "$PluginDir\lib" -Directory -ErrorAction SilentlyContinue).Count
Write-OK "Dependencies installed  ($libItems top-level packages in .\lib)"

# ──────────────────────────────────────────────────────────────────────────────
# Step 3 – Syntax check
# ──────────────────────────────────────────────────────────────────────────────
Write-Step "Verifying main.py syntax"
try {
    $pyPath = $PluginDir.Replace("\", "/")
    python -c "import ast; ast.parse(open('$pyPath/main.py', encoding='utf-8').read())"
    Write-OK "Syntax check passed"
}
catch {
    Write-Fail "Syntax error in main.py: $_"
    exit 1
}

# ──────────────────────────────────────────────────────────────────────────────
# Step 4 – Run tests (if pytest is available)
# ──────────────────────────────────────────────────────────────────────────────
Write-Step "Running unit tests"
if (Get-Command pytest -ErrorAction SilentlyContinue) {
    Write-Info "Running: pytest tests/ -v"
    pytest "$PluginDir\tests\" -v
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Some tests failed. The plugin may still work, but review the output above."
    }
    else {
        Write-OK "All tests passed"
    }
}
else {
    Write-Warn "pytest not found — skipping tests."
    Write-Info "Install with: pip install pytest"
}

# ──────────────────────────────────────────────────────────────────────────────
# Step 5 (optional) – Copy to Flow Launcher
# ──────────────────────────────────────────────────────────────────────────────
if ($InstallToFlowLauncher) {
    Write-Step "Installing plugin to Flow Launcher"

    $flUserPath    = "$env:APPDATA\FlowLauncher\Plugins"
    $flPluginsPath = "$env:LOCALAPPDATA\FlowLauncher\Plugins"

    $target = $null
    if      (Test-Path $flPluginsPath) { $target = $flPluginsPath }
    elseif  (Test-Path $flUserPath)    { $target = $flUserPath    }

    if ($target) {
        $dest = "$target\hz-plugin"
        Write-Info "Destination: $dest"

        if (Test-Path $dest) {
            Write-Info "Existing installation found — cleaning up…"
            Remove-Item -Recurse -Force "$dest\*"
        }
        else {
            New-Item -ItemType Directory -Path $dest -Force | Out-Null
        }

        Copy-Item -Recurse -Force "$PluginDir\*" -Destination $dest `
            -Exclude ".git", ".gitignore", "*.zip", "*.resolved", "tests"

        $fileCount = (Get-ChildItem $dest -Recurse -File).Count
        Write-OK "Plugin installed to $dest  ($fileCount files copied)"
        Write-Info "Restart Flow Launcher (right-click tray icon → Restart) to load the plugin."
    }
    else {
        Write-Warn "Flow Launcher plugins directory not found."
        Write-Info "Checked: $flPluginsPath"
        Write-Info "Checked: $flUserPath"
        Write-Warn "Please copy the plugin folder to your Flow Launcher Plugins directory manually."
    }
}

# ──────────────────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────────────────
$elapsed = (Get-Date) - $StartTime
Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║     Setup complete in $([math]::Round($elapsed.TotalSeconds, 1))s         ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Usage:" -ForegroundColor White
Write-Host "    Open Flow Launcher  (Alt + Space)" -ForegroundColor DarkGray
Write-Host "    Type  hz            → primary monitor" -ForegroundColor DarkGray
Write-Host "    Type  hz2           → second monitor" -ForegroundColor DarkGray
Write-Host "    Type  hz3           → third monitor  (etc.)" -ForegroundColor DarkGray
Write-Host ""

# Open Instagram Profile
Start-Process "https://instagram.com/psychowhoqustionmark"
