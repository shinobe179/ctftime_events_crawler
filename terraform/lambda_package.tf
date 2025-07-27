# Create a directory for Lambda package
resource "null_resource" "lambda_package" {
  # This will be triggered whenever the source code changes
  triggers = {
    source_code_hash = filebase64sha256("${path.module}/../lambda_function.py")
  }

  # Create package directory and install dependencies
  provisioner "local-exec" {
    command = <<EOF
      # Cleanup any existing files
      rm -rf ${path.module}/package ${path.module}/lambda_package.zip
      
      # Create temporary directory
      mkdir -p ${path.module}/package
      
      # Copy source code
      cp ${path.module}/../lambda_function.py ${path.module}/package/
      
      # Install dependencies
      pip install --target ${path.module}/package requests boto3
      
      # Remove unnecessary files
      find ${path.module}/package -type d -name "__pycache__" -exec rm -rf {} +
      find ${path.module}/package -type f -name "*.pyc" -delete
      find ${path.module}/package -type f -name "*.pyo" -delete
      find ${path.module}/package -type f -name "*.dist-info" -delete
    EOF
  }
}

# Create zip file from the package
data "archive_file" "lambda_package" {
  depends_on  = [null_resource.lambda_package]
  type        = "zip"
  source_dir  = "${path.module}/package"
  output_path = "${path.module}/lambda_package.zip"

  excludes = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.dist-info"
  ]
}

# Cleanup package directory after zip creation
resource "null_resource" "cleanup" {
  depends_on = [data.archive_file.lambda_package]

  # This will be triggered whenever the package is updated
  triggers = {
    lambda_package = data.archive_file.lambda_package.output_base64sha256
  }

  provisioner "local-exec" {
    command = "rm -rf ${path.module}/package"
  }
}