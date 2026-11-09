terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    archive = {
      source = "hashicorp/archive"
    }

    random = {
      source = "hashicorp/random"
    }

  }
}

variable "region" {
  default = "us-east-1"
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project = "cloudscale"
    }
  }
}