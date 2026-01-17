"""
Groq LLM Client Module
Provides integration with Groq API for text classification and severity analysis.
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
    # Fallback to root .env if server-specific doesn't exist
    load_dotenv()

logger = logging.getLogger(__name__)


class GroqClient:
    """Client for Groq LLM API integration."""

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the Groq client.

        Args:
            api_key: Groq API key. Defaults to GROQ_API_KEY environment variable.
            model: Model to use for inference. Defaults to llama-3.3-70b-versatile.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self._client = None

        if not self.api_key:
            logger.warning("GROQ_API_KEY not set. LLM features will be limited.")

    def _get_client(self):
        """Lazily initialize the Groq client."""
        if self._client is None:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except ImportError:
                logger.error("groq package not installed. Run: pip install groq")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                raise
        return self._client

    def classify_text(
        self,
        text: str,
        categories: List[Dict[str, Any]],
        industry: str
    ) -> Dict[str, Any]:
        """
        Classify intake text into a category using LLM.

        Args:
            text: The intake text to classify
            categories: List of category definitions from config
            industry: The industry context

        Returns:
            Classification result with category, confidence, and explanation
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

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise classification assistant. Always respond with valid JSON only, no additional text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            result = json.loads(result_text)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._fallback_classify(text, categories)
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
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

        Args:
            text: The intake text to analyze
            category: The classified category
            severity_rules: Severity rules from config
            risk_flags: Risk flag keywords from config
            industry: The industry context

        Returns:
            Severity analysis with score, priority, and risk flags
        """
        if not self.api_key:
            return self._fallback_severity(text, severity_rules, risk_flags)

        # Build severity level descriptions
        severity_desc = "\n".join([
            f"- Score {rules.get('score', level)}: {level.upper()} - Keywords: {', '.join(rules.get('keywords', [])[:5])}"
            for level, rules in severity_rules.items()
            if isinstance(rules, dict)
        ])

        # Build risk flag descriptions
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
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise severity analysis assistant. Always respond with valid JSON only, no additional text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            result_text = response.choices[0].message.content.strip()
            
            # Handle potential markdown code blocks
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            result = json.loads(result_text)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._fallback_severity(text, severity_rules, risk_flags)
        except Exception as e:
            logger.error(f"LLM severity analysis failed: {e}")
            return self._fallback_severity(text, severity_rules, risk_flags)

    def detect_industry(self, text: str, available_industries: List[str]) -> Dict[str, Any]:
        """
        Detect the industry from intake text.

        Args:
            text: The intake text to analyze
            available_industries: List of available industry configurations

        Returns:
            Industry detection result with industry name and confidence
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
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise industry classification assistant. Always respond with valid JSON only, no additional text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )

            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            result = json.loads(result_text)
            
            # Validate industry is in available list
            if result.get('industry') not in available_industries:
                result['industry'] = available_industries[0] if available_industries else 'banking'
                result['confidence'] = 0.5
            
            return result

        except Exception as e:
            logger.error(f"Industry detection failed: {e}")
            return self._fallback_detect_industry(text, available_industries)

    def _fallback_classify(
        self,
        text: str,
        categories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback keyword-based classification when LLM is unavailable."""
        text_lower = text.lower()
        best_match = None
        best_score = 0

        for category in categories:
            keywords = category.get('keywords', [])
            matches = sum(1 for kw in keywords if kw.lower() in text_lower)
            if matches > best_score:
                best_score = matches
                best_match = category

        if best_match:
            confidence = min(0.3 + (best_score * 0.1), 0.7)  # Cap at 0.7 for fallback
            return {
                "category_id": best_match['id'],
                "category_name": best_match['name'],
                "confidence": confidence,
                "subcategory": None,
                "explanation": f"Matched {best_score} keywords (fallback mode)"
            }

        # Default to first category if no matches
        default_cat = categories[0] if categories else {"id": "unknown", "name": "Unknown"}
        return {
            "category_id": default_cat['id'],
            "category_name": default_cat['name'],
            "confidence": 0.2,
            "subcategory": None,
            "explanation": "No keyword matches found (fallback mode)"
        }

    def _fallback_severity(
        self,
        text: str,
        severity_rules: Dict[str, Any],
        risk_flags: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Fallback keyword-based severity analysis when LLM is unavailable."""
        text_lower = text.lower()
        
        # Check severity keywords
        detected_severity = "low"
        severity_score = 2
        
        for level, rules in severity_rules.items():
            if not isinstance(rules, dict):
                continue
            keywords = rules.get('keywords', [])
            if any(kw.lower() in text_lower for kw in keywords):
                score = rules.get('score', 2)
                if score > severity_score:
                    severity_score = score
                    detected_severity = level

        # Check risk flags
        found_flags = []
        for flag_type, flags in risk_flags.items():
            if any(flag.lower() in text_lower for flag in flags):
                found_flags.append(flag_type)

        # Determine priority
        if severity_score >= 5:
            priority = "urgent"
        elif severity_score >= 4:
            priority = "high"
        elif severity_score >= 3:
            priority = "normal"
        else:
            priority = "low"

        return {
            "severity_score": severity_score,
            "severity_level": detected_severity,
            "priority": priority,
            "risk_flags_found": found_flags,
            "urgency_indicators": [],
            "explanation": "Keyword-based analysis (fallback mode)"
        }

    def _fallback_detect_industry(
        self,
        text: str,
        available_industries: List[str]
    ) -> Dict[str, Any]:
        """Fallback keyword-based industry detection."""
        text_lower = text.lower()
        
        industry_keywords = {
            "banking": ["bank", "account", "loan", "credit", "debit", "atm", "wire", "transfer", "mortgage"],
            "healthcare": ["doctor", "patient", "prescription", "medical", "appointment", "health", "hospital", "nurse"],
            "it_services": ["computer", "laptop", "password", "network", "software", "email", "vpn", "system", "error"],
            "retail": ["order", "return", "refund", "product", "delivery", "shipping", "store", "purchase", "item"],
            "logistics": ["shipment", "package", "tracking", "delivery", "freight", "carrier", "customs", "container"]
        }

        best_industry = available_industries[0] if available_industries else "banking"
        best_score = 0

        for industry, keywords in industry_keywords.items():
            if industry in available_industries:
                matches = sum(1 for kw in keywords if kw in text_lower)
                if matches > best_score:
                    best_score = matches
                    best_industry = industry

        confidence = min(0.3 + (best_score * 0.1), 0.7)
        
        return {
            "industry": best_industry,
            "confidence": confidence,
            "explanation": f"Matched {best_score} keywords (fallback mode)"
        }


# Global singleton instance
_groq_client: Optional[GroqClient] = None


def get_groq_client() -> GroqClient:
    """Get the global Groq client instance."""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
