$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Virtual environment missing. Follow README.md to install dependencies first.'
}
& $python -c "import streamlit; import faster_whisper"
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Dependencies are missing or broken. Run this command, wait for completion, then start again:'
    Write-Host "& '$python' -m pip install -r '$PSScriptRoot\requirements.txt'"
    exit 1
}
Write-Host 'Computer: http://localhost:8501'
Write-Host 'Phone: scan the QR shown below with your phone camera (no need to open the page here first).'
# Force a UTF-8 console so the QR block characters render correctly.
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
& $python (Join-Path $PSScriptRoot 'phone_address.py') --port 8501
Write-Host 'Keep this terminal open. Press Ctrl+C to stop.'
& $python -m streamlit run (Join-Path $PSScriptRoot 'app.py')
exit $LASTEXITCODE