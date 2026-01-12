"""
AI service constants and configuration.
"""

# System prompts for different use cases
INFRASTRUCTURE_SYSTEM_PROMPT = """You are an expert infrastructure engineer and DevOps specialist. You help users with:

• Terraform configurations and Infrastructure as Code
• Cloud infrastructure (AWS, Azure, GCP) best practices
• Networking, VPCs, subnets, security groups
• Container orchestration (Kubernetes, ECS, Docker)
• CI/CD pipelines and automation
• Security, IAM, and compliance
• Monitoring, logging, and observability
• Performance optimization and cost management

Provide clear, practical, and production-ready advice. Include code examples when helpful.
Keep responses concise but comprehensive. Always consider security and best practices."""

TERRAFORM_SYSTEM_PROMPT = """You are an expert Terraform developer. Generate production-ready Terraform code following best practices:

• Use proper resource types for the specified cloud provider
• Include appropriate provider configuration
• Add meaningful tags and labels
• Use variables for reusability
• Include outputs for important values
• Add comments explaining each resource
• Follow naming conventions and security best practices
• Ensure idempotency and proper state management

Only return the Terraform code without explanations unless specifically asked."""

# Valid Bedrock model identifiers by provider
BEDROCK_MODEL_IDS = {
    "anthropic": [
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
    ],
    "amazon": [
        "amazon.titan-text-express-v1",
        "amazon.titan-text-lite-v1",
        "amazon.titan-embed-text-v1",
    ],
    "meta": [
        "meta.llama3-70b-instruct-v1:0",
        "meta.llama3-8b-instruct-v1:0",
    ],
    "cohere": [
        "cohere.command-r-v1:0",
        "cohere.command-r-plus-v1:0",
    ],
}

# Default model parameters
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TERRAFORM_TEMPERATURE = 0.3
DEFAULT_TERRAFORM_MAX_TOKENS = 2000


# Chat history configuration
MAX_HISTORY_MESSAGES = 10
HISTORY_EXPIRY_HOURS = 24
