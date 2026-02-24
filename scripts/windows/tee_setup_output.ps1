param(
    [Parameter(Mandatory = $true)]
    [string]$ScriptPath,
    [Parameter(Mandatory = $true)]
    [string]$LogFile,
    [Parameter(Mandatory = $true)]
    [string]$LogSource,
    [Parameter(Mandatory = $false)]
    [string]$ProjectRoot
)

$logDir = Split-Path -Path $LogFile
if ($logDir -and -not (Test-Path -Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Get-ProjectRootPath {
    param(
        [string]$ScriptPath,
        [string]$ProjectRootOverride
    )
    if ($ProjectRootOverride) {
        $cleanRoot = $ProjectRootOverride -replace '"', ''
        $cleanRoot = $cleanRoot.Trim()
        try {
            return (Resolve-Path -LiteralPath $cleanRoot).Path
        } catch {
            return $cleanRoot
        }
    }
    try {
        $resolvedScript = (Resolve-Path -LiteralPath $ScriptPath).Path
    } catch {
        return $null
    }
    $root = Split-Path -Parent $resolvedScript
    $root = Split-Path -Parent $root
    $root = Split-Path -Parent $root
    return $root
}

function Convert-ToRelativePath {
    param(
        [string]$Value,
        [string]$RootPath,
        [string]$RootPattern,
        [string]$RootPatternPosix
    )
    if (-not $Value -or -not $RootPath -or -not $RootPattern) {
        return $Value
    }
    $normalized = $Value -replace "(?i)$RootPattern", "."
    if ($RootPatternPosix -and $RootPatternPosix -ne $RootPattern) {
        $normalized = $normalized -replace "(?i)$RootPatternPosix", "."
    }
    return $normalized
}

$projectRootPath = Get-ProjectRootPath -ScriptPath $ScriptPath -ProjectRootOverride $ProjectRoot
$rootPattern = $null
$rootPatternPosix = $null
if ($projectRootPath) {
    $rootPattern = [regex]::Escape($projectRootPath)
    $rootPatternPosix = [regex]::Escape(($projectRootPath -replace "\\", "/"))
}

$consolePattern = '^(?<time>\d{2}:\d{2}:\d{2}Z?) \| (?<lvl>DBG|INF|WRN|ERR|CRT) \| (?<rest>.+)$'
$filePattern = '^(?<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z) \| (?<lvl>DBG|INF|WRN|ERR|CRT) \| (?<rest>.+)$'
$levelMap = @{
    "DBG" = "DEBUG"
    "INF" = "INFO"
    "WRN" = "WARNING"
    "ERR" = "ERROR"
    "CRT" = "CRITICAL"
}

$scriptArg = "`"$ScriptPath`" 2>&1"
$stream = $null
$writer = $null
try {
    $encoding = New-Object System.Text.UTF8Encoding $false
    $stream = [System.IO.File]::Open($LogFile, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    $writer = New-Object System.IO.StreamWriter $stream, $encoding
    $writer.AutoFlush = $true
    # Redirect stderr inside cmd to avoid PowerShell NativeCommandError output.
    function Test-IsPrefixedLine {
        param([string]$Value)
        return ($Value -match $consolePattern -or $Value -match $filePattern)
    }

    function Write-Entry {
        param([string]$Value)
        if ($null -eq $Value) {
            return
        }
        $line = $Value.ToString().TrimEnd()
        if ($line -match "\x00") {
            $line = $line -replace "\x00", ""
        }
        $line = Convert-ToRelativePath -Value $line -RootPath $projectRootPath -RootPattern $rootPattern -RootPatternPosix $rootPatternPosix
        $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        $entryLevel = "INFO"
        $entryMessage = $line
        if ($line -match $consolePattern -or $line -match $filePattern) {
            $level = $matches['lvl']
            $rest = $matches['rest']
            if ($levelMap.ContainsKey($level)) {
                $entryLevel = $levelMap[$level]
            }
            $entryMessage = $rest
        }
        $entryMessage = Convert-ToRelativePath -Value $entryMessage -RootPath $projectRootPath -RootPattern $rootPattern -RootPatternPosix $rootPatternPosix
        $entry = '{0} | {1} | {2} | {3}' -f $timestamp, $entryLevel, $LogSource, $entryMessage
        try { $writer.WriteLine($entry) } catch { }
        $line
    }

    $pendingLine = $null
    $pendingListing = $false
    & cmd /c $scriptArg | ForEach-Object {
        $line = $_
        if ($null -eq $line) {
            return
        }
        $line = $line.ToString().TrimEnd("`r", "`n")
        if ($line -match "\x00") {
            $line = $line -replace "\x00", ""
        }
        $line = $line.TrimEnd()
        if ($pendingListing) {
            if ($line -match "^\s*'") {
                Write-Entry -Value ($pendingLine.TrimEnd() + " " + $line.TrimStart())
                $pendingLine = $null
                $pendingListing = $false
                return
            }
            Write-Entry -Value $pendingLine
            $pendingLine = $null
            $pendingListing = $false
        }

        if ($line -match "(?i)\bListing\s*$") {
            $pendingLine = $line
            $pendingListing = $true
            return
        }

        Write-Entry -Value $line
    }
    if ($pendingListing -and $null -ne $pendingLine) {
        Write-Entry -Value $pendingLine
    }
} finally {
    if ($writer) { $writer.Dispose() }
    if ($stream) { $stream.Dispose() }
}

exit $LASTEXITCODE
