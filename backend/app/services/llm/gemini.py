"""
Google Gemini LLM Client - Chat completions with error handling
Robust version that handles blocked DLLs in restricted environments.
"""
import os
import logging
from typing import Any, Dict, Optional
from app.core.config import settings

logger = logging.getLogger("ai_workforce.llm.gemini")

# Lazy import to prevent crash if library is blocked by IT policy
genai = None
import_error_msg = None

try:
    import google.generativeai as _genai
    genai = _genai
except ImportError as e:
    import_error_msg = str(e)
    logger.error(f"Gemini library (google-generativeai) could not be loaded: {e}")
except Exception as e:
    import_error_msg = str(e)
    logger.error(f"Unexpected error loading Gemini library: {e}")


class GeminiClient:
    """Google Gemini chat client with error handling."""

    def __init__(self):
        self._has_api_key = False
        self.model = None
        self.model_name = settings.GEMINI_MODEL
        
        if import_error_msg:
            logger.warning(f"GeminiClient initialized in restricted mode: {import_error_msg}")
            return

        api_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            logger.warning("GOOGLE_API_KEY is not set. Gemini API calls will fail.")
        
        if genai:
            try:
                genai.configure(api_key=api_key or "no-google-api-key-set")
                self.model = genai.GenerativeModel(self.model_name)
                self._has_api_key = bool(api_key)
            except Exception as e:
                logger.error(f"Failed to configure Gemini: {e}")

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate content using Gemini.
        """
        if import_error_msg:
            return {
                "content": "",
                "usage": {},
                "error": "library_blocked",
                "detail": f"Gemini library is blocked or missing in this environment: {import_error_msg}",
            }

        if not self._has_api_key:
            return {
                "content": "",
                "usage": {},
                "error": "api_key_missing",
                "detail": "GOOGLE_API_KEY is not configured.",
            }

        if not genai or not self.model:
            return {
                "content": "",
                "usage": {},
                "error": "init_failed",
                "detail": "Gemini client failed to initialize.",
            }

        try:
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            
            # Disable safety filters to prevent blocks
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            current_model = self.model
            if model and model != self.model_name:
                current_model = genai.GenerativeModel(model)

            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            response = current_model.generate_content(
                full_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
            )
            
            if not response or not response.candidates:
                return {
                    "content": "",
                    "usage": {},
                    "error": "blocked_or_empty",
                    "detail": "Gemini API returned no candidates.",
                }

            try:
                content = response.text
            except ValueError as ve:
                # If safety block, try to get whatever is available
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        content = candidate.content.parts[0].text
                    else:
                        return {
                            "content": "",
                            "usage": {},
                            "error": "safety_block",
                            "detail": str(ve),
                        }
                else:
                    return {
                        "content": "",
                        "usage": {},
                        "error": "safety_block",
                        "detail": str(ve),
                    }
            
            usage = {}
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0),
                }
            else:
                usage = {"total_tokens": len(content.split()) * 4}
                
            return {"content": content, "usage": usage}
            
        except Exception as e:
            logger.error(f"Gemini error: {e}", exc_info=True)
            return {
                "content": "",
                "usage": {},
                "error": "api_error",
                "detail": str(e)
            }
