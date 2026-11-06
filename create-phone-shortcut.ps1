"""Create a desktop shortcut that starts the service and shows a phone QR code.

Double-click the shortcut any time to start the transcription service; its window
prints the phone address and a QR you can scan - no need to open the web page on
the computer first.

    powershell -ExecutionPolicy Bypass -File 'D:\\myAI\\newstranscribe\\create-phone-shortcut.ps1'
"""

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$target = Join-Path $root 'start.ps1'
if (-not (Test-Path -LiteralPath $target)) {
    throw "Launcher missing: $target"
}

$desktop = [Environment]::GetFolderPath('Desktop')
$link = Join-Path $desktop 'News Transcriber (Phone).lnk'
$icon = "$(Join-Path $env:SystemRoot 'System32\\imageres.dll'),179"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($link)
$shortcut.TargetPath = 'powershell.exe'
$shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "{0}"' -f $target
$shortcut.WorkingDirectory = $root
$shortcut.IconLocation = $icon
$shortcut.Description = 'Start the transcription service and show a QR to open it on your phone'
$shortcut.Save()

Write-Host "Desktop shortcut created: $link"
Write-Host 'It starts the service WITHOUT opening a browser; scan the QR it prints with your phone.'
