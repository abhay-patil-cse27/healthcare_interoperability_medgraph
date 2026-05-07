"""
AWS Bedrock LLM Service
========================
Replaces Groq with AWS Bedrock (Claude Sonnet).
Uses boto3 with the user's configured AWS CLI credentials.
Supports:
  - Multi-turn conversation history
  - Retry with exponential backoff
  - Structured logging
  - Amazon Bedrock Guardrails (HIPAA-compliant content filtering)

Guardrails are applied when BEDROCK_GUARDRAIL_ID is set in .env.
The guardrail checks both input and output for:
  - PHI/PII leakage
  - Unsafe medical advice
  - Content policy violations (hate, violence, etc.)
  - Denied topics (diagnosis, unauthorized access)
  - Contextual grounding (hallucination prevention)
"""
import json
import time
import structlog
from typing import List, Optional
import boto3
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings

logger = structlog.get_logger()


class GuardrailInterventionError(Exception):
    """Raised when Bedrock Guardrails block the request or response."""
    def __init__(self, message: str, action: str, trace: dict = None):
        super().__init__(message)
        self.action = action  # "GUARDRAIL_INTERVENED"
        self.trace = trace


class BedrockService:
    def __init__(self):
        settings = get_settings()
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
        )
        self.model_id = settings.bedrock_model_id
        self.guardrail_id = settings.bedrock_guardrail_id
        self.guardrail_version = settings.bedrock_guardrail_version

        if self.guardrail_id:
            logger.info(
                "bedrock_guardrails_enabled",
                guardrail_id=self.guardrail_id,
                guardrail_version=self.guardrail_version,
            )
        else:
            logger.warning("bedrock_guardrails_disabled", reason="BEDROCK_GUARDRAIL_ID not set")

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
        apply_guardrails: bool = True,
    ) -> dict:
        """
        Invoke Claude via Bedrock Converse API with optional Guardrails.

        Args:
            system_prompt:     System-level instruction.
            user_message:      Current user turn.
            max_tokens:        Max tokens in response.
            temperature:       Sampling temperature (0.0 = deterministic).
            history:           Prior turns: [{"role": "user"|"assistant", "content": "..."}]
            apply_guardrails:  Whether to apply Bedrock Guardrails (default: True).
                               Set to False for internal operations like entity extraction
                               where guardrails may interfere with structured output.
        """
        # Build messages in Bedrock Converse format
        messages = []

        if history:
            for turn in history:
                messages.append({
                    "role": turn["role"],
                    "content": [{"text": turn["content"]}],
                })

        messages.append({
            "role": "user",
            "content": [{"text": user_message}],
        })

        # Build invoke kwargs
        invoke_kwargs = {
            "modelId": self.model_id,
            "system": [{"text": system_prompt}],
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
        }

        # Apply Bedrock Guardrails if configured
        if apply_guardrails and self.guardrail_id:
            invoke_kwargs["guardrailConfig"] = {
                "guardrailIdentifier": self.guardrail_id,
                "guardrailVersion": self.guardrail_version or "DRAFT",
                "trace": "enabled",
            }

        start = time.time()
        try:
            response = self.client.converse(**invoke_kwargs)

            latency_ms = int((time.time() - start) * 1000)

            # Check if guardrail intervened
            stop_reason = response.get("stopReason", "")
            if stop_reason == "guardrail_intervened":
                # Guardrail blocked the output
                output_message = response.get("output", {}).get("message", {})
                blocked_text = ""
                if output_message.get("content"):
                    blocked_text = output_message["content"][0].get("text", "")

                # Extract guardrail trace for logging
                trace = response.get("trace", {}).get("guardrail", {})
                guardrail_action = trace.get("action", "INTERVENED")

                logger.warning(
                    "bedrock_guardrail_intervened",
                    action=guardrail_action,
                    latency_ms=latency_ms,
                    model=self.model_id,
                    guardrail_id=self.guardrail_id,
                )

                # Return the blocked message (guardrail's replacement text)
                return {
                    "text": blocked_text or "This request was blocked by our safety policies. Please rephrase your query.",
                    "input_tokens": response.get("usage", {}).get("inputTokens", 0),
                    "output_tokens": response.get("usage", {}).get("outputTokens", 0),
                    "latency_ms": latency_ms,
                    "guardrail_action": "BLOCKED",
                    "guardrail_trace": trace,
                }

            # Normal response
            output_message = response["output"]["message"]
            text = output_message["content"][0]["text"]

            # Token usage
            usage = response.get("usage", {})
            input_tokens = usage.get("inputTokens", 0)
            output_tokens = usage.get("outputTokens", 0)

            # Check for guardrail trace even on successful responses (for monitoring)
            guardrail_trace = response.get("trace", {}).get("guardrail", {})

            logger.info(
                "bedrock_invoked",
                latency_ms=latency_ms,
                model=self.model_id,
                history_turns=len(history) if history else 0,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                guardrail_applied=bool(apply_guardrails and self.guardrail_id),
            )

            result = {
                "text": text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": latency_ms,
                "guardrail_action": "NONE",
            }

            # Include trace if guardrail was applied (useful for audit)
            if guardrail_trace:
                result["guardrail_trace"] = guardrail_trace

            return result

        except self.client.exceptions.ValidationException as e:
            logger.error("bedrock_validation_error", error=str(e), model=self.model_id)
            raise
        except Exception as e:
            logger.error("bedrock_invocation_failed", error=str(e), model=self.model_id)
            raise
