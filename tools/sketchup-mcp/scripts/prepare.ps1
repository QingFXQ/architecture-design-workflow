param([switch]$Quiet)
$ErrorActionPreference = 'Stop'
$integrationRoot = Split-Path -Parent $PSScriptRoot
$pin = Get-Content -LiteralPath (Join-Path $integrationRoot 'upstream.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($asset in $pin.assets) {
    $assetPath = Join-Path $integrationRoot ('vendor/' + $asset.name)
    if (-not (Test-Path -LiteralPath $assetPath -PathType Leaf)) { throw "Missing bundle: $assetPath" }
    $actual = (Get-FileHash -LiteralPath $assetPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $asset.sha256) { throw "Checksum mismatch: $($asset.name)" }
}
$runtimeRoot = Join-Path $integrationRoot 'runtime'
$runtimePath = Join-Path $runtimeRoot ('v' + $pin.version)
$entryPath = Join-Path $runtimePath 'server/index.mjs'
if (Test-Path -LiteralPath $runtimePath) {
    if (-not (Test-Path -LiteralPath $entryPath -PathType Leaf)) { throw "Incomplete runtime preserved at $runtimePath; inspect it before moving it aside." }
    $actual = (Get-FileHash -LiteralPath $entryPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $pin.server_sha256) { throw "Changed runtime preserved at $runtimePath; inspect it before moving it aside." }
} else {
    New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
    $stagePath = Join-Path $runtimeRoot ('stage-' + [Guid]::NewGuid().ToString('N'))
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $bundlePath = Join-Path $integrationRoot 'vendor/sketchup-mcp-1.3.0.mcpb'
    [System.IO.Compression.ZipFile]::ExtractToDirectory($bundlePath, $stagePath)
    $actual = (Get-FileHash -LiteralPath (Join-Path $stagePath 'server/index.mjs') -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $pin.server_sha256) { throw "Extracted server mismatch; stage preserved at $stagePath" }
    Move-Item -LiteralPath $stagePath -Destination $runtimePath
}
if (-not $Quiet) {
    Write-Output "Verified SketchUp MCP $($pin.version); runtime: $runtimePath"
    Write-Output 'No SketchUp plugin or client configuration was installed or changed.'
}
