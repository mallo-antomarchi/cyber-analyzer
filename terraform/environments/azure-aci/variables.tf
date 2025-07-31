variable "resource_group_name" {
  description = "Name of the Azure resource group"
  type        = string
  default     = "cyber-analyzer-rg"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "cyber-analyzer"
}

variable "docker_image_tag" {
  description = "Tag for the Docker image"
  type        = string
  default     = "latest"
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "semgrep_app_token" {
  description = "Semgrep app token"
  type        = string
  sensitive   = true
}