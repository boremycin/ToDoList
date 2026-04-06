param(
    [string]$Repository = "boremycin/ToDoList",
    [string]$Tag = "v1.0",
    [string]$AssetPath = "D:\Desktop\coding\RecordToday\release\RecordToday-windows-portable-fixed.zip",
    [string]$NotesPath = "D:\Desktop\coding\RecordToday\RELEASE_NOTES_v1.0.md",
    [string]$Token = $env:GITHUB_TOKEN
)

$ErrorActionPreference = "Stop"

if (-not $Token) {
    throw "Missing GITHUB_TOKEN. Set the environment variable or pass -Token."
}

if (-not (Test-Path -LiteralPath $AssetPath)) {
    throw "Asset not found: $AssetPath"
}

if (-not (Test-Path -LiteralPath $NotesPath)) {
    throw "Release notes not found: $NotesPath"
}

$headers = @{
    Authorization = "Bearer $Token"
    Accept = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
    "User-Agent" = "RecordToday-Release-Script"
}

$notes = Get-Content -LiteralPath $NotesPath -Raw -Encoding UTF8
$release = Invoke-RestMethod `
    -Method Get `
    -Headers $headers `
    -Uri "https://api.github.com/repos/$Repository/releases/tags/$Tag"

$updateBody = @{
    name = $Tag
    body = $notes
    draft = $false
    prerelease = $false
} | ConvertTo-Json

$null = Invoke-RestMethod `
    -Method Patch `
    -Headers $headers `
    -Uri "https://api.github.com/repos/$Repository/releases/$($release.id)" `
    -Body $updateBody

$assetName = [System.IO.Path]::GetFileName($AssetPath)
$existingAsset = $release.assets | Where-Object { $_.name -eq $assetName } | Select-Object -First 1

if ($existingAsset) {
    Invoke-RestMethod `
        -Method Delete `
        -Headers $headers `
        -Uri "https://api.github.com/repos/$Repository/releases/assets/$($existingAsset.id)"
}

$uploadHeaders = @{
    Authorization = "Bearer $Token"
    Accept = "application/vnd.github+json"
    "Content-Type" = "application/zip"
    "X-GitHub-Api-Version" = "2022-11-28"
    "User-Agent" = "RecordToday-Release-Script"
}

$uploadUri = "https://uploads.github.com/repos/$Repository/releases/$($release.id)/assets?name=$assetName"
$assetBytes = [System.IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $AssetPath))

$null = Invoke-RestMethod `
    -Method Post `
    -Headers $uploadHeaders `
    -Uri $uploadUri `
    -Body $assetBytes

Write-Output "Updated release $Tag with asset $assetName"
