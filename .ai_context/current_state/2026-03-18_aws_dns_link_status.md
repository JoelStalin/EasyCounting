# AWS and DNS Link Status - 2026-03-18

## Objective

Verify whether this workstation is already linked to AWS/Route53 and whether the target domain points to this machine.

## Local findings

- AWS CLI is installed:
  - `aws-cli/2.33.17`
- Existing local AWS profiles are not usable:
  - `default`: `SignatureDoesNotMatch`
  - `dev01`: `InvalidClientTokenId`
- Current public IP of this workstation at verification time:
  - `172.58.135.164`

## DNS findings

- `getupsoft.com`
  - result: `NXDOMAIN`
- `chefalitas.com.do`
  - result: DNS request timed out from this host

## Local port findings

- Port `80` is listening on this workstation
- Listener owner appears as `System` (`PID 4`)
- Port `443` was not observed listening during this verification

## Conclusion

The machine is not yet reliably linked to Route53 for the target domain because:

1. local AWS credentials are invalid or expired
2. the target domain does not currently resolve correctly from this host
3. HTTPS exposure is not ready on this workstation yet

## Required to continue

- valid AWS CLI credentials with Route53 permissions:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_SESSION_TOKEN` if temporary credentials or MFA-backed session is used
- target `HostedZoneId`
- exact record names to update
- confirmation of which domain should point to this workstation:
  - `getupsoft.com`
  - `chefalitas.com.do`
  - or both

## Existing scripts

- `scripts/automation/configure_aws_route53_profile.ps1`
- `scripts/automation/update_route53_getupsoft.ps1`

These are ready to use once valid credentials and the correct hosted zone are provided.
