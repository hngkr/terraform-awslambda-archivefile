terraform-awslambda-archivefile
===============================

This module builds Python Lambda function deployment packages from a `requiements.txt` file, possibly including
packages with binary dependencies using the excellent [lambci](https://hub.docker.com/r/lambci/lambda/) docker images.

Runtime dependencies: Python 3 + Docker

```
module "example-zip" {
  source            = "app.terraform.io/glue-consulting/archivefile/awslambda"
  version           = "1.0.0"
  name              = "example"
  runtime           = "python3.8"
  project_path      = "${path.module}/lambda/example"
  output_path       = "${path.module}/builds"
  requirements_file = "${path.module}/lambda/requirements.txt"
}
```

This is how the module are to be used in `resource "aws_lambda_function"`:

```
locals {
  example_lambda_function_name = "example-${terraform.workspace}"
}

resource "aws_lambda_function" "example" {
  function_name    = local.example_lambda_function_name
  description      = "Example lambda function"

  filename         = module.example-zip.path
  source_code_hash = module.example-zip.sha256

  role             = aws_iam_role.example.arn
  handler          = "lambda.example_handler"
  runtime          = "python3.8"

  depends_on = [ aws_cloudwatch_log_group.example ]
}

resource "aws_cloudwatch_log_group" "example" {
  name = "/aws/lambda/${local.example_lambda_function_name}"
  retention_in_days = 7
}
```
