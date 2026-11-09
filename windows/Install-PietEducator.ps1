[CmdletBinding()]
param(
    [ValidateSet('6-9', '10-12', '13-17', 'adult')][string]$AgeBand,
    [switch]$ValidateOnly
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$SourceRoot = Split-Path -Parent $PSScriptRoot

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Executable. Setup can be run again after fixing this step." }
}

function Find-Python {
    $Candidates = @()
    foreach ($Name in @('py', 'python', 'python3')) {
        $Found = Get-Command $Name -ErrorAction SilentlyContinue
        if ($Found) { $Candidates += $Found.Source }
    }
    if ($env:LOCALAPPDATA) {
        $Candidates += @(Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python*\python.exe') -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
    }
    foreach ($Candidate in $Candidates) {
        if ($Candidate -match '\\WindowsApps\\') { continue }
        try {
            $Result = & $Candidate -c "import sys; print(sys.executable if (3, 9) <= sys.version_info[:2] < (3, 15) else '')" 2>$null
            if ($LASTEXITCODE -eq 0 -and $Result -and (Test-Path -LiteralPath ([string]$Result))) { return [string]$Result }
        } catch { }
    }
    return $null
}

function Find-Ollama {
    $Found = Get-Command ollama -ErrorAction SilentlyContinue
    if ($Found) { return $Found.Source }
    $Known = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
    if (Test-Path -LiteralPath $Known) { return $Known }
    return $null
}

function Install-Prerequisite {
    param([string]$PackageId, [string]$ManualUrl)
    $Winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $Winget) { throw "Install the missing requirement from $ManualUrl, then run Install-Windows.cmd again. Windows App Installer provides winget." }
    Write-Host "Installing $PackageId. Review any installer or licence prompts that appear."
    Invoke-Checked $Winget.Source @('install', '--exact', '--id', $PackageId, '--source', 'winget', '--scope', 'user', '--interactive', '--no-upgrade')
    # New installations are not added to the PATH of an already running process.
    $env:PATH = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}

function Test-OllamaReady {
    try {
        $Response = Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2
        return ($null -ne $Response.PSObject.Properties['models'])
    } catch { return $false }
}

