terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

# Configure Azure Provider
provider "azurerm" {
  features {}
}

# Use existing resource group
data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}

# Use existing Azure Container Registry from Container Apps deployment
data "azurerm_container_registry" "acr" {
  name                = replace("${var.project_name}acr", "-", "")
  resource_group_name = data.azurerm_resource_group.main.name
}

# Configure Docker provider to use existing ACR
provider "docker" {
  registry_auth {
    address  = data.azurerm_container_registry.acr.login_server
    username = data.azurerm_container_registry.acr.admin_username
    password = data.azurerm_container_registry.acr.admin_password
  }
}

# Build and push Docker image (reuse existing image if available)
resource "docker_image" "app" {
  name = "${data.azurerm_container_registry.acr.login_server}/${var.project_name}:${var.docker_image_tag}-aci"
  
  build {
    context    = "${path.module}/../../../"
    dockerfile = "Dockerfile"
    platform   = "linux/amd64"
    no_cache   = true
  }
}

resource "docker_registry_image" "app" {
  name = docker_image.app.name
  
  depends_on = [docker_image.app]
}

# Create Azure Container Instance
resource "azurerm_container_group" "main" {
  name                = "${var.project_name}-aci"
  location            = data.azurerm_resource_group.main.location
  resource_group_name = data.azurerm_resource_group.main.name
  ip_address_type     = "Public"
  dns_name_label      = "${var.project_name}-aci"
  os_type             = "Linux"

  container {
    name   = "main"
    image  = docker_registry_image.app.name
    cpu    = "1.0"
    memory = "2.0"

    ports {
      port     = 8000
      protocol = "TCP"
    }

    environment_variables = {
      ENVIRONMENT        = "production"
      PYTHONUNBUFFERED  = "1"
    }

    secure_environment_variables = {
      OPENAI_API_KEY    = var.openai_api_key
      SEMGREP_APP_TOKEN = var.semgrep_app_token
    }
  }

  image_registry_credential {
    server   = data.azurerm_container_registry.acr.login_server
    username = data.azurerm_container_registry.acr.admin_username
    password = data.azurerm_container_registry.acr.admin_password
  }

  tags = {
    environment = terraform.workspace
    project     = var.project_name
  }
}

# Outputs
output "app_url" {
  value       = "http://${azurerm_container_group.main.fqdn}:8000"
  description = "URL of the deployed application"
}

output "app_ip" {
  value       = azurerm_container_group.main.ip_address
  description = "IP address of the container instance"
}

output "resource_group" {
  value       = data.azurerm_resource_group.main.name
  description = "Resource group name"
}