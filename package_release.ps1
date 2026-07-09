param(
    [string]$RuntimeDir = ".\runtime\python",
    [string]$ZipDir = ".\release_packages",
    [string]$PackageName = "PriceTool_Portable",
    [switch]$IncludeRuntimeData
)

$ErrorActionPreference = "Stop"

$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimePath = Resolve-Path -LiteralPath (Join-Path $BaseDir $RuntimeDir) -ErrorAction SilentlyContinue
if (-not $RuntimePath) {
    throw "Embedded Python runtime not found: $(Join-Path $BaseDir $RuntimeDir)"
}
$RuntimePath = $RuntimePath.Path
$RuntimePython = Join-Path $RuntimePath "python.exe"
if (-not (Test-Path -LiteralPath $RuntimePython)) {
    throw "python.exe not found in runtime folder: $RuntimePath"
}

$ZipRoot = Join-Path $BaseDir $ZipDir
New-Item -ItemType Directory -Force -Path $ZipRoot | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$StageRoot = Join-Path $ZipRoot "_stage_$Stamp"
$StagePackage = Join-Path $StageRoot $PackageName
$ZipPath = Join-Path $ZipRoot "$PackageName`_$Stamp.zip"

function Copy-DirectoryFresh {
    param(
        [string]$Source,
        [string]$Destination
    )
    if (Test-Path -LiteralPath $Destination) {
        Remove-Item -LiteralPath $Destination -Recurse -Force
    }
    Copy-Item -LiteralPath $Source -Destination $Destination -Recurse -Force
}

function Copy-FileIfExists {
    param(
        [string]$Source,
        [string]$Destination
    )
    if (Test-Path -LiteralPath $Source) {
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host " UK Order Price Tool - Package Release"
Write-Host "========================================"
Write-Host "Source  : $BaseDir"
Write-Host "Runtime : $RuntimePath"
Write-Host "Output  : $ZipRoot"
Write-Host ""

Write-Host "[1/4] Preparing clean package folder..."
if (Test-Path -LiteralPath $StageRoot) {
    Remove-Item -LiteralPath $StageRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $StagePackage | Out-Null

Write-Host "[2/4] Copying source files and runtime..."
Copy-DirectoryFresh -Source (Join-Path $BaseDir "app") -Destination (Join-Path $StagePackage "app")
Copy-DirectoryFresh -Source (Join-Path $BaseDir "src") -Destination (Join-Path $StagePackage "src")
Copy-DirectoryFresh -Source (Join-Path $BaseDir "config") -Destination (Join-Path $StagePackage "config")
Copy-DirectoryFresh -Source (Join-Path $BaseDir ".streamlit") -Destination (Join-Path $StagePackage ".streamlit")
Copy-DirectoryFresh -Source $RuntimePath -Destination (Join-Path $StagePackage "python")

Copy-FileIfExists -Source (Join-Path $BaseDir "launcher.py") -Destination (Join-Path $StagePackage "launcher.py")
Copy-FileIfExists -Source (Join-Path $BaseDir "requirements-portable.txt") -Destination (Join-Path $StagePackage "requirements-portable.txt")
Copy-FileIfExists -Source (Join-Path $BaseDir "README_使用说明.txt") -Destination (Join-Path $StagePackage "README_使用说明.txt")
Copy-FileIfExists -Source (Join-Path $BaseDir "LICENSE") -Destination (Join-Path $StagePackage "LICENSE")

$EntryFiles = @(
    "start_tool.cmd",
    "stop_tool.cmd",
    "restart_tool.cmd",
    "open_page.cmd"
)
foreach ($File in $EntryFiles) {
    Copy-FileIfExists -Source (Join-Path $BaseDir $File) -Destination (Join-Path $StagePackage $File)
}

foreach ($Dir in @("data", "output", "logs", "temp")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $StagePackage $Dir) | Out-Null
}

if (-not $IncludeRuntimeData) {
    Write-Host "[3/4] Removing runtime data and caches..."
    $RuntimePatterns = @(
        "data\*.db",
        "data\*.sqlite",
        "logs\*",
        "output\*",
        "temp\*",
        "get-pip.py",
        "*.zip",
        "__pycache__",
        "*.pyc"
    )
    foreach ($Pattern in $RuntimePatterns) {
        Get-ChildItem -Path (Join-Path $StagePackage $Pattern) -Force -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
    Get-ChildItem -LiteralPath $StagePackage -Directory -Recurse -Force -Filter "__pycache__" -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -LiteralPath $StagePackage -File -Recurse -Force -Filter "*.pyc" -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
    foreach ($Dir in @("data", "output", "logs", "temp")) {
        New-Item -ItemType Directory -Force -Path (Join-Path $StagePackage $Dir) | Out-Null
    }
} else {
    Write-Host "[3/4] Keeping runtime data in package..."
}

Write-Host "[4/4] Creating zip package..."
if (Test-Path -LiteralPath $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}
Compress-Archive -LiteralPath $StagePackage -DestinationPath $ZipPath -Force
Remove-Item -LiteralPath $StageRoot -Recurse -Force

Write-Host ""
Write-Host "Done."
Write-Host "Zip package: $ZipPath"
Write-Host ""
