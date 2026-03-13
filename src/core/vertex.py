#!/usr/bin/env python3
"""
Vertex AI API Client Script

Uses the Google Gen AI SDK (google-genai) with vertexai=True for Gemini and embeddings.
See: https://cloud.google.com/vertex-ai/generative-ai/docs/deprecations/genai-vertexai-sdk
"""

import json
import os
from typing import List, Dict, Optional, Any
from google.cloud import aiplatform
from google.genai import Client
from google.genai import types as genai_types


class VertexAIClient:
    """
    A client for interacting with Google Cloud Vertex AI API
    """
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """
        Initialize the Vertex AI client (Google Gen AI SDK with Vertex AI backend).
        
        Args:
            project_id: Google Cloud Project ID
            location: GCP region (default: us-central1)
        """
        self.project_id = project_id
        self.location = location
        
        google_token = os.getenv("GOOGLE_TOKEN")
        if google_token:
            self._setup_token_authentication(google_token)
            print(f"🔑 Using Google Cloud authentication token from GOOGLE_TOKEN")
        
        self._genai_client = Client(
            vertexai=True,
            project=project_id,
            location=location,
        )
        aiplatform.init(project=project_id, location=location)
        
        print(f"✅ Vertex AI client initialized for project: {project_id}")

    def _setup_token_authentication(self, token: str):
        """
        Set up authentication using a Google Cloud token
        
        Args:
            token: Google Cloud authentication token (service account key JSON or access token)
        """
        import tempfile
        import base64
        import json
        import binascii
        
        try:
            json.loads(token)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(token)
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
                print(f"📝 Created temporary credentials file: {f.name}")
                
        except json.JSONDecodeError:
            try:
                decoded = base64.b64decode(token).decode('utf-8')
                json.loads(decoded)
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(decoded)
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
                    print(f"📝 Created temporary credentials file from base64: {f.name}")
                    
            except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError):
                print(f"🔑 Using token as access token (limited functionality)")
                pass

    def generate_text(self, prompt: str, model_name: str = "gemini-2.5-flash",
                     max_output_tokens: int = 1024, temperature: float = 0.2) -> str:
        """
        Generate text using Gemini via Google Gen AI SDK.
        
        Args:
            prompt: Input text prompt
            model_name: Gemini model to use
            max_output_tokens: Maximum tokens in response
            temperature: Creativity level (0.0-1.0)
            
        Returns:
            Generated text response
        """
        try:
            response = self._genai_client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                ),
            )
            return response.text or ""
        except Exception as e:
            print(f"❌ Error with Gemini: {str(e)}")
            raise

    def generate_with_gemini(self, prompt: str, model_name: str = "gemini-2.5-pro") -> str:
        """
        Generate text using Gemini via Google Gen AI SDK.
        
        Args:
            prompt: Input text prompt
            model_name: Gemini model to use
            
        Returns:
            Generated text response
        """
        try:
            response = self._genai_client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=genai_types.GenerateContentConfig(temperature=0.2),
            )
            if hasattr(response, "text") and response.text is not None:
                return response.text
            if response.candidates and response.candidates[0].content.parts:
                return "".join(
                    getattr(p, "text", "") or ""
                    for p in response.candidates[0].content.parts
                )
            return ""
        except Exception as e:
            print(f"❌ Error with Gemini: {str(e)}")
            raise

    def start_chat_session(self, model_name: str = "gemini-2.5-pro") -> Optional[Any]:
        """
        Start a chat session with Gemini (Google Gen AI SDK).
        
        Args:
            model_name: Gemini model to use
            
        Returns:
            Chat session object (genai chat)
        """
        try:
            chat = self._genai_client.chats.create(model=model_name)
            print(f"✅ Chat session started with {model_name}")
            return chat
        except Exception as e:
            print(f"❌ Error starting chat session: {e}")
            return None

    def send_chat_message(self, chat_session: Any, message: str) -> str:
        """
        Send a message in a chat session.
        
        Args:
            chat_session: Active chat session (from start_chat_session)
            message: Message to send
            
        Returns:
            Response text from the model
        """
        try:
            response = chat_session.send_message(message)
            return getattr(response, "text", "") or ""
        except Exception as e:
            print(f"❌ Error sending chat message: {e}")
            return ""

    def get_embeddings(self, texts: List[str], model_name: str = "text-embedding-004") -> List[List[float]]:
        """
        Generate embeddings for given texts (Google Gen AI SDK).
        
        Args:
            texts: List of texts to embed
            model_name: Embedding model (e.g. text-embedding-004, gemini-embedding-001)
            
        Returns:
            List of embedding vectors
        """
        try:
            result: List[List[float]] = []
            for text in texts:
                response = self._genai_client.models.embed_content(
                    model=model_name,
                    contents=text,
                )
                if response.embeddings:
                    emb = response.embeddings[0]
                    values = getattr(emb, "values", None) or getattr(emb, "embedding", None)
                    if values is not None:
                        result.append(list(values))
                    elif hasattr(emb, "__iter__") and not isinstance(emb, (str, bytes)):
                        result.append(list(emb))
                    else:
                        result.append([])
                else:
                    result.append([])
            return result
        except Exception as e:
            print(f"❌ Error getting embeddings: {e}")
            return []

    def batch_predict(self, instances: List[Dict], model_endpoint: str) -> List[Dict]:
        """
        Perform batch prediction on a deployed model
        
        Args:
            instances: List of input instances
            model_endpoint: Deployed model endpoint
            
        Returns:
            List of predictions
        """
        try:
            endpoint = aiplatform.Endpoint(endpoint_name=model_endpoint)
            
            response = endpoint.predict(instances=instances)
            
            return response.predictions
            
        except Exception as e:
            print(f"❌ Error with batch prediction: {e}")
            return []


