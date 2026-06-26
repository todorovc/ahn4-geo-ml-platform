terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "s3_data_lake" {
  source      = "../../modules/s3_data_lake"
  bucket_name = var.data_bucket_name
}

module "ecr" {
  source = "../../modules/ecr"
  repositories = ["ahn4-ingest","ahn4-processing","ahn4-training","ahn4-inference"]
}
