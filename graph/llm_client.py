"""
LLM Client - Model-agnostic interface for various providers
"""
import os
import json
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """
    Unified LLM interface supporting multiple providers.
    Configure via environment variables:
    - LLM_PROVIDER: openai|anthropic|local
    - LLM_MODEL: model name/identifier
    - LLM_API_KEY: API key for the provider
    """
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        
        # Initialize provider-specific client
        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("Install anthropic: pip install anthropic")
        elif self.provider == "local":
            # For local models via OpenAI-compatible API (e.g., vLLM, Ollama)
            from openai import OpenAI
            base_url = os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")
            self.client = OpenAI(api_key="not-needed", base_url=base_url)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Send chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (overrides default)
            max_tokens: Maximum tokens in response
            response_format: Optional format spec (e.g., {"type": "json_object"})
        
        Returns:
            str: Response content
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens or 2000
        
        if self.provider == "openai" or self.provider == "local":
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temp,
                "max_tokens": tokens
            }
            if response_format:
                kwargs["response_format"] = response_format
            
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        
        elif self.provider == "anthropic":
            # Anthropic has different message format
            system_msg = None
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)
            
            kwargs = {
                "model": self.model,
                "messages": user_messages,
                "temperature": temp,
                "max_tokens": tokens
            }
            if system_msg:
                kwargs["system"] = system_msg
            
            response = self.client.messages.create(**kwargs)
            return response.content[0].text
        
        raise NotImplementedError(f"Chat not implemented for {self.provider}")
    
    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Request JSON response from LLM.
        
        Returns:
            dict: Parsed JSON response
        """
        # For OpenAI, we can use response_format
        if self.provider == "openai":
            response = self.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
        else:
            # For other providers, add JSON instruction
            messages = messages.copy()
            if messages[-1]["role"] == "user":
                messages[-1]["content"] += "\n\nRespond with valid JSON only."
            
            response = self.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        # Parse JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Failed to parse JSON from response: {response[:200]}")


# Singleton instance
_llm_client = None

def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def load_prompt(filename: str) -> str:
    """Load prompt from prompts/ directory."""
    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "prompts",
        filename
    )
    with open(prompt_path, "r") as f:
        return f.read()
