terraform {
  backend "s3" {
    bucket         = "getupsoft-terraform"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "getupsoft-terraform-locks"
    encrypt        = true
  }
}
