#Requires -Version 5.1
<#
Daily Bible Reading setup v2.0 (2026-09-07)
Replace the old setup-and-deploy.ps1 in the project folder with this file.
Run: .\setup-and-deploy.ps1
Optional: .\setup-and-deploy.ps1 -TestDate 2026-09-07

Uses existing project files. Does not overwrite the generator or reading plan.
Adds tzdata to requirements.txt if missing. Does not delete files, force-push,
rename existing branches, change repository visibility, or alter global Git config.
The ESV key is entered only into GitHub CLI's hidden interactive prompt.
#>
[CmdletBinding()]
param([string]$TestDate = "")

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$Repo = 'cwarloe/daily-bible-reading'
$RepositoryUrl = "https://github.com/$Repo"
$SiteUrl = 'https://cwarloe.github.io/daily-bible-reading/'
$OriginalPath = $env:PATH

# Native stderr is NOT necessarily a PowerShell failure (Windows PowerShell 5.1).
# Capture stderr without terminating, then explicitly check the native exit code.
# The permissive preferences are function-local and never change the caller.
function Invoke-Checked {
    param(
        [string]$Exe,
        [string[]]$Arguments,
        [switch]$AllowFailure
    )
    $ErrorActionPreference = 'Continue'
    $PSNativeCommandUseErrorActionPreference = $false
    $lines = @(& $Exe @Arguments 2>&1)
    $code = $LASTEXITCODE
    $outputText = ($lines | ForEach-Object { $_.ToString() }) -join "`n"
    if ($code -ne 0 -and -not $AllowFailure) {
        throw "Command failed (exit $code): $Exe $($Arguments -join ' ')`n$outputText"
    }
    return [pscustomobject]@{ ExitCode = $code; Text = $outputText }
}

function Invoke-Interactive {
    param([string]$Exe, [string[]]$Arguments)
    $ErrorActionPreference = 'Continue'
    $PSNativeCommandUseErrorActionPreference = $false
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Interactive command failed (exit $LASTEXITCODE). Setup stopped."
    }
}

function Assert-Origin {
    param([string]$Remote)
    if ($Remote -notmatch '^(https://github\.com/cwarloe/daily-bible-reading(?:\.git)?/?|git@github\.com:cwarloe/daily-bible-reading(?:\.git)?)$') {
        throw 'Origin does not point to cwarloe/daily-bible-reading. Stopped without changing it.'
    }
}

function Test-NotFound {
    param($Result)
    return ($Result.ExitCode -ne 0 -and $Result.Text -match 'HTTP 404')
}

