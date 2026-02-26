#!/usr/bin/env python3
"""
AWS Bedrock Claude API Client

Integrates with Amazon Bedrock to invoke Anthropic Claude (e.g. Claude Opus)
for security scanning. Uses the Messages API. Use by setting AI_SAST_LLM=bedrock.
"""

import json
import os
from typing import Optional, Any, Dict

import boto3
from botocore.exceptions import ClientError, BotoCoreError


# Default Claude Opus model ID on Bedrock (public; no account-specific ARNs)
DEFAULT_MODEL_ID = "anthropic.claude-opus-4-5-20251101-v1:0"
# Alternative: Claude Opus 4.6 (broader region support)
MODEL_OPUS_4_6 = "anthropic.claude-opus-4-6-v1"


class BedrockClaudeClient:
    """
    Client for invoking Claude models on Amazon Bedrock.

    Uses the Bedrock Runtime InvokeModel API with the Anthropic Messages format.
    Supports Claude Opus and other Claude models available on Bedrock.
    """

    def __init__(
        self,
        region_name: Optional[str] = None,
        model_id: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
    ):
        """
        Initialize the Bedrock Claude client.

        Args:
            region_name: AWS region (e.g. us-east-1). Defaults to AWS_REGION or us-east-1.
            model_id: Bedrock model ID (e.g. anthropic.claude-opus-4-5-20251101-v1:0).
            aws_access_key_id: Optional explicit credentials (otherwise uses env/default).
            aws_secret_access_key: Optional explicit credentials.
            aws_session_token: Optional session token (e.g. for assumed role).
        """
        self.region_name = (
            region_name
            or os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "us-east-1"
        )
        self.model_id = model_id or os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)

        client_kwargs: Dict[str, Any] = {
            "service_name": "bedrock-runtime",
            "region_name": self.region_name,
        }
        if aws_access_key_id and aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = aws_access_key_id
            client_kwargs["aws_secret_access_key"] = aws_secret_access_key
            if aws_session_token:
                client_kwargs["aws_session_token"] = aws_session_token

        self._client = boto3.client(**client_kwargs)
        print(f"✅ Bedrock Claude client initialized (region: {self.region_name}, model: {self.model_id})")

    def _invoke_messages(
        self,
        prompt: str,
        model_id: str,
        *,
        max_tokens: int = 8192,
        temperature: float = 0.2,
    ) -> str:
        """
        Invoke Claude using the Messages API.

        Args:
            prompt: User message text.
            model_id: Bedrock model ID (e.g. anthropic.claude-opus-4-5-20251101-v1:0).
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0.0–1.0).

        Returns:
            Generated text from the model.

        Raises:
            ClientError: On Bedrock API errors (e.g. model not enabled, throttling).
        """
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ],
        }
        payload = json.dumps(body)

        response = self._client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=payload,
        )

        response_body = json.loads(response["body"].read())
        content_blocks = response_body.get("content", [])
        if not content_blocks:
            return ""
        first = content_blocks[0]
        if first.get("type") == "text":
            return first.get("text", "")
        return ""

    def generate_with_bedrock(self, prompt: str, model_name: Optional[str] = None) -> str:
        """
        Generate text using Claude on Bedrock (Bedrock-specific API for scanning).

        Args:
            prompt: Input prompt.
            model_name: Optional Bedrock model ID (e.g. anthropic.claude-opus-4-5-20251101-v1:0).
                        If None or a non-Bedrock name, uses BEDROCK_MODEL_ID or default Claude Opus.

        Returns:
            Generated text.
        """
        model_id = self.model_id
        if model_name and ("anthropic." in model_name or "claude" in model_name.lower()):
            model_id = model_name
        try:
            return self._invoke_messages(prompt, model_id)
        except (ClientError, BotoCoreError) as e:
            msg = str(e)
            print(f"❌ Error invoking Claude on Bedrock: {msg}")
            raise

    def generate_with_claude(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.2,
    ) -> str:
        """
        Generate text using Claude on Bedrock (explicit API).

        Args:
            prompt: User prompt.
            model_id: Bedrock model ID. Defaults to configured default.
            max_tokens: Maximum output tokens.
            temperature: Sampling temperature.

        Returns:
            Generated text.
        """
        model_id = model_id or self.model_id
        return self._invoke_messages(
            prompt,
            model_id,
            max_tokens=max_tokens,
            temperature=temperature,
        )


def main() -> None:
    """Quick test of Bedrock Claude client."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    client = BedrockClaudeClient(region_name=region)

    print("\n🤖 Bedrock Claude Opus – test generation")
    print("-" * 50)
    prompt = "In one sentence, what is the main purpose of a 'hello world' program?"
    try:
        response = client.generate_with_bedrock(prompt)
        print(f"Prompt: {prompt}")
        print(f"Response: {response}")
    except (ClientError, BotoCoreError) as e:
        print(f"Error: {e}")
        print("Ensure AWS credentials are set and Claude is enabled in Bedrock for this region.")


if __name__ == "__main__":
    main()
