param(
    [string]$Python = "python"
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$previousPythonPath = $env:PYTHONPATH

try {
    $env:PYTHONPATH = Join-Path $repoRoot "src"
    & $Python -m mingyirx run `
        --config (Join-Path $repoRoot "configs\example.json") `
        --input (Join-Path $repoRoot "data\synthetic\prescriptions.csv") `
        --output (Join-Path $repoRoot "outputs\demo")
    exit $LASTEXITCODE
}
finally {
    $env:PYTHONPATH = $previousPythonPath
}
