# Diagnostic script to check npm/Node.js installation
# This will help identify why npm is not recognized

$logPath = "c:\Users\bryan\git\inkling\.cursor\debug.log"

function Write-DebugLog {
    param($sessionId, $runId, $hypothesisId, $location, $message, $data)
    
    $logEntry = @{
        sessionId = $sessionId
        runId = $runId
        hypothesisId = $hypothesisId
        location = $location
        message = $message
        data = $data
        timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    } | ConvertTo-Json -Compress
    
    Add-Content -Path $logPath -Value $logEntry
}

$sessionId = "npm-diagnosis"
$runId = "run1"

# #region agent log - Hypothesis A: Node.js not installed
Write-DebugLog -sessionId $sessionId -runId $runId -hypothesisId "A" -location "diagnose_npm.ps1:16" -message "Checking if node.exe exists in PATH" -data @{}
$nodeInPath = Get-Command node -ErrorAction SilentlyContinue
Write-DebugLog -sessionId $sessionId -runId $runId -hypothesisId "A" -location "diagnose_npm.ps1:18" -message "node.exe in PATH result" -data @{found = ($null -ne $nodeInPath); path = if ($nodeInPath) { $nodeInPath.Path } else { "not found" }}
# #endregion

# #region agent log - Hypothesis B: npm not in PATH
Write-DebugLog -sessionId $sessionId -runId $runId -hypothesisId "B" -location "diagnose_npm.ps1:21" -message "Checking if npm.cmd exists in PATH" -data @{}
$npmInPath = Get-Command npm -ErrorAction SilentlyContinue
Write-DebugLog -sessionId $sessionId -runId $runId -hypothesisId "B" -location "diagnose_npm.ps1:23" -message "npm in PATH result" -data @{found = ($null -ne $npmInPath); path = if ($npmInPath) { $npmInPath.Path } else { "not found" }}
# #endregion

# #region agent log - Hypothesis C: Node.js installed in Program Files
Write-DebugLog -sessionId $sessionId -runId $runId -hypothesisId "C" -location "diagnose_npm.ps1:26" -message "Checking Program Files for Node.js" -data @{}
$programFilesNode = Test-Path "C:\Program Files\nodejs\node.exe"
$programFilesNpm = Test-Path "C:\Program Files\nodejs\npm.cmd"
Write-DebugLog -sessionId $sessionId -runId $runId -hypothesisId "C" -location "diagnose_npm.ps1:29" -message "Program Files check result" -data @{nodeExists = $programFilesNode; npmExists = $programFilesNpm}
# #endregion

# #region agent log - Hypothesis D: Node.js installed in Program Files (x86)
Write-DebugLog -sessionId $sessionId -runId $runId -hypothesisId "D" -location "diagnose_npm.ps1:32" -message "Checking Program Files (x86) for Node.js" -data @{}
$programFilesX86Node = Test-Path "C:\Program Files (x86)\nodejs\node.exe"
$programFilesX86Npm = Test-Path "C:\Program Files (x86)\nodejs\npm.cmd"
Write-DebugLog -sessionId $sessionId -runId $runId -hypothesisId "D" -location "diagnose_npm.ps1:35" -message "Program Files (x86) check result" -data @{nodeExists = $programFilesX86Node; npmExists = $programFilesX86Npm}
# #endregion

# #region agent log - Hypothesis E: PATH environment variable check
Write-DebugLog -sessionId $sessionId -runId $runId -hypothesisId "E" -location "diagnose_npm.ps1:38" -message "Checking PATH environment variable" -data @{}
$envPath = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
$pathEntries = $envPath -split ";" | Where-Object { $_ -like "*node*" -or $_ -like "*npm*" }
Write-DebugLog -sessionId $sessionId -runId $runId -hypothesisId "E" -location "diagnose_npm.ps1:41" -message "PATH entries containing node/npm" -data @{entries = $pathEntries}
# #endregion

# #region agent log - Hypothesis F: Checking for node version (if node exists)
Write-DebugLog -sessionId $sessionId -runId $runId -hypothesisId "F" -location "diagnose_npm.ps1:44" -message "Attempting to run node --version" -data @{}
try {
    $nodeVersion = node --version 2>&1
    Write-DebugLog -sessionId $sessionId -runId $runId -hypothesisId "F" -location "diagnose_npm.ps1:47" -message "node --version result" -data @{success = $true; output = $nodeVersion.ToString()}
} catch {
    Write-DebugLog -sessionId $sessionId -runId $runId -hypothesisId "F" -location "diagnose_npm.ps1:49" -message "node --version failed" -data @{success = $false; error = $_.Exception.Message}
}
# #endregion

Write-Host "Diagnostic complete. Check $logPath for detailed logs."
Write-Host "Summary:"
Write-Host "  Node.js in PATH: $(if ($nodeInPath) { 'YES - ' + $nodeInPath.Path } else { 'NO' })"
Write-Host "  npm in PATH: $(if ($npmInPath) { 'YES - ' + $npmInPath.Path } else { 'NO' })"
Write-Host "  Node.js in Program Files: $programFilesNode"
Write-Host "  npm in Program Files: $programFilesNpm"


