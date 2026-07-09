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
$FfmpegRoot = Join-Path $ProjectRoot "tools\ffmpeg"
$FfmpegCandidate = Get-ChildItem -Path $FfmpegRoot -Recurse -Filter "ffmpeg.exe" -File -ErrorAction SilentlyContinue |
    Sort-Object FullName |
    Select-Object -First 1

if (-not $FfmpegCandidate) {
    throw "Local ffmpeg.exe not found. Run RecordScreen.bat once before building."
}

$FfmpegBinary = "$($FfmpegCandidate.FullName);tools\ffmpeg\bin"

Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $ReleaseRoot
New-Item -ItemType Directory -Force -Path $ReleaseRoot, $WorkPath, $SpecPath | Out-Null

& $VenvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name RecordScreen `
    --distpath $ReleaseRoot `
    --workpath $WorkPath `
    --specpath $SpecPath `
    --add-data "$VersionFile;." `
    --add-binary $FfmpegBinary `
    --hidden-import soundcard.mediafoundation `
    --hidden-import cffi `
    record_screen_gui.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed"
}

$ExePath = Join-Path $ReleaseRoot "RecordScreen.exe"
if (-not (Test-Path $ExePath)) {
    throw "Portable executable was not created"
}

$ZipPath = Join-Path $ProjectRoot "dist\$ReleaseName.zip"
Remove-Item -Force -ErrorAction SilentlyContinue $ZipPath
Compress-Archive -Path $ExePath -DestinationPath $ZipPath

Write-Host "Portable release created:"
Write-Host $ExePath
Write-Host $ZipPath
