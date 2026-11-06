# Push this project to GitHub, so Streamlit Community Cloud can deploy it.
#
# Run from the project folder in PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\push-to-github.ps1 -RepoUrl https://github.com/<you>/<repo>.git
# Omit -RepoUrl and the script will ask for it.

param(
    [string]$RepoUrl,
    [string]$Branch = 'main'
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host 'Git is not installed. Get it from https://git-scm.com/download/win and run this again.' -ForegroundColor Yellow
    exit 1
}

if (-not $RepoUrl) {
    $RepoUrl = Read-Host 'Paste your GitHub repo URL (it ends with .git)'
}
if (-not $RepoUrl) {
    Write-Host 'No repository URL given. Aborting.' -ForegroundColor Yellow
    exit 1
}

# Make sure git has an identity for the commit.
if (-not (git config user.email)) {
    git config user.email 'newstranscribe@example.com'
    git config user.name 'newstranscribe'
    Write-Host 'Set a local git identity (newstranscribe@example.com).'
    Write-Host 'Change it any time with: git config user.email you@example.com'
}

if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.git'))) {
    git init
}

git add -A
git commit -m 'Update newstranscribe' | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Nothing new to commit.'
}

git branch -M $Branch

$remotes = git remote
if ($remotes -contains 'origin') {
    git remote set-url origin $RepoUrl
} else {
    git remote add origin $RepoUrl
}

Write-Host ''
Write-Host 'Pushing to GitHub ...'
git push -u origin $Branch
Write-Host ''
Write-Host 'Done.' -ForegroundColor Green
Write-Host 'Next: open https://share.streamlit.io and deploy from this repo (main file path: app.py).'
