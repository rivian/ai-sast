variable "tags" {
  type = object({
    ProjectOwner = string
    Customer     = string
    Project      = string
    Environment  = string
    Terraform    = bool
  })
  description = "The set of tags required for the AWS resources."
}

variable "service_name" {
  type        = string
  description = "Name of service"
  default     = "ai-sast-webhook-listener"
}

variable "container_port" {
  type        = number
  description = "Port number of service on container"
  default     = 8080
}

variable "load_balancer_port" {
  type        = number
  description = "Port number of load balancer"
  default     = 443
}

variable "vpc" {
  type        = string
  description = "VPC ID where resources will be deployed"
}

variable "subnet_a" {
  type        = string
  description = "First subnet ID for high availability"
}

variable "subnet_b" {
  type        = string
  description = "Second subnet ID for high availability"
}

variable "subnet_c" {
  type        = string
  description = "Third subnet ID for API Gateway"
}

variable "certificate_arn" {
  type        = string
  description = "ARN of ACM certificate for HTTPS"
}

variable "aws_id" {
  type        = string
  description = "AWS account ID"
}

variable "aws_region" {
  type        = string
  description = "AWS region"
  default     = "us-east-1"
}

variable "dns_name" {
  type        = string
  description = "DNS name for the webhook service (e.g., ai-sast-webhook.yourdomain.com)"
}

variable "zone_id" {
  type        = string
  description = "Route53 hosted zone ID for DNS record"
}

variable "sns_topic_arn" {
  type        = string
  description = "SNS topic ARN for notifications (optional)"
  default     = ""
}

variable "databricks_host" {
  type        = string
  description = "Databricks workspace URL (e.g., https://your-workspace.cloud.databricks.com)"
  default     = ""
}

variable "databricks_http_path" {
  type        = string
  description = "Databricks SQL warehouse HTTP path"
  default     = ""
}

variable "databricks_catalog" {
  type        = string
  description = "Databricks Unity Catalog name"
  default     = ""
}

variable "databricks_schema" {
  type        = string
  description = "Databricks schema name"
  default     = ""
}

variable "databricks_table" {
  type        = string
  description = "Databricks table name for storing feedback"
  default     = ""
}

