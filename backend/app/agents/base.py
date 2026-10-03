"""
Base Agent - Provides LLM interface for all agents
"""

import logging
from abc import ABC, abstractmethod
from groq import Groq
import asyncio
import google.generativeai as genai
from app.core.config import settings
from app.models.debate import AgentRole


class BaseAgent(ABC):
    """
    Base class for all debate agents.
    Provides Groq LLM interface for debaters and Gemini interface for neutral synthesis.
    """

    def __init__(self, role: AgentRole):
        self.role = role
        self._logger = logging.getLogger("aether.agents")
        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set. Please add it to .env file")
        self.client = Groq(api_key=api_key)

    # ------------------------------------------------------------------
    # Text clipping helpers
    # ------------------------------------------------------------------

    def _clip(self, text: str) -> str:
        max_chars = getattr(settings, "LOG_LLM_MAX_CHARS", 4000)
        if not text:
            return ""
        if max_chars and len(text) > max_chars:
            return text[:max_chars] + "\n... (truncated)"
        return text

    def _clip_store(self, text: str) -> str:
        max_chars = getattr(settings, "STORE_LLM_MAX_CHARS", 12000)
        if not text:
            return ""
        if max_chars and len(text) > max_chars:
            return text[:max_chars] + "\n... (truncated)"
        return text

    def _log_block(self, title: str, body: str) -> None:
        if not getattr(settings, "LOG_AGENT_CONVERSATION", False):
            return
        clipped = self._clip(body)
        header = f"\n{'=' * 18} {title} ({self.role.value}) {'=' * 18}"
        footer = f"{'=' * (len(header) - 2)}\n"
        print(header)
        print(clipped)
        print(footer)

    # ------------------------------------------------------------------
    # Groq — used by all debater agents
    # ------------------------------------------------------------------

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        *,
        debate_id: str | None = None,
        event_prefix: str = "llm",
        meta: dict | None = None,
    ) -> str:
        """
        Call Groq LLM with system and user prompts.
        Used by Pro, Con, CrossExaminer, RoundEvaluator agents.
        """
        try:
            if getattr(settings, "LOG_LLM_PROMPTS", False):
                self._log_block("SYSTEM PROMPT", system_prompt)
                self._log_block("USER PROMPT", user_prompt)

            message = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )

            content = message.choices[0].message.content

            if getattr(settings, "LOG_LLM_RESPONSES", False):
                self._log_block("MODEL RESPONSE", content)

            return content

        except Exception as e:
            print(f"LLM call error ({self.role.value}): {e}")
            raise

    # ------------------------------------------------------------------
    # Gemini — one-sentence neutral rebuttal summary (existing)
    # ------------------------------------------------------------------

    async def _call_gemini(self, text: str) -> str:
        """
        Call Gemini to produce a neutral 1-sentence summary of a rebuttal.
        Used to populate summary_fact on RebuttalArgument without bias.
        Falls back to a character-trimmed version of text if Gemini is unavailable.
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            self._logger.warning("GEMINI_API_KEY not set — falling back to text trim for summary_fact")
            return text[:300] + "..." if len(text) > 300 else text

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            prompt = (
                "Summarise the following debate rebuttal into exactly 1 neutral, informative sentence "
                "that captures its core claim. Do not take sides. Output only the sentence.\n\n"
                f"{text}"
            )
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text.strip()
        except Exception as e:
            self._logger.warning(f"Gemini summarization failed: {e} — falling back to text trim")
            return text[:300] + "..." if len(text) > 300 else text

    # ------------------------------------------------------------------
    # Gemini — full synthesis call (new)
    # Used by SynthesizerAgent as primary LLM.
    # Falls back to Groq if Gemini is unavailable or fails.
    # ------------------------------------------------------------------

    async def _call_gemini_synthesis(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        debate_id: str | None = None,
    ) -> str:
        """
        Call Gemini for full structured synthesis.
        Primary model for SynthesizerAgent — neutral, large context window.

        Falls back to Groq (_call_llm) if:
        - GEMINI_API_KEY is not set
        - Gemini call raises any exception

        Args:
            system_prompt: System instructions (role + output format)
            user_prompt:   Full debate content to synthesize
            debate_id:     Optional — for logging

        Returns:
            Raw text response containing JSON
        """
        api_key = settings.GEMINI_API_KEY

        if not api_key:
            self._logger.warning(
                "GEMINI_API_KEY not set — falling back to Groq for synthesis"
            )
            return await self._groq_synthesis_fallback(system_prompt, user_prompt)

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction=system_prompt,
            )

            if getattr(settings, "LOG_LLM_PROMPTS", False):
                self._log_block("GEMINI SYNTHESIS PROMPT", user_prompt)

            response = await asyncio.to_thread(
                model.generate_content,
                user_prompt,
            )

            content = response.text.strip()

            if getattr(settings, "LOG_LLM_RESPONSES", False):
                self._log_block("GEMINI SYNTHESIS RESPONSE", content)

            print(f"✅ Gemini synthesis completed ({len(content)} chars)")
            return content

        except Exception as e:
            self._logger.warning(
                f"Gemini synthesis failed: {e} — falling back to Groq"
            )
            return await self._groq_synthesis_fallback(system_prompt, user_prompt)

    async def _groq_synthesis_fallback(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        """
        Groq fallback for synthesis when Gemini is unavailable.
        Uses higher max_tokens than normal agents to handle large debate inputs.
        """
        print("⚠️  Using Groq as synthesis fallback")
        try:
            return await self._call_llm(
                system_prompt,
                user_prompt,
                max_tokens=6000,
                event_prefix="synthesis_fallback",
            )
        except Exception as e:
            self._logger.error(f"Groq synthesis fallback also failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Abstract
    # ------------------------------------------------------------------

    @abstractmethod
    async def execute(self, *args, **kwargs):
        """Execute the agent's task - implemented by subclasses"""
        pass