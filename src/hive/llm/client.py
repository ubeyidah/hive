"""LiteLLM client wrapper for Hive."""

from __future__ import annotations

from typing import List, Dict, Optional

import litellm

from hive.config.schema import LLMConfig


class HiveLLMClient:
    def __init__(self, llm_config: LLMConfig) -> None:
        self.llm_config = llm_config
        self.model = self._build_model_string(llm_config.provider, llm_config.model)
        self.api_key = llm_config.api_key

    @staticmethod
    def _build_model_string(provider: str, model: str) -> str:
        if provider == "openai":
            return model
        if provider == "anthropic":
            return f"anthropic/{model}"
        if provider == "groq":
            return f"groq/{model}"
        return model

    async def chat(self, messages: List[Dict]) -> Optional[str]:
        try:
            response = await litellm.acompletion(
                model=self.model, messages=messages, api_key=self.api_key
            )
            return response.choices[0].message.content
        except Exception as exc:  # pragma: no cover - error path
            provider = self.llm_config.provider
            model = self.llm_config.model
            print(f"LLM Error ({provider}/{model}): {exc}")
            return None

    async def test_connection(self) -> bool:
        response = await self.chat([{"role": "user", "content": "Say hello"}])
        if response:
            print("Connection OK")
            return True
        print("Connection FAILED")
        return False
