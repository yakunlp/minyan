$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$target = Join-Path $root 'open-app.bat'
if (-not (Test-Path -LiteralPath $target)) {
    throw "Launcher missing: $target"
}
$desktop = [Environment]::GetFolderPath('Desktop')
$link = Join-Path $desktop 'News Transcriber.lnk'
$chrome = @(
    (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
    $(if (${env:ProgramFiles(x86)}) { Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe' }),
    (Join-Path $env:LocalAppData 'Google\Chrome\Application\chrome.exe')
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
$icon = if ($chrome) { "$chrome,0" } else { "$(Join-Path $env:SystemRoot 'System32\imageres.dll'),179" }
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($link)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $root
$shortcut.IconLocation = $icon
$shortcut.Description = 'Open the English news transcription tool in Google Chrome'
$shortcut.Save()
Write-Host "Desktop shortcut created: $link"
if (-not $chrome) {
    Write-Host 'Note: Google Chrome was not found, so the default browser icon was used.'
}
