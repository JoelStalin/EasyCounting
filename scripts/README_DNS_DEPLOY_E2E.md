# DNS + Deploy + Selenium E2E (GetUpSoft DGII)

## DNS dinámico Route 53 (WSL)

```bash
chmod +x scripts/route53_update.sh scripts/route53_install_cron.sh
AWS_PROFILE=dev01 AWS_REGION=us-east-1 ./scripts/route53_update.sh
SCRIPT_PATH=/path/to/repo/scripts/route53_update.sh ./scripts/route53_install_cron.sh
```

## DNS dinámico (Docker)

```bash
docker run --rm \
  -v ~/.aws:/root/.aws \
  -v /path/to/repo/scripts:/scripts \
  -e AWS_PROFILE=dev01 \
  -e AWS_REGION=us-east-1 \
  amazon/aws-cli:2.15.45 \
  /bin/sh -c "/scripts/route53_update.sh"
```

## Certificados HTTPS (Let’s Encrypt)

```bash
chmod +x scripts/certbot_request.sh
LE_EMAIL=admin@getupsoft.com.do ./scripts/certbot_request.sh
```

Renovación:

```bash
chmod +x scripts/certbot_renew.sh
./scripts/certbot_renew.sh
```

## Deploy local

```bash
chmod +x scripts/deploy_local.sh
REPO_DIR=/path/to/repo ./scripts/deploy_local.sh
```

## Selenium E2E

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r e2e/requirements.txt

BASE_URL_ADMIN=https://dgiiadmin.getupsoft.com.do \
BASE_URL_CLIENT=https://dgiicliente.getupsoft.com.do \
TEST_USER=admin@getupsoft.com.do \
TEST_PASS='Admin@1234' \
pytest -c e2e/pytest.ini --html=artifacts/report.html
```
