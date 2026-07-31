$python = "C:\Program Files\Python314\python.exe"
$script = Join-Path $PSScriptRoot "app.py"
& $python $script
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error running app. Press any key to exit."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
