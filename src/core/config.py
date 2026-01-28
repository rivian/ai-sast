"""
Configuration file for Vertex AI API client
"""

import os

# GOOGLE_CLOUD_PROJECT or GOOGLE_PROJECT_ID: Your Google Cloud project ID
# Example: "my-company-production" or "security-scanning-project"
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_PROJECT_ID", "your-project-id")

# VERTEX_AI_LOCATION or GOOGLE_LOCATION: Google Cloud region for Vertex AI
# Example: "us-central1", "us-east1", "europe-west1", "asia-southeast1"
LOCATION = os.getenv("VERTEX_AI_LOCATION") or os.getenv("GOOGLE_LOCATION", "us-central1")

# GEMINI_MODEL: Gemini model to use for security analysis
# Example: "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-2.5-pro"
# Default: "gemini-2.0-flash-exp" (fast, low-cost, good for most scans)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

DEFAULT_TEXT_MODEL = "text-bison@001"
DEFAULT_GEMINI_MODEL = GEMINI_MODEL  # For backward compatibility
DEFAULT_EMBEDDING_MODEL = "textembedding-gecko@001"

DEFAULT_MAX_OUTPUT_TOKENS = 1024
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_K = 40
DEFAULT_TOP_P = 0.8

# GOOGLE_APPLICATION_CREDENTIALS: Path to service account key file (optional)
# Example: "/path/to/service-account-key.json" or "~/.gcp/my-project-key.json"
SERVICE_ACCOUNT_KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)

# GOOGLE_TOKEN: Google Cloud authentication token - service account JSON or access token (optional)
# Example: Raw JSON string or base64-encoded service account key
GOOGLE_TOKEN = os.getenv("GOOGLE_TOKEN", None)

AVAILABLE_REGIONS = [
    "us-central1",
    "us-east1",
    "us-west1",
    "us-west4",
    "europe-west1",
    "europe-west4",
    "asia-east1",
    "asia-northeast1",
    "asia-southeast1"
]

MODEL_AVAILABILITY = {
    "text-bison@001": ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"],
    "gemini-2.0-flash-exp": ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"],
    "textembedding-gecko@001": ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"]
}

def validate_config():
    """
    Validate the configuration settings
    """
    errors = []
    
    if PROJECT_ID == "your-project-id":
        errors.append("Please set your Google Cloud Project ID in the GOOGLE_CLOUD_PROJECT or GOOGLE_PROJECT_ID environment variable")
    
    if LOCATION not in AVAILABLE_REGIONS:
        errors.append(f"Invalid location: {LOCATION}. Available regions: {', '.join(AVAILABLE_REGIONS)}")
    
    if SERVICE_ACCOUNT_KEY_PATH and not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
        errors.append(f"Service account key file not found: {SERVICE_ACCOUNT_KEY_PATH}")
    
    return errors

def get_model_config(model_type: str = "text"):
    """
    Get model configuration for different types
    
    Args:
        model_type: Type of model ("text", "gemini", "embedding")
    
    Returns:
        Dictionary with model configuration
    """
    configs = {
        "text": {
            "model_name": DEFAULT_TEXT_MODEL,
            "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
            "temperature": DEFAULT_TEMPERATURE,
            "top_k": DEFAULT_TOP_K,
            "top_p": DEFAULT_TOP_P
        },
        "gemini": {
            "model_name": DEFAULT_GEMINI_MODEL,
            "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
            "temperature": DEFAULT_TEMPERATURE,
            "top_k": DEFAULT_TOP_K,
            "top_p": DEFAULT_TOP_P
        },
        "embedding": {
            "model_name": DEFAULT_EMBEDDING_MODEL
        }
    }
    
    return configs.get(model_type, configs["text"])

