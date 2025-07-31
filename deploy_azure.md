# Azure Deployment Guide

This guide will deploy the Cybersecurity Analyzer to Azure Container Apps using Terraform. The deployment will automatically build your Docker image, push it to Azure Container Registry, and deploy it as a serverless container application.

## Prerequisites

✅ Complete the [Azure Setup Guide](./setup_azure.md) first
✅ Terraform CLI installed (covered in previous course modules)
✅ Docker running locally
✅ `.env` file in project root with your API keys

## Quick Terraform Check

If you missed the Terraform installation from previous modules:

```bash
# Check if Terraform is installed
terraform version

# If not installed:
# Mac: brew install terraform
# Windows: Download from https://terraform.io/downloads
```

---

## Step 1: Set Environment Variables

Terraform will read your API keys from environment variables. We'll load them from your `.env` file:

### Mac/Linux:
```bash
# Load environment variables from .env file
export $(cat .env | xargs)

# Verify they're loaded
echo "OpenAI key loaded: ${OPENAI_API_KEY:0:8}..."
echo "Semgrep token loaded: ${SEMGREP_APP_TOKEN:0:8}..."
```

### Windows (PowerShell):
```powershell
# Load environment variables from .env file
Get-Content .env | ForEach-Object {
    $name, $value = $_.split('=', 2)
    Set-Item -Path "env:$name" -Value $value
}

# Verify they're loaded
Write-Host "OpenAI key loaded: $($env:OPENAI_API_KEY.Substring(0,8))..."
Write-Host "Semgrep token loaded: $($env:SEMGREP_APP_TOKEN.Substring(0,8))..."
```

---

## Step 2: Initialize Terraform

Navigate to the Azure Terraform configuration:

```bash
cd terraform/environments/azure
```

Initialize Terraform and create an Azure workspace:

```bash
# Initialize Terraform
terraform init

# Create and select Azure workspace
terraform workspace new azure
terraform workspace select azure

# Verify you're in the right workspace
terraform workspace show
```

You should see output showing the Azure provider being downloaded and the workspace set to `azure`.

---

## Step 3: Login to Azure and Register Providers

Ensure you're logged into Azure CLI and register the required resource providers:

```bash
# Login to Azure (will open browser)
az login

# Verify you're logged in and see your subscription
az account show --output table
```

Make sure the subscription shown matches what you set up in the Azure setup guide.

Now register the required Azure resource providers (one-time setup):

```bash
# Register Container Apps provider
az provider register --namespace Microsoft.App

# Register Log Analytics provider
az provider register --namespace Microsoft.OperationalInsights

# Check registration status (should show "Registered")
az provider show --namespace Microsoft.App --query "registrationState" -o tsv
az provider show --namespace Microsoft.OperationalInsights --query "registrationState" -o tsv
```

⏳ **Wait for registration**: If either shows "Registering", wait 1-2 minutes and check again. Both must show "Registered" before proceeding.

---

## Step 4: Deploy to Azure

Now let's deploy everything with a single command:

```bash
# Plan the deployment (see what will be created)
terraform plan \
  -var="openai_api_key=$OPENAI_API_KEY" \
  -var="semgrep_app_token=$SEMGREP_APP_TOKEN"
```

Review the plan output. You should see:
- ✅ Azure Container Registry (ACR)
- ✅ Log Analytics Workspace
- ✅ Container App Environment
- ✅ Container App
- ✅ Docker image build and push

If everything looks good, apply the changes:

```bash
# Deploy everything
terraform apply \
  -var="openai_api_key=$OPENAI_API_KEY" \
  -var="semgrep_app_token=$SEMGREP_APP_TOKEN"
```

Type `yes` when prompted. This will take 5-10 minutes as it:
1. Creates the Azure Container Registry
2. Builds your Docker image locally
3. Pushes the image to ACR
4. Creates the Container App infrastructure
5. Deploys your application

**Important**: If you make code changes and redeploy, Terraform may not detect the changes automatically. If your updates don't appear, force a rebuild:

```bash
# Force rebuild of Docker image when code changes
terraform taint docker_image.app
terraform taint docker_registry_image.app

# Then redeploy
terraform apply \
  -var="openai_api_key=$OPENAI_API_KEY" \
  -var="semgrep_app_token=$SEMGREP_APP_TOKEN"
```