Push-Location $PSScriptRoot
try {
    Write-Host "Daily Bible Reading setup v2.0" -ForegroundColor Cyan
    Write-Host "Folder: $PSScriptRoot"
    Write-Host "Target: $RepositoryUrl"

    $GitExe = (Get-Command git.exe -CommandType Application -ErrorAction Stop).Source
    $PythonExe = (Get-Command python.exe -CommandType Application -ErrorAction Stop).Source
    $ghCandidates = @()
    if ($env:ProgramFiles) { $ghCandidates += Join-Path $env:ProgramFiles 'GitHub CLI\gh.exe' }
    if ($env:LOCALAPPDATA) { $ghCandidates += Join-Path $env:LOCALAPPDATA 'Programs\GitHub CLI\gh.exe' }
    $ghCandidates += @(Get-Command gh.exe -CommandType Application -All -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Source)
    $GhExe = $null
    foreach ($candidate in ($ghCandidates | Select-Object -Unique)) {
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
        $version = Invoke-Checked $candidate @('--version') -AllowFailure
        if ($version.ExitCode -eq 0 -and $version.Text -match '^gh version ') {
            $GhExe = $candidate
            break
        }
    }
    if (-not $GhExe) { throw 'Official GitHub CLI gh.exe was not found. Install it before continuing.' }
    Write-Host "GitHub CLI: $GhExe"
    $env:PATH = (Split-Path -Parent $GhExe) + [IO.Path]::PathSeparator + $env:PATH
    $null = Invoke-Checked $PythonExe @('-c', "import sys; assert sys.version_info >= (3,11), 'Python 3.11 or later required'")

    $projectFiles = @(
        '.github/workflows/daily_reading.yml', '.gitignore', '.nojekyll',
        'generate_page.py', 'mcheyne.json', 'requirements.txt',
        'tests/test_generator.py', 'index.html', 'README.md',
        'CODEX_HANDOFF.md', 'setup-and-deploy.ps1'
    )
    foreach ($file in $projectFiles) {
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
            throw "Missing project file: $file. Put this script in the original extracted project folder."
        }
    }

    $rootCheck = Invoke-Checked $GitExe @('rev-parse', '--show-toplevel') -AllowFailure
    if ($rootCheck.ExitCode -eq 0) {
        $actualRoot = [IO.Path]::GetFullPath($rootCheck.Text.Trim()).TrimEnd('\','/')
        $expectedRoot = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\','/')
        if ($actualRoot -ne $expectedRoot) {
            throw 'This folder is inside a different Git repository. Stopping to protect that repository.'
        }
        $branch = Invoke-Checked $GitExe @('symbolic-ref', '--short', 'HEAD')
        if ($branch.Text.Trim() -ne 'main') {
            throw "Current branch is not main. Stopped without renaming or switching branches."
        }
        $remotes = Invoke-Checked $GitExe @('remote')
        if (($remotes.Text -split "`n") -contains 'origin') {
            $fetchUrl = Invoke-Checked $GitExe @('remote', 'get-url', 'origin')
            $pushUrl = Invoke-Checked $GitExe @('remote', 'get-url', '--push', 'origin')
            Assert-Origin $fetchUrl.Text.Trim()
            Assert-Origin $pushUrl.Text.Trim()
        }
        $staged = Invoke-Checked $GitExe @('diff', '--cached', '--name-only')
        foreach ($path in ($staged.Text -split "`n")) {
            if ($path -and $path -notin $projectFiles) {
                throw 'Unrelated staged changes exist. Unstage those changes before running setup.'
            }
        }
    }
    elseif ($rootCheck.Text -notmatch 'not a git repository') {
        throw "Cannot inspect the local repository:`n$($rootCheck.Text)"
    }

    $auth = Invoke-Checked $GhExe @('auth', 'status', '--hostname', 'github.com') -AllowFailure
    if ($auth.ExitCode -ne 0) {
        Invoke-Interactive $GhExe @('auth', 'login', '--hostname', 'github.com', '--git-protocol', 'https', '--web')
    }
    $userResponse = Invoke-Checked $GhExe @('api', '--hostname', 'github.com', 'user')
    $account = $userResponse.Text | ConvertFrom-Json
    if ($account.login -ne 'cwarloe') {
        throw "Signed in as $($account.login), not cwarloe. Switch accounts before continuing."
    }

    # Repair the missing cross-platform timezone dependency, once.
    $requirementsPath = Join-Path $PSScriptRoot 'requirements.txt'
    $requirementsText = [IO.File]::ReadAllText($requirementsPath)
    if ($requirementsText -notmatch '(?im)^\s*tzdata\b') {
        [IO.File]::AppendAllText($requirementsPath, "`r`ntzdata`r`n", [Text.UTF8Encoding]::new($false))
        Write-Host 'Added tzdata to requirements.txt.'
    }
    Write-Host 'Installing dependencies and running project tests...'
    Invoke-Interactive $PythonExe @('-m', 'pip', 'install', '-r', 'requirements.txt')
    Invoke-Interactive $PythonExe @('-m', 'unittest', 'discover', '-s', 'tests', '-v')

    if ([string]::IsNullOrWhiteSpace($TestDate)) {
        $dateResult = Invoke-Checked $PythonExe @('-c', "from datetime import datetime; from zoneinfo import ZoneInfo; print(datetime.now(ZoneInfo('America/Boise')).date().isoformat())")
        $TestDate = $dateResult.Text.Trim()
    }
    $parsedDate = [datetime]::MinValue
    if (-not [datetime]::TryParseExact($TestDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None, [ref]$parsedDate)) {
        throw 'TestDate must be a valid YYYY-MM-DD date.'
    }
    Write-Host "Reading date: $TestDate"

    $repoCheck = Invoke-Checked $GhExe @('api', '--hostname', 'github.com', "repos/$Repo") -AllowFailure
    if (Test-NotFound $repoCheck) {
        Write-Host "Creating public repository $Repo..."
        $null = Invoke-Checked $GhExe @('repo', 'create', $Repo, '--public', '--description', 'Daily MCheyne Bible readings formatted for ElevenReader')
        $repoCheck = Invoke-Checked $GhExe @('api', '--hostname', 'github.com', "repos/$Repo")
    }
    elseif ($repoCheck.ExitCode -ne 0) {
        throw "Repository lookup failed; no creation attempted:`n$($repoCheck.Text)"
    }
    $repoInfo = $repoCheck.Text | ConvertFrom-Json
    if ($repoInfo.private) { throw 'Existing repository is private. Stopped without changing its visibility.' }
    if (-not $repoInfo.permissions.push) { throw 'Your GitHub account cannot push to this repository.' }
    if ($repoInfo.size -gt 0 -and $repoInfo.default_branch -ne 'main') {
        throw 'Existing repository uses a different default branch. Stopped without changing it.'
    }

    if ($rootCheck.ExitCode -ne 0) {
        $null = Invoke-Checked $GitExe @('init', '-b', 'main')
    }
    $remotes = Invoke-Checked $GitExe @('remote')
    if (($remotes.Text -split "`n") -notcontains 'origin') {
        $null = Invoke-Checked $GitExe @('remote', 'add', 'origin', "$RepositoryUrl.git")
    }

    # Use the authenticated CLI as a credential helper ONLY for these commands.
    $networkArgs = @('-c', 'credential.helper=', '-c', 'credential.helper=!gh auth git-credential')
    $remoteHeads = Invoke-Checked $GitExe ($networkArgs + @('ls-remote', '--heads', 'origin'))
    if ($remoteHeads.Text.Trim()) {
        if ($remoteHeads.Text -notmatch 'refs/heads/main(?:\s|$)') {
            throw 'Remote has branches but no main branch. Stopped without rewriting history.'
        }
        $null = Invoke-Checked $GitExe ($networkArgs + @('fetch', 'origin', 'main'))
        $hasHead = Invoke-Checked $GitExe @('rev-parse', '--verify', 'HEAD') -AllowFailure
        if ($hasHead.ExitCode -ne 0) {
            throw 'Remote already contains commits but this folder has no history. Clone the existing repo rather than overwriting it.'
        }
        $ancestor = Invoke-Checked $GitExe @('merge-base', '--is-ancestor', 'FETCH_HEAD', 'HEAD') -AllowFailure
        if ($ancestor.ExitCode -eq 1) {
            $dirty = Invoke-Checked $GitExe @('status', '--porcelain')
            if ($dirty.Text.Trim()) {
                throw 'Remote has newer or different commits and local edits exist. Stopped to preserve both; share this message for reconciliation.'
            }
            $null = Invoke-Checked $GitExe @('merge', '--ff-only', 'FETCH_HEAD')
        }
        elseif ($ancestor.ExitCode -ne 0) { throw 'Could not compare Git histories. Stopped.' }
    }

    $nameCheck = Invoke-Checked $GitExe @('config', 'user.name') -AllowFailure
    if ($nameCheck.ExitCode -eq 1) { $null = Invoke-Checked $GitExe @('config', '--local', 'user.name', 'cwarloe') }
    elseif ($nameCheck.ExitCode -ne 0) { throw 'Could not read Git user.name.' }
    $emailCheck = Invoke-Checked $GitExe @('config', 'user.email') -AllowFailure
    if ($emailCheck.ExitCode -eq 1) {
        $null = Invoke-Checked $GitExe @('config', '--local', 'user.email', "$($account.id)+cwarloe@users.noreply.github.com")
    }
    elseif ($emailCheck.ExitCode -ne 0) { throw 'Could not read Git user.email.' }

    # Only explicitly named project files, never git add . (which could include keys).
    $null = Invoke-Checked $GitExe (@('add', '--') + $projectFiles)
    $staged = Invoke-Checked $GitExe @('diff', '--cached', '--name-only')
    if ($staged.Text.Trim()) {
        $null = Invoke-Checked $GitExe @('commit', '-m', 'Set up daily Bible reading with Windows-compatible installer')
    }
    Write-Host 'Pushing main (no force push)...'
    $null = Invoke-Checked $GitExe ($networkArgs + @('push', '-u', 'origin', 'main'))

    $secrets = Invoke-Checked $GhExe @('secret', 'list', '--repo', $Repo, '--json', 'name')
    $secretNames = @($secrets.Text | ConvertFrom-Json | ForEach-Object { $_.name })
    if ($secretNames -contains 'ESV_API_KEY') {
        Write-Host 'ESV_API_KEY already exists; keeping it unchanged.'
    }
    else {
        Write-Host 'Paste your ESV API key at the GitHub CLI hidden prompt, then press Enter.'
        Invoke-Interactive $GhExe @('secret', 'set', 'ESV_API_KEY', '--repo', $Repo)
    }

    $pagesCheck = Invoke-Checked $GhExe @('api', '--hostname', 'github.com', "repos/$Repo/pages") -AllowFailure
    if (Test-NotFound $pagesCheck) {
        $null = Invoke-Checked $GhExe @('api', '--hostname', 'github.com', '--method', 'POST', "repos/$Repo/pages", '-f', 'build_type=workflow')
    }
    elseif ($pagesCheck.ExitCode -eq 0) {
        $pagesInfo = $pagesCheck.Text | ConvertFrom-Json
        if ($pagesInfo.build_type -ne 'workflow') {
            $null = Invoke-Checked $GhExe @('api', '--hostname', 'github.com', '--method', 'PUT', "repos/$Repo/pages", '-f', 'build_type=workflow')
        }
    }
    else { throw "Pages lookup failed; no configuration changes attempted:`n$($pagesCheck.Text)" }

    Write-Host "Starting the reading workflow for $TestDate..."
    $null = Invoke-Checked $GhExe @('workflow', 'run', 'daily_reading.yml', '--repo', $Repo, '--ref', 'main', '-f', "date=$TestDate")
    Write-Host 'Workflow submitted. Deployment is not yet verified.' -ForegroundColor Green
    Write-Host "Watch its progress: $RepositoryUrl/actions/workflows/daily_reading.yml"
    Write-Host "After the run turns green, open: $SiteUrl"
    Write-Host 'Import the page into ElevenReader manually. No audio was generated by this script.'
}
catch {
    Write-Host "`nSETUP STOPPED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Completed steps remain in place. Do not delete .git or force-push.'
    throw
}
finally {
    $env:PATH = $OriginalPath
    Pop-Location
}
