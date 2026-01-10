param()

$logFile = $env:CC_LOG_FILE
if ([string]::IsNullOrWhiteSpace($logFile)) {
    exit 0
}

$logDir = Split-Path -Path $logFile
if ($logDir -and -not (Test-Path -Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$level = $env:CC_LOG_LEVEL
$source = $env:CC_LOG_SOURCE
$message = $env:CC_LOG_MESSAGE
$entry = '{0} | {1} | {2} | {3}' -f $timestamp, $level, $source, $message

$stream = $null
$writer = $null
try {
    $encoding = New-Object System.Text.UTF8Encoding $false
    $stream = [System.IO.File]::Open($logFile, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    $writer = New-Object System.IO.StreamWriter $stream, $encoding
    $writer.WriteLine($entry)
} finally {
    if ($writer) { $writer.Dispose() }
    if ($stream) { $stream.Dispose() }
}
