# Run from any working directory without activating the virtual environment.
$projectRoot = $PSScriptRoot
$projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $projectPython)) {
    Write-Error 'Run: py setup_environment.py from the project directory first.'
    exit 1
}
& $projectPython (Join-Path $projectRoot 'transcribe_translate.py') @args
exit $LASTEXITCODE
