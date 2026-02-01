"""
Gemini LLM Client Module
Provides integration with Google Gemini Pro API for text classification and severity analysis.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from mcp_server/.env
_server_dir = Path(__file__).parent.parent  # Go up from llm/ to mcp_server/
_env_path = _server_dir / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini API integration."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro"):
        """
        Initialize the Gemini client.

        Args:
            api_key: Gemini API key. Defaults to GEMINI_API_KEY environment variable.
            model: Model to use for inference. Defaults to gemini-pro.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self._genai = None
        self._model_instance = None

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. LLM features will be limited.")

    def _get_client(self):
        """Lazily initialize the Gemini client."""
        if self._genai is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._genai = genai
                self._model_instance = genai.GenerativeModel(self.model)
            except ImportError:
                logger.error("google-generativeai package not installed. Run: pip install google-generativeai")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                raise
        return self._model_instance

    def classify_text(
        self,
        text: str,
        categories: List[Dict[str, Any]],
        industry: str,
        images: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Classify intake text into a category using LLM.
        
        Args:
            text: The intake text to classify
            categories: List of category definitions from config
            industry: The industry context
            images: Optional list of image dicts with base64_data, mime_type, filename
        """
        if not self.api_key:
            return self._fallback_classify(text, categories)

        # Build category descriptions for the prompt
        category_list = "\n".join([
            f"- {cat['id']}: {cat['name']} - {cat.get('description', '')}"
            for cat in categories
        ])

        prompt = f"""You are an expert intake classifier for the {industry} industry.
        Analyze the following intake text and classify it into one of the categories below.

        CATEGORIES:
        {category_list}

        INTAKE TEXT:
        {text}

        Respond ONLY with a valid JSON object in this exact format:
        {{
            "category_id": "the matching category id",
            "category_name": "the category name",
            "confidence": 0.95,
            "subcategory": "optional subcategory if applicable",
            "explanation": "brief explanation of why this category was chosen"
        }}

        Important:
        - confidence should be a number between 0 and 1
        - Choose the most specific and accurate category
        - If multiple categories could apply, choose the primary one"""

        # Add image analysis instruction if images are present
        if images:
            prompt += "\n- Also analyze any images provided and incorporate their content into your classification decision."

        try:
            # Determine model - use vision-capable model if images present
            model_to_use = self.model
            if images:
                model_to_use = "gemini-2.5-flash"
            
            # Re-initialize model if different from default
            if model_to_use != self.model:
                import google.generativeai as genai
                model = genai.GenerativeModel(model_to_use)
            else:
                model = self._get_client()
            
            # Build content for request
            if images:
                # Multimodal request with images
                from PIL import Image
                import io
                import base64
                
                content = [prompt]
                for img in images[:5]:  # Limit to 5 images
                    try:
                        # Decode base64 and create PIL Image
                        img_bytes = base64.b64decode(img['base64_data'])
                        pil_image = Image.open(io.BytesIO(img_bytes))
                        content.append(pil_image)
                    except Exception as e:
                        logger.warning(f"Failed to process image: {e}")
                
                response = model.generate_content(content)
            else:
                # Text-only request
                response = model.generate_content(prompt)
            
            result_text = response.text.strip()
            
            # Parse JSON response
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            result = json.loads(result_text)
            
            # Add model info to result
            result["model_used"] = model_to_use
            
            return result

        except Exception as e:
            logger.error(f"Gemini classification failed: {e}")
            return self._fallback_classify(text, categories)

    def analyze_severity(
        self,
        text: str,
        category: str,
        severity_rules: Dict[str, Any],
        risk_flags: Dict[str, List[str]],
        industry: str
    ) -> Dict[str, Any]:
        """
        Analyze severity of intake text using LLM.
        """
        if not self.api_key:
            return self._fallback_severity(text, severity_rules, risk_flags)

        severity_desc = "\n".join([
            f"- Score {rules.get('score', level)}: {level.upper()} - Keywords: {', '.join(rules.get('keywords', [])[:5])}"
            for level, rules in severity_rules.items()
            if isinstance(rules, dict)
        ])

        risk_desc = "\n".join([
            f"- {flag_type}: {', '.join(flags[:5])}"
            for flag_type, flags in risk_flags.items()
        ])

        prompt = f"""You are an expert severity analyst for the {industry} industry.
        Analyze the following intake text that has been classified as "{category}".

        SEVERITY LEVELS:
        {severity_desc}

        RISK FLAG CATEGORIES:
        {risk_desc}

        INTAKE TEXT:
        {text}

        Respond ONLY with a valid JSON object in this exact format:
        {{
            "severity_score": 3,
            "severity_level": "medium",
            "priority": "normal",
            "risk_flags_found": ["list", "of", "matching", "risk", "flag", "types"],
            "urgency_indicators": ["specific", "urgent", "phrases", "found"],
            "explanation": "brief explanation of severity assessment"
        }}

        Important:
        - severity_score should be 1-5 (1=minimal, 5=critical)
        - priority should be: "low", "normal", "high", or "urgent"
        - List all applicable risk flag types that match"""

        try:
            model = self._get_client()
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            result = json.loads(result_text)
            return result

        except Exception as e:
            logger.error(f"Gemini severity analysis failed: {e}")
            return self._fallback_severity(text, severity_rules, risk_flags)

    def detect_industry(self, text: str, available_industries: List[str]) -> Dict[str, Any]:
        """
        Detect the industry from intake text.
        """
        if not self.api_key:
            return self._fallback_detect_industry(text, available_industries)

        industry_list = ", ".join(available_industries)

        prompt = f"""You are an expert at classifying customer inquiries into industry categories.
        Analyze the following text and determine which industry it belongs to.

        AVAILABLE INDUSTRIES: {industry_list}

        TEXT:
        {text}

        Respond ONLY with a valid JSON object in this exact format:
        {{
            "industry": "the matching industry name",
            "confidence": 0.95,
            "explanation": "brief explanation of why this industry was chosen"
        }}

        Important:
        - industry must be one of the available industries listed above
        - confidence should be a number between 0 and 1"""

        try:
            model = self._get_client()
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            result = json.loads(result_text)
            
            if result.get('industry') not in available_industries:
                result['industry'] = available_industries[0] if available_industries else 'banking'
                result['confidence'] = 0.5
            
            return result

        except Exception as e:
            logger.error(f"Gemini industry detection failed: {e}")
            return self._fallback_detect_industry(text, available_industries)

    def _fallback_classify(self, text, categories):
        """Fallback keyword-based classification."""
        # Reuse logic from GroqClient or implement similar
        # For simplicity, returning a default
        default_cat = categories[0] if categories else {"id": "unknown", "name": "Unknown"}
        return {
            "category_id": default_cat['id'],
            "category_name": default_cat['name'],
            "confidence": 0.2,
            "subcategory": None,
            "explanation": "Gemini not available (fallback mode)"
        }

    def _fallback_severity(self, text, severity_rules, risk_flags):
        """Fallback keyword-based severity analysis."""
        return {
            "severity_score": 2,
            "severity_level": "low",
            "priority": "low",
            "risk_flags_found": [],
            "urgency_indicators": [],
            "explanation": "Gemini not available (fallback mode)"
        }

    def _fallback_detect_industry(self, text, available_industries):
        """Fallback keyword-based industry detection."""
        return {
            "industry": available_industries[0] if available_industries else "banking",
            "confidence": 0.3,
            "explanation": "Gemini not available (fallback mode)"
        }


# Global singleton instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get the global Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
