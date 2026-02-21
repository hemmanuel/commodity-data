$ManifestPath = "formatted_manifest.json"
$DownloadDir = "data/raw/eia"

if (-not (Test-Path $ManifestPath)) {
    Write-Error "Manifest file not found: $ManifestPath"
    exit 1
}

if (-not (Test-Path $DownloadDir)) {
    Write-Warning "Download directory does not exist yet: $DownloadDir"
    $CurrentCount = 0
} else {
    $CurrentCount = (Get-ChildItem $DownloadDir).Count
}

try {
    $JsonContent = Get-Content $ManifestPath -Raw | ConvertFrom-Json
    # Handle different JSON structures if necessary, assuming dataset property exists
    if ($JsonContent.dataset) {
        $TotalCount = $JsonContent.dataset.PSObject.Properties.Count
    } else {
        $TotalCount = 0
        Write-Warning "Could not determine total count from manifest."
    }
} catch {
    Write-Error "Failed to parse manifest file."
    exit 1
}

Write-Host "Monitoring download progress..."
Write-Host "Target Directory: $DownloadDir"
Write-Host "Total Files Expected: $TotalCount"

while ($true) {
    if (Test-Path $DownloadDir) {
        $CurrentFiles = Get-ChildItem $DownloadDir
        $CurrentCount = $CurrentFiles.Count
        
        $Percent = 0
        if ($TotalCount -gt 0) {
            $Percent = [math]::Round(($CurrentCount / $TotalCount) * 100, 2)
        }

        $LastFile = $CurrentFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        $LastFileName = if ($LastFile) { $LastFile.Name } else { "None" }

        Write-Progress -Activity "Downloading EIA Data" -Status "$CurrentCount / $TotalCount files ($Percent%) - Last: $LastFileName" -PercentComplete $Percent
        
        if ($CurrentCount -ge $TotalCount) {
            Write-Host "`nDownload complete! ($CurrentCount / $TotalCount files)" -ForegroundColor Green
            break
        }
    }
    
    Start-Sleep -Seconds 1
}
