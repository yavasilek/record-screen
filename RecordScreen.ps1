param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $AppArgs
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$VenvPythonw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
$CodexPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

function Invoke-BasePython {
    param(
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )

    if (Test-Path $CodexPython) {
        & $CodexPython @Arguments
        return $LASTEXITCODE
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        & $py.Source -3 @Arguments
        return $LASTEXITCODE
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source @Arguments
        return $LASTEXITCODE
    }

    Write-Host "Python was not found. Install Python 3.11+ or run this from Codex Desktop." -ForegroundColor Red
    return 1
}

function Invoke-QuietCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string] $FilePath,
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments,
        [Parameter(Mandatory = $true)]
        [string] $FailureMessage
    )

    $output = & $FilePath @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        $output | ForEach-Object { Write-Host $_ }
        throw $FailureMessage
    }
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating local Python environment..."
    $code = Invoke-BasePython @("-m", "venv", ".venv")
    if ($code -ne 0) {
        throw "Failed to create .venv"
    }
}

Write-Host "Checking dependencies..."
Invoke-QuietCommand `
    -FilePath $VenvPython `
    -Arguments @("-m", "pip", "install", "--disable-pip-version-check", "--quiet", "-r", "requirements.txt") `
    -FailureMessage "Failed to install dependencies"

if ($AppArgs.Count -eq 0 -and (Test-Path $VenvPythonw)) {
    Start-Process -FilePath $VenvPythonw -ArgumentList @("-m", "screen_recorder.app") -WorkingDirectory $ProjectRoot
    exit 0
}

& $VenvPython -m screen_recorder.app @AppArgs
if ($LASTEXITCODE -ne 0) {
    throw "Program exited with error code $LASTEXITCODE"
}
