#!/usr/bin/env python3
"""
Vertex AI API Client Script

This script demonstrates how to interact with Google Cloud Vertex AI API
for various tasks including text generation, chat, and embeddings.
"""

import json
import os
from typing import List, Dict, Optional
from google.cloud import aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
from vertexai.language_models import TextEmbeddingModel, TextGenerationModel


class VertexAIClient:
    """
    A client for interacting with Google Cloud Vertex AI API
    """
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """
        Initialize the Vertex AI client
        
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
        
        vertexai.init(project=project_id, location=location)
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

    def generate_text(self, prompt: str, model_name: str = "text-bison@001", 
                     max_output_tokens: int = 1024, temperature: float = 0.2) -> str:
        """
        Generate text using Vertex AI Text Generation model
        
        Args:
            prompt: Input text prompt
            model_name: Model to use for generation
            max_output_tokens: Maximum tokens in response
            temperature: Creativity level (0.0-1.0)
            
        Returns:
            Generated text response
        """
        try:
            model = TextGenerationModel.from_pretrained(model_name)
            
            response = model.predict(
                prompt=prompt,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                top_k=40,
                top_p=0.8,
            )
            
            return response.text
            
        except Exception as e:
            print(f"❌ Error with PaLM: {str(e)}")
            raise

    def generate_with_gemini(self, prompt: str, model_name: str = "gemini-2.5-pro") -> str:
        """
        Generate text using Gemini model
        
        Args:
            prompt: Input text prompt
            model_name: Gemini model to use
            
        Returns:
            Generated text response
        """
        try:
            model = GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            # Handle multi-part responses by joining them.
            if response.candidates and response.candidates[0].content.parts:
                return "".join(part.text for part in response.candidates[0].content.parts)
            
            # Fallback for simple responses (though the above should cover it)
            return response.text
            
        except Exception as e:
            print(f"❌ Error with Gemini: {str(e)}")
            raise

    def start_chat_session(self, model_name: str = "gemini-2.5-pro") -> Optional[ChatSession]:
        """
        Start a chat session with Gemini
        
        Args:
            model_name: Gemini model to use
            
        Returns:
            Chat session object
        """
        try:
            model = GenerativeModel(model_name)
            chat_session = model.start_chat()
            
            print(f"✅ Chat session started with {model_name}")
            return chat_session
            
        except Exception as e:
            print(f"❌ Error starting chat session: {e}")
            return None

    def send_chat_message(self, chat_session: ChatSession, message: str) -> str:
        """
        Send a message in a chat session
        
        Args:
            chat_session: Active chat session
            message: Message to send
            
        Returns:
            Response from the model
        """
        try:
            response = chat_session.send_message(message)
            return response.text
            
        except Exception as e:
            print(f"❌ Error sending chat message: {e}")
            return ""

    def get_embeddings(self, texts: List[str], model_name: str = "textembedding-gecko@001") -> List[List[float]]:
        """
        Generate embeddings for given texts
        
        Args:
            texts: List of texts to embed
            model_name: Embedding model to use
            
        Returns:
            List of embedding vectors
        """
        try:
            model = TextEmbeddingModel.from_pretrained(model_name)
            
            embeddings = model.get_embeddings(texts)  # type: ignore[arg-type]
            
            return [embedding.values for embedding in embeddings]
            
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