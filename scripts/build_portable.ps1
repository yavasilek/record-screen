param(
    [switch] $SkipInstall
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

$Version = (Get-Content -Raw "VERSION").Trim()
if (-not $Version) {
    throw "VERSION is empty"
}

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    throw "Local .venv not found. Run RecordScreen.bat once before building."
}

if (-not $SkipInstall) {
    & $VenvPython -m pip install --disable-pip-version-check --quiet -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install runtime requirements"
    }

    & $VenvPython -m pip install --disable-pip-version-check --quiet -r requirements-dev.txt pyinstaller
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install build requirements"
    }
}

& $VenvPython -m pytest -v
if ($LASTEXITCODE -ne 0) {
    throw "Tests failed"
}

$ReleaseName = "RecordScreen-v$Version"
$ReleaseRoot = Join-Path $ProjectRoot "dist\$ReleaseName"
$WorkPath = Join-Path $ProjectRoot "build\pyinstaller"
$SpecPath = Join-Path $ProjectRoot "build\spec"
$VersionFile = Join-Path $ProjectRoot "VERSION"

Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $ReleaseRoot
New-Item -ItemType Directory -Force -Path $ReleaseRoot, $WorkPath, $SpecPath | Out-Null

& $VenvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name RecordScreen `
    --distpath $ReleaseRoot `
    --workpath $WorkPath `
    --specpath $SpecPath `
    --add-data "$VersionFile;." `
    --hidden-import soundcard.mediafoundation `
    --hidden-import cffi `
    record_screen_gui.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed"
}

$AppDir = Join-Path $ReleaseRoot "RecordScreen"
Copy-Item -Recurse -Force (Join-Path $ProjectRoot "tools") $AppDir
Copy-Item -Force (Join-Path $ProjectRoot "README.md") $AppDir
Copy-Item -Force (Join-Path $ProjectRoot "VERSION") $AppDir
Copy-Item -Force (Join-Path $ProjectRoot "RELEASES.md") $AppDir

$LaunchBat = Join-Path $AppDir "RecordScreen.bat"
@"
@echo off
setlocal
cd /d "%~dp0"
start "" "%~dp0RecordScreen.exe"
"@ | Set-Content -Encoding ASCII $LaunchBat

$ZipPath = Join-Path $ProjectRoot "dist\$ReleaseName.zip"
Remove-Item -Force -ErrorAction SilentlyContinue $ZipPath
Compress-Archive -Path $AppDir -DestinationPath $ZipPath

Write-Host "Portable release created:"
Write-Host $AppDir
Write-Host $ZipPath