def main():
    """
    Main function demonstrating various Vertex AI API calls
    """
    
    # Import configuration - supports both standard and GitLab environment variables
    from .config import PROJECT_ID, LOCATION, validate_config
    
    # Validate configuration
    config_errors = validate_config()
    if config_errors:
        print("❌ Configuration errors:")
        for error in config_errors:
            print(f"   - {error}")
        return
    
    # Initialize client
    client = VertexAIClient(PROJECT_ID, LOCATION)
    
    # Example 1: Simple text generation
    print("\n🔤 Example 1: Text Generation")
    print("-" * 50)
    
    prompt = "Write a short story about a robot learning to paint."
    response = client.generate_text(prompt)
    print(f"Prompt: {prompt}")
    print(f"Response: {response}")
    
    # Example 2: Gemini text generation
    print("\n🤖 Example 2: Gemini Text Generation")
    print("-" * 50)
    
    gemini_prompt = "Explain quantum computing in simple terms."
    gemini_response = client.generate_with_gemini(gemini_prompt)
    print(f"Prompt: {gemini_prompt}")
    print(f"Response: {gemini_response}")
    
    # Example 3: Chat session
    print("\n💬 Example 3: Chat Session")
    print("-" * 50)
    
    chat_session = client.start_chat_session()
    if chat_session:
        # First message
        response1 = client.send_chat_message(chat_session, "Hello! What's your name?")
        print(f"Human: Hello! What's your name?")
        print(f"AI: {response1}")
        
        # Follow-up message
        response2 = client.send_chat_message(chat_session, "Can you help me write a Python function?")
        print(f"Human: Can you help me write a Python function?")
        print(f"AI: {response2}")
    
    # Example 4: Text embeddings
    print("\n🧮 Example 4: Text Embeddings")
    print("-" * 50)
    
    texts = [
        "The cat sat on the mat.",
        "A feline rested on the rug.",
        "The dog ran in the park.",
        "Machine learning is fascinating."
    ]
    
    embeddings = client.get_embeddings(texts)
    print(f"Generated embeddings for {len(texts)} texts:")
    for i, (text, embedding) in enumerate(zip(texts, embeddings)):
        print(f"Text {i+1}: {text}")
        print(f"Embedding dimension: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
        print()


def interactive_chat():
    """
    Interactive chat function for continuous conversation
    """
    # Import configuration - supports both standard and GitLab environment variables
    from .config import PROJECT_ID, LOCATION, validate_config
    
    # Validate configuration
    config_errors = validate_config()
    if config_errors:
        print("❌ Configuration errors:")
        for error in config_errors:
            print(f"   - {error}")
        return
    
    client = VertexAIClient(PROJECT_ID, LOCATION)
    chat_session = client.start_chat_session()
    
    if not chat_session:
        print("❌ Failed to start chat session")
        return
    
    print("\n🤖 Interactive Chat with Vertex AI")
    print("Type 'quit' to exit the chat")
    print("-" * 50)
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye! 👋")
            break
        
        if not user_input:
            continue
        
        response = client.send_chat_message(chat_session, user_input)
        print(f"AI: {response}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        interactive_chat()
    else:
        main() 