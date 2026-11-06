# Let your phone reach the transcription page over the local network.
# Run once, as Administrator: right-click this file > "Run as administrator",
# or from an elevated PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\allow-phone.ps1
#
# The rule only allows the local subnet (never the public internet).

$ErrorActionPreference = 'Stop'

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltinRole]::Administrator
)
if (-not $isAdmin) {
    Write-Host 'This script must run as Administrator.' -ForegroundColor Yellow
    Write-Host 'Right-click allow-phone.ps1, pick "Run as administrator", then confirm.'
    exit 1
}

$ruleName = 'News Transcriber 8501'

# Recreate a single rule so re-running the script stays idempotent.
Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule `
    -DisplayName $ruleName `
    -Direction Inbound `
    -Action Allow `
    -Protocol TCP `
    -LocalPort 8501 `
    -RemoteAddress LocalSubnet `
    -Profile Private, Public | Out-Null

Write-Host "Firewall rule '$ruleName' is now active (TCP 8501, local network only)."
Write-Host ''

$addresses = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
    Select-Object -ExpandProperty IPAddress
foreach ($ip in $addresses) {
    Write-Host "Phone URL: http://${ip}:8501"
}
Write-Host ''
Write-Host 'Keep the service window open on the PC, and make sure both devices share the same Wi-Fi.'