try {
    $Required = @('server.py', 'educator.py', 'library.py', 'extract_material.py', 'windows_launcher.py', 'requirements.txt', 'Modelfile', 'lessons.json', 'web', 'tests', 'windows\Start-PietEducator.cmd')
    foreach ($Relative in $Required) {
        if (-not (Test-Path -LiteralPath (Join-Path $SourceRoot $Relative))) { throw "Missing $Relative. Extract the complete Piet-Educator ZIP before running setup." }
    }
    if ($ValidateOnly) { Write-Host 'Windows installer source layout is valid.'; return }
    if ([Environment]::OSVersion.Platform -ne 'Win32NT') { throw 'This installer is for Windows.' }
    if (-not [Environment]::Is64BitOperatingSystem) { throw 'Piet Educator requires 64-bit Windows.' }
    if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { throw 'This setup targets x64 Windows. ARM devices need a separate compatibility review.' }

    $InstallHome = Join-Path $env:LOCALAPPDATA 'PietEducator'
    $App = Join-Path $InstallHome 'app'
    $Data = Join-Path $InstallHome 'data'
    $Settings = Join-Path $InstallHome 'settings.json'
    if (Test-Path -LiteralPath $Settings) {
        $Previous = Get-Content -LiteralPath $Settings -Raw | ConvertFrom-Json
        if (-not $AgeBand) { $AgeBand = [string]$Previous.age_band }
    }
    if (-not $AgeBand) {
        Write-Host 'Choose the learning space: 1 = ages 6-9, 2 = ages 10-12, 3 = ages 13-17, 4 = adult.'
        $Choice = Read-Host 'Enter 1, 2, 3 or 4 (Enter selects ages 6-9)'
        switch ($Choice) {
            '' { $AgeBand = '6-9' }
            '1' { $AgeBand = '6-9' }
            '2' { $AgeBand = '10-12' }
            '3' { $AgeBand = '13-17' }
            '4' { $AgeBand = 'adult' }
            default { throw 'Choose one of the four age settings. No adult fallback was selected.' }
        }
    }
    if ($AgeBand -notin @('6-9', '10-12', '13-17', 'adult')) { throw 'The saved age setting is invalid.' }
    if (Test-Path -LiteralPath $App) {
        Write-Host 'If Piet is running, close its server window before continuing.'
        Read-Host 'Press Enter when Piet is closed' | Out-Null
    }

    $Python = Find-Python
    if (-not $Python) { Install-Prerequisite 'Python.Python.3.13' 'https://www.python.org/downloads/windows/'; $Python = Find-Python }
    if (-not $Python) { throw 'Python was installed but was not found. Close this window and run setup again.' }
    $Ollama = Find-Ollama
    if (-not $Ollama) { Install-Prerequisite 'Ollama.Ollama' 'https://ollama.com/download/windows'; $Ollama = Find-Ollama }
    if (-not $Ollama) { throw 'Ollama was installed but was not found. Close this window and run setup again.' }

    New-Item -ItemType Directory -Force -Path $InstallHome, $App, $Data | Out-Null
    foreach ($Folder in @($InstallHome, $App, $Data)) {
        if ((Get-Item -LiteralPath $Folder).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Choose a local installation folder without links: $Folder" }
    }
    # Restrict the application and books to this Windows account, SYSTEM and administrators.
    $Sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    Invoke-Checked 'icacls.exe' @($InstallHome, '/inheritance:r', '/grant:r', "*${Sid}:(OI)(CI)F", '*S-1-5-18:(OI)(CI)F', '*S-1-5-32-544:(OI)(CI)F')

    $Files = @('server.py', 'educator.py', 'library.py', 'extract_material.py', 'windows_launcher.py', 'requirements.txt', 'Modelfile', 'lessons.json', 'README.md', 'CURRICULUM.md', 'VALIDATION.md', 'WINDOWS-INSTALL.md')
    foreach ($File in $Files) { Copy-Item -LiteralPath (Join-Path $SourceRoot $File) -Destination (Join-Path $App $File) -Force }
    foreach ($Folder in @('web', 'tests')) {
        New-Item -ItemType Directory -Force -Path (Join-Path $App $Folder) | Out-Null
        Copy-Item -Path (Join-Path $SourceRoot "$Folder\*") -Destination (Join-Path $App $Folder) -Recurse -Force
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Start-PietEducator.cmd') -Destination (Join-Path $App 'Start-PietEducator.cmd') -Force
    # Deliberate allowlist: source data/, credentials and Git history are never copied.
    $Runtime = Join-Path $InstallHome 'runtime'
    $VenvPython = Join-Path $Runtime 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $VenvPython)) { Invoke-Checked $Python @('-m', 'venv', $Runtime) }
    Invoke-Checked $VenvPython @('-m', 'pip', 'install', '--disable-pip-version-check', '-r', (Join-Path $App 'requirements.txt'))
    @{schema_version = 1; age_band = $AgeBand} | ConvertTo-Json | Set-Content -LiteralPath $Settings -Encoding UTF8

    $env:OLLAMA_HOST = '127.0.0.1:11434'
    $env:OLLAMA_NO_CLOUD = '1'
    if (-not (Test-OllamaReady)) {
        Start-Process -FilePath $Ollama -ArgumentList 'serve' -WindowStyle Hidden | Out-Null
        for ($Attempt = 0; $Attempt -lt 60 -and -not (Test-OllamaReady); $Attempt++) { Start-Sleep -Milliseconds 500 }
    }
    if (-not (Test-OllamaReady)) { throw 'Open Ollama from the Start menu, then run setup again.' }
    Write-Host 'Downloading the local Qwen model (approximately 5.2 GB on first setup). Keep this window open.'
    Invoke-Checked $Ollama @('pull', 'qwen3:8b')
    Invoke-Checked $Ollama @('create', 'piet-educator', '-f', (Join-Path $App 'Modelfile'))
    Invoke-Checked $VenvPython @('-m', 'unittest', 'discover', '-s', (Join-Path $App 'tests'), '-v')
    Invoke-Checked $VenvPython @((Join-Path $App 'windows_launcher.py'), '--home', $InstallHome, '--diagnostics')

    $Shell = New-Object -ComObject WScript.Shell
    $ShortcutFolders = @([Environment]::GetFolderPath('Desktop'), (Join-Path ([Environment]::GetFolderPath('Programs')) 'Piet Educator'))
    foreach ($ShortcutFolder in $ShortcutFolders) {
        New-Item -ItemType Directory -Force -Path $ShortcutFolder | Out-Null
        foreach ($Page in @('reader', 'library')) {
            $Name = if ($Page -eq 'reader') { 'Piet Educator' } else { 'Piet Educator Library' }
            $Link = $Shell.CreateShortcut((Join-Path $ShortcutFolder "$Name.lnk"))
            $Link.TargetPath = $env:ComSpec
            $Link.Arguments = '/d /c ""' + (Join-Path $App 'Start-PietEducator.cmd') + '" --page ' + $Page + '"'
            $Link.WorkingDirectory = $App
            $Link.Description = 'Private local learning support'
            $Link.Save()
        }
    }
    Write-Host "Piet Educator is installed. Books are stored separately in $Data."
    Write-Host 'Open the Piet Educator shortcut on your Desktop. Keep its window open while learning.'
} catch {
    Write-Host ('Setup could not finish: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
