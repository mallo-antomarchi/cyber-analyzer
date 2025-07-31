# Azure Container Instances (ACI) Deployment

This is a test deployment to diagnose MCP server timeout issues with Azure Container Apps.

## Quick Test Deployment

```bash
# Navigate to ACI directory
cd terraform/environments/azure-aci

# Initialize Terraform
terraform init

# Create ACI workspace
terraform workspace new azure-aci
terraform workspace select azure-aci

# Load environment variables
export $(cat ../../../.env | xargs)

# Plan deployment
terraform plan \
  -var="openai_api_key=$OPENAI_API_KEY" \
  -var="semgrep_app_token=$SEMGREP_APP_TOKEN"

# Deploy
terraform apply \
  -var="openai_api_key=$OPENAI_API_KEY" \
  -var="semgrep_app_token=$SEMGREP_APP_TOKEN"

# Get URL
terraform output app_url
```

## Key Differences from Container Apps

- **No serverless scaling**: Always-on container instance
- **Direct container runtime**: Standard Docker process management
- **Public IP**: Direct access without load balancer complexity
- **Simplified networking**: No ingress controllers

## Testing MCP Server

1. Get the URL: `terraform output app_url`
2. Test the application works: `{url}/health`
3. Test MCP server: Submit a Python file for analysis
4. Check logs: `az container logs --name cyber-analyzer-aci --resource-group cyber-analyzer-rg`

## Clean Up

```bash
terraform destroy \
  -var="openai_api_key=$OPENAI_API_KEY" \
  -var="semgrep_app_token=$SEMGREP_APP_TOKEN"
```