---

## Step 5: Get Your Application URL

Once deployment completes, Terraform will output your application URL:

```bash
# Get the application URL
terraform output app_url
```

You should see something like:
```
"https://cyber-analyzer.nicehill-12345678.eastus.azurecontainerapps.io"
```

🎉 **Your application is now live!** Visit the URL to test it.

---

## Step 6: Verify Deployment

### Test the Application
1. Open the URL from Step 5 in your browser
2. You should see the Cybersecurity Analyzer interface
3. Try uploading a Python file to verify it works end-to-end

### Check Azure Resources
In the Azure Portal (https://portal.azure.com):
1. Navigate to your resource group: `cyber-analyzer-rg`
2. You should see:
   - Container registry (cyberanalyzeracr)
   - Log Analytics workspace (cyber-analyzer-logs)
   - Container App Environment (cyber-analyzer-env)
   - Container App (cyber-analyzer)

### Monitor Logs
```bash
# View application logs
az containerapp logs show \
  --name cyber-analyzer \
  --resource-group cyber-analyzer-rg \
  --follow
```

---

## Understanding What Was Created

### Cost Breakdown (all very low cost/free):
- **Container Registry**: Basic tier (~$5/month, includes 10GB storage)
- **Container App**: Pay-per-use, scales to zero (~$0 when not in use)
- **Log Analytics**: 5GB free per month
- **Total estimated cost**: < $5/month for learning

### Architecture:
```
Internet → Container App → Your Docker Image
              ↓
          Log Analytics (monitoring)
              ↓
      Container Registry (image storage)
```

### Scaling:
- **Min replicas**: 0 (scales to zero when not used = $0)
- **Max replicas**: 1 (keeps costs minimal)
- **Auto-scaling**: Based on HTTP requests

---

## Managing Your Deployment

### View Infrastructure State
```bash
# See what's deployed
terraform show

# List all resources
terraform state list
```

### Update the Application
After making code changes:

```bash
# Rebuild and redeploy
terraform apply \
  -var="openai_api_key=$OPENAI_API_KEY" \
  -var="semgrep_app_token=$SEMGREP_APP_TOKEN" \
  -var="docker_image_tag=v2"
```

### Clean Up (Important for Cost Management!)
When you're done with the lab:

```bash
# Destroy all resources
terraform destroy \
  -var="openai_api_key=$OPENAI_API_KEY" \
  -var="semgrep_app_token=$SEMGREP_APP_TOKEN"
```

Type `yes` to confirm. This removes everything and stops all charges.

---

## Troubleshooting

### "Failed to build Docker image"
- Make sure Docker is running: `docker ps`
- Ensure you're in the project root directory
- Check Dockerfile exists and is valid

### "MissingSubscriptionRegistration" error
This means Azure resource providers aren't registered:
```bash
# Register the required providers
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights

# Wait for registration to complete
az provider show --namespace Microsoft.App --query "registrationState" -o tsv
```
Re-run `terraform apply` once both show "Registered".

### "Login server could not be found"
- Run `az login` again
- Verify resource group exists: `az group show --name cyber-analyzer-rg`

### "Environment variables not set"
- Re-run the environment variable commands from Step 1
- Check `.env` file exists and has correct format

### "Terraform workspace issues"
```bash
# List workspaces
terraform workspace list

# Switch back to azure
terraform workspace select azure
```

### Application not accessible
- Check the URL from `terraform output app_url`
- Wait 2-3 minutes after deployment completes
- Check logs: `az containerapp logs show --name cyber-analyzer --resource-group cyber-analyzer-rg`

---

## Next Steps

🎉 **Congratulations!** You've successfully deployed a containerized application to Azure using Infrastructure as Code.

**What you've learned:**
- Azure Container Apps for serverless containers
- Azure Container Registry for image storage
- Terraform workspaces for environment management
- Environment variable management in cloud deployments
- Cost-effective cloud architecture patterns

**Coming up next:** We'll deploy the same application to Google Cloud Platform using Cloud Run and compare the two approaches!