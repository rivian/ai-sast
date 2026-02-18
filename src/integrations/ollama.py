#!/usr/bin/env python3
"""
Ollama API Client for Local LLM Inference

This module provides an interface to Ollama for running local open-source models
as an alternative to commercial cloud-based LLM services.
"""

import json
import requests
from typing import Optional


class OllamaClient:
    """
    A client for interacting with Ollama's local LLM API
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5-coder:14b"):
        """
        Initialize the Ollama client
        
        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            model: Model name to use (default: qwen2.5-coder:14b)
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_url = f"{self.base_url}/api/generate"
        
        # Test connection
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            print(f"✅ Ollama client initialized at {base_url}")
            print(f"🤖 Using model: {model}")
            
            # Check if model is available
            available_models = response.json().get('models', [])
            model_names = [m['name'] for m in available_models]
            if model not in model_names:
                print(f"⚠️  Warning: Model '{model}' not found locally")
                print(f"   Available models: {', '.join(model_names)}")
                print(f"   Run: ollama pull {model}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to Ollama at {base_url}")
            print(f"   Error: {str(e)}")
            print(f"   Make sure Ollama is running: https://ollama.com/")
            raise

    def generate_with_ollama(self, prompt: str, temperature: float = 0.2, max_tokens: Optional[int] = None) -> str:
        """
        Generate text using Ollama model (Ollama-specific API for scanning).

        Args:
            prompt: Input text prompt
            temperature: Creativity level (0.0-1.0, default: 0.2 for security analysis)
            max_tokens: Maximum tokens in response (optional)

        Returns:
            Generated text response
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=300  # 5 minutes for large models
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
            
        except requests.exceptions.Timeout:
            print(f"❌ Request timed out. Model '{self.model}' may be too slow or not responding.")
            raise
        except requests.exceptions.RequestException as e:
            print(f"❌ Error calling Ollama API: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Ollama response: {str(e)}")
            raise

    def list_models(self) -> list:
        """
        List all available models in Ollama
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get('models', [])
            return [m['name'] for m in models]
        except Exception as e:
            print(f"❌ Error listing models: {str(e)}")
            return []

    def pull_model(self, model_name: str) -> bool:
        """
        Pull/download a model from Ollama registry
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"📥 Pulling model '{model_name}' from Ollama registry...")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=600  # 10 minutes for large downloads
            )
            response.raise_for_status()
            print(f"✅ Model '{model_name}' pulled successfully")
            return True
        except Exception as e:
            print(f"❌ Error pulling model: {str(e)}")
            return False

    def is_available(self) -> bool:
        """
        Check if Ollama service is available
        
        Returns:
            True if Ollama is running and accessible
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False


# Recommended models for security scanning
RECOMMENDED_MODELS = {
    "qwen2.5-coder:14b": "Recommended - Best balance (14B params, ~8GB RAM)",
    "qwen2.5-coder:7b": "Fast, code-focused model (7B params, ~4GB RAM)",
    "qwen2.5-coder:32b": "Most capable Qwen (32B params, ~20GB RAM)",
    "deepseek-coder:6.7b": "Fast, code-focused model (6.7B params, ~4GB RAM)",
    "deepseek-coder:33b": "Most capable DeepSeek (33B params, ~20GB RAM)",
    "codellama:13b": "Meta's code model (13B params, ~8GB RAM)",
    "codellama:34b": "Larger Meta code model (34B params, ~20GB RAM)",
    "llama3.1:8b": "Latest Llama, general purpose (8B params, ~5GB RAM)",
    "llama3.1:70b": "Most capable Llama (70B params, ~40GB RAM)",
    "mixtral:8x7b": "Mixture of Experts (47B params, ~26GB RAM)",
    "phi3:medium": "Small but powerful (14B params, ~8GB RAM)",
}


def print_recommended_models():
    """Print recommended models for security scanning"""
    print("\n📚 Recommended Models for Security Scanning:")
    print("=" * 70)
    for model, description in RECOMMENDED_MODELS.items():
        print(f"  • {model:<25} - {description}")
    print("=" * 70)
print("\nTo install a model:")
print("  ollama pull <model-name>")
print("\nExample:")
print("  ollama pull qwen2.5-coder:14b")
print()
