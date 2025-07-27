# Lambda Function outputs
output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.ctftime_events.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.ctftime_events.function_name
}

# IAM Role outputs
output "lambda_role_arn" {
  description = "ARN of the Lambda IAM role"
  value       = aws_iam_role.lambda_role.arn
}

output "lambda_role_name" {
  description = "Name of the Lambda IAM role"
  value       = aws_iam_role.lambda_role.name
}

# CloudWatch Logs outputs
output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch Logs group"
  value       = aws_cloudwatch_log_group.lambda.arn
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch Logs group"
  value       = aws_cloudwatch_log_group.lambda.name
}

# Secrets Manager outputs
output "secrets_manager_arn" {
  description = "ARN of the Secrets Manager secret"
  value       = aws_secretsmanager_secret.slack_credentials.arn
}

# EventBridge outputs
output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.schedule.arn
}

# KMS outputs
output "kms_key_arn" {
  description = "ARN of the KMS key"
  value       = aws_kms_key.secrets.arn
}

# Lambda package info
output "lambda_package_hash" {
  description = "Base64-encoded SHA256 hash of the Lambda package"
  value       = data.archive_file.lambda_package.output_base64sha256
}