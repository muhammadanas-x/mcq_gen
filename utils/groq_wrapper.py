"""
Wrapper for Groq API to make it compatible with LangChain interface
"""
import os
from groq import Groq
from typing import List, Dict, Any


class GroqChatResponse:
    """Mock LangChain response object for Groq"""
    def __init__(self, content: str):
        self.content = content


class ChatGroq:
    """
    Wrapper for Groq client that mimics LangChain's ChatModel interface.
    Uses the native Groq SDK.
    """
    
    def __init__(self, model: str, temperature: float = 0.7, **kwargs):
        """
        Initialize Groq client.
        
        Args:
            model: Model name (e.g., "llama-3.3-70b-versatile")
            temperature: Temperature for generation (0.0 to 2.0)
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.timeout = 120  # 2 minute timeout for long requests
    
    def invoke(self, messages: List[Dict[str, str]]) -> GroqChatResponse:
        """
        Invoke Groq API with messages (compatible with LangChain interface).
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
                     OR a list of LangChain message objects
        
        Returns:
            GroqChatResponse with content attribute
        """
        # Convert LangChain message objects to dict format if needed
        formatted_messages = []
        for msg in messages:
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                # LangChain message object
                role = 'user' if msg.type == 'human' else msg.type
                formatted_messages.append({
                    "role": role,
                    "content": msg.content
                })
            elif isinstance(msg, dict):
                # Already a dict
                formatted_messages.append(msg)
            else:
                # Fallback
                formatted_messages.append({
                    "role": "user",
                    "content": str(msg)
                })
        
        # Call Groq API with timeout and retry logic
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=self.temperature,
                max_tokens=32768,  # Increased for large JSON responses
                top_p=1,
                stream=False,  # Use non-streaming for compatibility
                stop=None,
                timeout=self.timeout
            )
        except Exception as e:
            # Retry once on connection error
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                print(f"⚠ Connection error, retrying... ({str(e)[:100]})")
                import time
                time.sleep(2)
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    temperature=self.temperature,
                    max_tokens=32000,
                    top_p=1,
                    stream=False,
                    stop=None,
                    timeout=self.timeout
                )
            else:
                raise
        
        # Extract response content
        response_content = completion.choices[0].message.content
        
        # Return LangChain-compatible response
        return GroqChatResponse(content=response_content)
