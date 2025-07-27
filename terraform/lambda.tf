# CloudWatch Logs group
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.project_prefix}-function"
  retention_in_days = 14
}

# Lambda function
resource "aws_lambda_function" "ctftime_events" {
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  function_name    = "${var.project_prefix}-function"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = var.lambda_runtime
  memory_size     = var.lambda_memory_size
  timeout         = var.lambda_timeout

  environment {
    variables = {
      SLACK_CREDENTIALS_SECRET_ARN = aws_secretsmanager_secret.slack_credentials.arn
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy.lambda_cloudwatch_policy,
    aws_iam_role_policy.lambda_secrets_policy,
    null_resource.lambda_package
  ]
}

# Lambda permission for EventBridge
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ctftime_events.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}