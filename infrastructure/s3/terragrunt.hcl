locals {
  global_vars  = read_terragrunt_config(find_in_parent_folders("global.hcl")).locals
  account_vars = read_terragrunt_config(find_in_parent_folders("account.hcl")).locals
  app_name     = local.global_vars.app_name   
  aws_region   = try(local.account_vars.aws_region, "us-east-1")
  environment  = local.account_vars.environment
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
    terraform {
      required_providers {
        aws = {
          source  = "hashicorp/aws"
          version = "5.56.1"
        }
      }
    }
    provider "aws" {
      region = "${local.aws_region}"
      skip_metadata_api_check     = true
      skip_region_validation      = true
      skip_credentials_validation = true
    }
  EOF
}

terraform {
  source  = "terraform-aws-modules/s3-bucket/aws"
}

inputs = {
  bucket                   = try(local.account_vars.bucket, "${local.app_name}-${local.environment}-${local.aws_region}")
  acl                      = "private"
  control_object_ownership = true
  object_ownership         = "ObjectWriter"
  versioning               = { 
    enabled = true 
    }
  tags                     = {
    "Environment" = local.environment
    "Region"      = local.aws_region
    "Terraform"   = "true"
    }
}

remote_state {
  disable_init = tobool(get_env("TERRAGRUNT_DISABLE_INIT", "false"))
  backend      = "s3"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }
  config = {
    bucket         = "${local.app_name}-${local.environment}-${local.aws_region}-tf-state"
    key            = "s3/${path_relative_to_include()}/terraform.tfstate"
    region         = local.aws_region
    encrypt        = true
    dynamodb_table = "${local.app_name}-${local.environment}-${local.aws_region}-tf-lock"
    s3_bucket_tags = {
      "Environment" = local.environment
      "Region"      = local.aws_region
      "Terraform"   = "true"
    }
  }
}
