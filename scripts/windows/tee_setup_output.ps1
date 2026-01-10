param(
    [Parameter(Mandatory = $true)]
    [string]$ScriptPath,
    [Parameter(Mandatory = $true)]
    [string]$LogFile,
    [Parameter(Mandatory = $true)]
    [string]$LogSource
)

$logDir = Split-Path -Path $LogFile
if ($logDir -and -not (Test-Path -Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$scriptArg = "`"$ScriptPath`""
$stream = $null
$writer = $null
try {
    $encoding = New-Object System.Text.UTF8Encoding $false
    $stream = [System.IO.File]::Open($LogFile, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    $writer = New-Object System.IO.StreamWriter $stream, $encoding
    $writer.AutoFlush = $true
    & cmd /c $scriptArg 2>&1 | ForEach-Object {
        $line = $_
        $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        $entry = '{0} | INFO | {1} | {2}' -f $timestamp, $LogSource, $line
        try { $writer.WriteLine($entry) } catch { }
        $line
    }
} finally {
    if ($writer) { $writer.Dispose() }
    if ($stream) { $stream.Dispose() }
}

exit $LASTEXITCODE
