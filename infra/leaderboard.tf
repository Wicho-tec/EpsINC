data "archive_file" "leaderboard" {
  type        = "zip"
  source_file = "${path.module}/../serverless/leaderboard_function.py"
  output_path = "${path.module}/.terraform/leaderboard.zip"
}

resource "aws_dynamodb_table" "leaderboard" {
  name         = "epsinc-leaderboard"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "board"
  range_key    = "player_id"
  attribute {
    name = "board"
    type = "S"
  }
  attribute {
    name = "player_id"
    type = "S"
  }
}

resource "aws_iam_role" "leaderboard" {
  name = "epsinc-leaderboard"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_cloudwatch_log_group" "leaderboard" {
  name              = "/aws/lambda/epsinc-leaderboard"
  retention_in_days = 1
}

resource "aws_iam_role_policy" "leaderboard" {
  role = aws_iam_role.leaderboard.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["dynamodb:Query", "dynamodb:PutItem"], Resource = aws_dynamodb_table.leaderboard.arn },
      { Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents"], Resource = "${aws_cloudwatch_log_group.leaderboard.arn}:*" }
    ]
  })
}

resource "aws_lambda_function" "leaderboard" {
  function_name                  = "epsinc-leaderboard"
  role                           = aws_iam_role.leaderboard.arn
  handler                        = "leaderboard_function.handler"
  runtime                        = "python3.12"
  filename                       = data.archive_file.leaderboard.output_path
  source_code_hash               = data.archive_file.leaderboard.output_base64sha256
  memory_size                    = 256
  timeout                        = 5
  reserved_concurrent_executions = 2
  environment {
    variables = { TABLE_NAME = aws_dynamodb_table.leaderboard.name }
  }
  depends_on = [aws_iam_role_policy.leaderboard]
}

resource "aws_lambda_function_url" "leaderboard" {
  function_name      = aws_lambda_function.leaderboard.function_name
  authorization_type = "NONE"
}

resource "aws_lambda_permission" "leaderboard_url" {
  statement_id           = "PublicDemoURL"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.leaderboard.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "leaderboard_invoke" {
  statement_id             = "InvokeOnlyViaDemoURL"
  action                   = "lambda:InvokeFunction"
  function_name            = aws_lambda_function.leaderboard.function_name
  principal                = "*"
  invoked_via_function_url = true
}

output "leaderboard_url" {
  value = aws_lambda_function_url.leaderboard.function_url
}
