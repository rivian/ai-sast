terraform {
  backend "s3" {
    # Configure with your S3 bucket for state management
    # bucket = "your-terraform-state-bucket"
    # key    = "ai-sast/webhook/terraform.tfstate"
    # region = "us-east-1"
  }
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  required_version = ">= 1.0"
}

