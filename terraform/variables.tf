variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "ap-northeast-1"
}

variable "environment" {
  description = "Environment name (e.g. dev, prod)"
  type        = string
  default     = "dev"
}

variable "project_prefix" {
  description = "Prefix to be used in resource names"
  type        = string
  default     = "ctftime-events"
}

# Lambda Function Configuration
variable "lambda_memory_size" {
  description = "Amount of memory in MB for the Lambda Function"
  type        = number
  default     = 256
}

variable "lambda_timeout" {
  description = "Timeout in seconds for the Lambda Function"
  type        = number
  default     = 60
}

variable "lambda_runtime" {
  description = "Runtime for the Lambda Function"
  type        = string
  default     = "python3.12"
}

# Schedule Configuration
variable "schedule_expression" {
  description = "CloudWatch Events schedule expression"
  type        = string
  default     = "cron(0 0 ? * MON *)"  # Every Monday at 09:00 JST (00:00 UTC)
}

# Slack Configuration
variable "slack_oauth_token" {
  description = "Slack OAuth token for API access"
  type        = string
  sensitive   = true
}

variable "target_channel_id" {
  description = "Slack channel ID to post messages"
  type        = string
  sensitive   = true
}

# KMS Configuration
variable "kms_deletion_window_in_days" {
  description = "Duration in days before the KMS key is deleted"
  type        = number
  default     = 7
}

variable "enable_key_rotation" {
  description = "Specifies whether key rotation is enabled"
  type        = bool
  default     = true
}