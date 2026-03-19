param(
    [Parameter(Mandatory = $true)][string]$AccessKeyId,
    [Parameter(Mandatory = $true)][string]$SecretAccessKey,
    [string]$SessionToken,
    [string]$ProfileName = "getupsoft-route53",
    [string]$Region = "us-east-1"
)

aws configure set aws_access_key_id $AccessKeyId --profile $ProfileName
aws configure set aws_secret_access_key $SecretAccessKey --profile $ProfileName
if ($SessionToken) {
    aws configure set aws_session_token $SessionToken --profile $ProfileName
}
aws configure set region $Region --profile $ProfileName
aws configure set output json --profile $ProfileName

aws sts get-caller-identity --profile $ProfileName
Write-Output "Configured AWS CLI profile '$ProfileName'."
