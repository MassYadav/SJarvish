import logging
from typing import List, Dict, Any, Optional
import litellm
from litellm import acompletion
from core.config import settings
from core.security.encryption import vault

# Disable LiteLLM phone-home diagnostics and verbose telemetry
litellm.telemetry = False
litellm.suppress_logs = True

logger = logging.getLogger(__name__)

class LLMRouter:
    """
    High-availability LLM router utilizing LiteLLM.
    Handles seamless provider failover, local Ollama fallbacks,
    and runtime key injection through the cryptographic vault.
    """
    def __init__(self):
        # Explicit master hierarchy chain for your JARVIS-tier OS
        self.fallback_chain = [
            {"provider": "gemini", "model": "gemini/gemini-1.5-flash-latest"},
            {"provider": "openai", "model": "azure/gpt-4o" if "azure" in settings.REDIS_URL else "openai/gpt-4o"},
            {"provider": "anthropic", "model": "anthropic/claude-3-5-sonnet"},
            {"provider": "groq", "model": "groq/llama3-70b-8192"},
            {"provider": "deepseek", "model": "deepseek/deepseek-chat"},
            {"provider": "openrouter", "model": "openrouter/meta-llama/llama-3-70b-instruct"},
            {"provider": "ollama", "model": "ollama/qwen2.5"}
        ]

    def _get_api_key_for_provider(self, provider: str, custom_encrypted_key: Optional[str] = None) -> Optional[str]:
        """
        Extracts the requested API key. Prioritizes runtime dashboard-injected 
        keys (decrypted through the vault) before falling back to system environment variables.
        """
        if custom_encrypted_key:
            try:
                return vault.decrypt(custom_encrypted_key)
            except Exception as e:
                logger.error(f"Vault decryption failed for provider {provider}: {e}")

        # Fallback to systemic .env values loaded via Pydantic settings
        attr_map = {
            "gemini": "GEMINI_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "groq": "GROQ_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "openrouter": "OPENROUTER_API_KEY"
        }
        
        setting_attr = attr_map.get(provider)
        if setting_attr and hasattr(settings, setting_attr):
            secret_obj = getattr(settings, setting_attr)
            if secret_obj:
                return secret_obj.get_secret_value()
                
        return None

    async def generate_reply(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        runtime_keys: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executes an asynchronous chat completion request against the model pipeline.
        Loops through the high-availability failover chain if providers drop offline.
        """
        runtime_keys = runtime_keys or {}
        last_exception = None

        for tier in self.fallback_chain:
            provider = tier["provider"]
            model_string = tier["model"]
            
            # Extract credentials for this candidate tier
            api_key = self._get_api_key_for_provider(provider, runtime_keys.get(provider))
            
            # Ollama doesn't require an upstream API token; cloud services do
            if provider != "ollama" and not api_key:
                logger.debug(f"Skipping {provider}: No valid API credential supplied.")
                continue

            try:
                logger.info(f"Routing execution payload to targeting tier: {model_string}")
                
                # Setup unified parameter arguments for execution
                kwargs: Dict[str, Any] = {
                    "model": model_string,
                    "messages": messages,
                    "temperature": temperature,
                    "timeout": 60.0 # Guardrail timeout before executing chain-failover
                }
                
                if api_key:
                    kwargs["api_key"] = api_key
                if max_tokens:
                    kwargs["max_tokens"] = max_tokens

                # Execute async network completion call
                response = await acompletion(**kwargs)
                
                # Record route execution matrix metadata
                return {
                    "success": True,
                    "model_used": model_string,
                    "provider": provider,
                    "content": response.choices[0].message.content,
                    "usage": dict(response.get("usage", {}))
                }

            except Exception as e:
                logger.warn(f"⚠️ Provider Alert: {model_string} execution dropped out. Error: {str(e)}")
                last_exception = e
                # Fallthrough to next index item block within the execution loop array
                continue

        # If loop fully exhausts without a single breakthrough completion state:
        logger.critical("🛑 Upstream Blackout: Entire LLM failover architecture has been exhausted.")
        return {
            "success": False,
            "error": str(last_exception) if last_exception else "No active provider credentials configured.",
            "fallback_exhausted": True
        }

# Instantiate global high-availability inference router
llm_router = LLMRouter()