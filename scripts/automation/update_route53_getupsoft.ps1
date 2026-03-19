param(
    [Parameter(Mandatory = $true)][string]$HostedZoneId,
    [Parameter(Mandatory = $true)][string[]]$RecordNames,
    [string]$ProfileName = "getupsoft-route53",
    [int]$TTL = 300
)

$publicIp = (Invoke-RestMethod -Uri "https://checkip.amazonaws.com").Trim()
Write-Output "Current public IP: $publicIp"

foreach ($recordName in $RecordNames) {
    $currentDnsIp = aws route53 list-resource-record-sets `
        --hosted-zone-id $HostedZoneId `
        --profile $ProfileName `
        --query "ResourceRecordSets[?Name == '$recordName' && Type == 'A'].ResourceRecords[0].Value" `
        --output text

    if ($publicIp -eq $currentDnsIp) {
        Write-Output "No change needed for $recordName"
        continue
    }

    $changeBatch = @{
        Changes = @(
            @{
                Action = "UPSERT"
                ResourceRecordSet = @{
                    Name = $recordName
                    Type = "A"
                    TTL = $TTL
                    ResourceRecords = @(@{ Value = $publicIp })
                }
            }
        )
    } | ConvertTo-Json -Depth 6 -Compress

    aws route53 change-resource-record-sets `
        --hosted-zone-id $HostedZoneId `
        --profile $ProfileName `
        --change-batch $changeBatch
}
