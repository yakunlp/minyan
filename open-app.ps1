"""Ensure the local transcription web app is running, then open it in Google Chrome.

Double-clicked through the desktop shortcut created by create-open-shortcut.ps1.
If the service is not reachable yet, it is started (in a normal window so it can
be seen and stopped), then Chrome is opened once the page responds.
"""

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
$url = 'http://localhost:8501'

function Test-AppRunning {
    try {
        Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3 | Out-Null
        return $true
    } catch {
        return $false
    }
}

if (-not (Test-AppRunning)) {
    if (-not (Test-Path -LiteralPath $python)) {
        Write-Host 'Virtual environment missing. Follow README.md to install dependencies first.'
        Read-Host 'Press Enter to close'
        exit 1
    }
    Write-Host 'Starting the transcription service ...'
    # Go through start.ps1 so the service window also prints the phone QR code.
    $startScript = Join-Path $root 'start.ps1'
    $startArgs = '-NoProfile -ExecutionPolicy Bypass -File "{0}"' -f $startScript
    Start-Process -FilePath 'powershell.exe' -ArgumentList $startArgs
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline -and -not (Test-AppRunning)) {
        Start-Sleep -Milliseconds 800
    }
    if (-not (Test-AppRunning)) {
        Write-Host 'The service did not become reachable in time. Check the server window for errors.'
        Read-Host 'Press Enter to close'
        exit 1
    }
}

$chrome = @(
    (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
    $(if (${env:ProgramFiles(x86)}) { Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe' }),
    (Join-Path $env:LocalAppData 'Google\Chrome\Application\chrome.exe')
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1

if ($chrome) {
    Start-Process -FilePath $chrome -ArgumentList $url
} else {
    Write-Host 'Google Chrome was not found; opening with the default browser instead.'
    Start-Process $url
}
