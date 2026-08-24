[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateRange(1, 99999)][int]$MinKingdom,
    [Parameter(Mandatory)][ValidateRange(1, 99999)][int]$MaxKingdom,
    [string]$TransferGroupId = '',
    [Parameter(Mandatory)][string]$OutputPath,
    [ValidateRange(1, 8)][int]$ThrottleLimit = 4,
    [string]$ApiBase = 'https://kingshot-atlas.onrender.com'
)

$ErrorActionPreference = 'Stop'
if ($MinKingdom -gt $MaxKingdom) {
    throw 'MinKingdom must be less than or equal to MaxKingdom.'
}

function Get-AtlasJson {
    param([Parameter(Mandatory)][string]$Uri)

    $lastError = $null
    foreach ($attempt in 1..2) {
        try {
            return Invoke-RestMethod -Uri $Uri -TimeoutSec 30
        }
        catch {
            $lastError = $_
            if ($attempt -lt 2) { Start-Sleep -Milliseconds 400 }
        }
    }
    throw $lastError
}

$directoryUri = "$ApiBase/api/v1/kingdoms/directory"
$mysticMetaUri = "$ApiBase/api/v1/rankings/mystic/players/meta"
$directory = Get-AtlasJson $directoryUri
$mysticMeta = Get-AtlasJson $mysticMetaUri
$groupPlayers = if ($TransferGroupId) {
    Get-AtlasJson "$ApiBase/api/v1/rankings/mystic/players?scope=group&transfer_group_id=$TransferGroupId"
}
else { $null }

$kingdoms = @($MinKingdom..$MaxKingdom | ForEach-Object -Parallel {
    $number = $_
    $base = $using:ApiBase

    function Get-WithRetry([string]$Uri) {
        $lastError = $null
        foreach ($attempt in 1..2) {
            try { return Invoke-RestMethod -Uri $Uri -TimeoutSec 30 }
            catch {
                $lastError = $_
                if ($attempt -lt 2) { Start-Sleep -Milliseconds 400 }
            }
        }
        throw $lastError
    }

    try {
        [pscustomobject]@{
            kingdom_number = $number
            profile = Get-WithRetry "$base/api/v1/kingdoms/$number"
            mystic = Get-WithRetry "$base/api/v1/kingdoms/$number/mystic-trial"
            error = $null
        }
    }
    catch {
        [pscustomobject]@{
            kingdom_number = $number
            profile = $null
            mystic = $null
            error = $_.Exception.Message
        }
    }
} -ThrottleLimit $ThrottleLimit)

$directoryItems = @($directory.items | Where-Object {
    [int]$_.kingdom_number -ge $MinKingdom -and [int]$_.kingdom_number -le $MaxKingdom
})
$errors = @($kingdoms | Where-Object error)
$payload = [ordered]@{
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    source = [ordered]@{
        site = 'https://ks-atlas.com/'
        api_base = $ApiBase
        directory_url = $directoryUri
        mystic_meta_url = $mysticMetaUri
        transfer_group_id = $TransferGroupId
        min_kingdom = $MinKingdom
        max_kingdom = $MaxKingdom
        mystic_meta = $mysticMeta
        group_player_snapshot = if ($groupPlayers) {
            [ordered]@{
                snapshot_week_date = $groupPlayers.snapshot_week_date
                source_snapshot_at = $groupPlayers.source_snapshot_at
                source_checked_at = $groupPlayers.source_checked_at
                updated_label = $groupPlayers.updated_label
            }
        }
        else { $null }
    }
    directory_items = $directoryItems
    group_top100_players = if ($groupPlayers) { @($groupPlayers.rows) } else { @() }
    kingdoms = @($kingdoms | Sort-Object kingdom_number)
}

$resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = [System.IO.Path]::GetDirectoryName($resolvedOutput)
if ($outputDirectory) {
    [System.IO.Directory]::CreateDirectory($outputDirectory) | Out-Null
}
$payload | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $resolvedOutput -Encoding utf8
Write-Output "Saved $($payload.kingdoms.Count) kingdoms to $resolvedOutput"
if ($errors.Count -gt 0) {
    throw "KS Atlas returned errors for $($errors.Count) kingdom(s): $(@($errors.kingdom_number) -join ', ')"
}
