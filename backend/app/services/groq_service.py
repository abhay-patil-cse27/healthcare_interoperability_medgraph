"""
Groq LLM Service
=================
Wraps the Groq SDK with:
  - Multi-turn conversation history support (for chat)
  - Retry with exponential backoff
  - Structured logging
"""
import time
import structlog
from typing import List, Optional
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings

logger = structlog.get_logger()


class GroqService:
    def __init__(self):
        settings = get_settings()
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def invoke(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        history: Optional[List[dict]] = None,
    ) -> dict:
        """
        Invoke the LLM with optional conversation history.

        Args:
            system_prompt: The system-level instruction for the model.
            user_message:  The current user turn content.
            max_tokens:    Max tokens in the response.
            temperature:   Sampling temperature (0.0 = deterministic).
            history:       List of prior turns in OpenAI format:
                           [{"role": "user"|"assistant", "content": "..."}]
                           These are inserted between the system prompt and
                           the current user message.
        """
        messages = [{"role": "system", "content": system_prompt}]

        # Inject conversation history before the current turn
        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        start = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            latency_ms = int((time.time() - start) * 1000)
            text = response.choices[0].message.content

            logger.info(
                "groq_invoked",
                latency_ms=latency_ms,
                model=self.model,
                history_turns=len(history) if history else 0,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            )
            return {
                "text": text,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "latency_ms": latency_ms,
            }
        except Exception as e:
            logger.error("groq_invocation_failed", error=str(e))
            raise
