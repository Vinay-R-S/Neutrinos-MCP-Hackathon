"""
Generic YAML Adapter Module
Provides a flexible adapter that can handle any YAML structure and normalize it
to the format expected by the MCP server. This enables plug-and-play functionality
for different domain configurations.
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)


class GenericYAMLAdapter:
    """
    Adapter for handling arbitrary YAML configurations and normalizing them
    to the expected MCP server format.
    
    This adapter enables plug-and-play functionality by:
    1. Detecting the schema/structure of any YAML file
    2. Mapping alternative field names to expected names
    3. Using LLM for unknown schema discovery when needed
    4. Normalizing the config to the expected format
    """

    # Mapping of alternative key names to expected keys
    # Format: expected_key -> [list of alternative names]
    KEY_MAPPINGS = {
        # Top-level industry/domain identifier
        'industry': ['industry', 'domain', 'sector', 'vertical', 'area', 'field', 'type'],
        
        # Categories/classification structure
        'categories': [
            'categories', 'category', 'items', 'topics', 'types', 'issues', 
            'problems', 'ticket_types', 'complaint_types', 'request_types',
            'inquiry_types', 'case_types', 'classifications', 'classes',
            'ticket_categories', 'issue_types', 'problem_types'
        ],
        
        # Severity/priority rules
        'severity_rules': [
            'severity_rules', 'severity', 'priority_levels', 'priority_rules',
            'priority', 'urgency', 'urgency_levels', 'importance', 'criticality',
            'impact_levels', 'severity_levels', 'priorities'
        ],
        
        # Routing rules
        'routing_rules': [
            'routing_rules', 'routing', 'assignment_rules', 'assignments',
            'teams', 'queues', 'workflow', 'workflows', 'departments',
            'escalation_rules', 'routing_config', 'team_assignments',
            'department_routing', 'queue_rules'
        ],
        
        # Risk flags
        'risk_flags': [
            'risk_flags', 'risks', 'flags', 'indicators', 'triggers',
            'warning_signs', 'alert_triggers', 'risk_indicators',
            'escalation_triggers', 'warning_flags'
        ],
        
        # Sampling thresholds
        'sampling_thresholds': [
            'sampling_thresholds', 'thresholds', 'confidence_thresholds',
            'sampling', 'confidence_levels', 'auto_route_thresholds',
            'settings', 'config_thresholds'
        ]
    }

    # Mapping for category fields
    CATEGORY_FIELD_MAPPINGS = {
        'id': ['id', 'key', 'code', 'identifier', 'type_id', 'category_id', 'cat_id'],
        'name': ['name', 'title', 'label', 'display_name', 'type_name', 'category_name'],
        'description': ['description', 'desc', 'details', 'info', 'about', 'summary'],
        'keywords': [
            'keywords', 'tags', 'labels', 'related_words', 'terms', 
            'search_terms', 'indicators', 'triggers', 'words', 'phrases'
        ],
        'subcategories': [
            'subcategories', 'subtypes', 'children', 'sub_types', 
            'sub_categories', 'nested', 'child_categories'
        ]
    }

    # Mapping for severity level names
    SEVERITY_LEVEL_MAPPINGS = {
        'critical': ['critical', 'p1', 'emergency', 'severe', 'highest', '5', 'urgent'],
        'high': ['high', 'p2', 'important', 'major', '4'],
        'medium': ['medium', 'p3', 'moderate', 'normal', 'standard', '3'],
        'low': ['low', 'p4', 'minor', '2'],
        'minimal': ['minimal', 'p5', 'trivial', 'lowest', 'info', 'informational', '1']
    }

    # Mapping for severity rule fields
    SEVERITY_FIELD_MAPPINGS = {
        'score': ['score', 'value', 'level', 'priority', 'weight', 'rank'],
        'keywords': ['keywords', 'triggers', 'indicators', 'words', 'terms', 'phrases'],
        'conditions': ['conditions', 'criteria', 'rules', 'requirements', 'when']
    }

    # Mapping for routing rule fields
    ROUTING_FIELD_MAPPINGS = {
        'name': ['name', 'team', 'team_name', 'queue', 'dept', 'department', 'id'],
        'display_name': ['display_name', 'label', 'title', 'display', 'friendly_name'],
        'conditions': ['conditions', 'rules', 'criteria', 'when', 'for_types', 'handles'],
        'sla_hours': ['sla_hours', 'sla', 'response_time', 'response_hours', 'target_hours'],
        'escalation_path': ['escalation_path', 'escalate_to', 'escalation', 'next_level', 'fallback'],
        'notes': ['notes', 'description', 'comments', 'info']
    }

    def __init__(self, llm_client=None):
        """
        Initialize the adapter.
        
        Args:
            llm_client: Optional LLM client for schema discovery. If not provided,
                       will attempt to use the default Groq client.
        """
        self._llm_client = llm_client
        self._schema_cache: Dict[str, Dict[str, str]] = {}

    def _get_llm_client(self):
        """Lazily get the LLM client."""
        if self._llm_client is None:
            try:
                from ..llm.groq_client import get_groq_client
                self._llm_client = get_groq_client()
            except Exception as e:
                logger.warning(f"Could not get LLM client: {e}")
        return self._llm_client

    def load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load a YAML file from the given path.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Parsed YAML content as dictionary
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def is_standard_format(self, config: Dict[str, Any]) -> bool:
        """
        Check if the configuration is already in the standard/expected format.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if config matches expected format, False otherwise
        """
        required_keys = ['industry', 'categories', 'severity_rules', 'routing_rules']
        
        # Check all required keys exist
        if not all(key in config for key in required_keys):
            return False
        
        # Check categories structure
        categories = config.get('categories', [])
        if not isinstance(categories, list) or len(categories) == 0:
            return False
        
        # Check first category has required fields
        first_cat = categories[0]
        if not all(key in first_cat for key in ['id', 'name', 'keywords']):
            return False
        
        return True

    def detect_schema(self, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Detect the schema of the configuration and create a mapping.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dictionary mapping detected keys to expected keys
        """
        mapping = {}
        
        for expected_key, alternatives in self.KEY_MAPPINGS.items():
            for alt in alternatives:
                if alt in config:
                    mapping[alt] = expected_key
                    break
        
        return mapping

    def _find_mapped_key(self, config: Dict[str, Any], expected_key: str) -> Optional[str]:
        """
        Find the actual key in config that maps to the expected key.
        
        Args:
            config: Configuration dictionary
            expected_key: The expected/normalized key name
            
        Returns:
            The actual key found in config, or None
        """
        alternatives = self.KEY_MAPPINGS.get(expected_key, [expected_key])
        for alt in alternatives:
            if alt in config:
                return alt
        return None

    def _find_field_value(
        self, 
        item: Dict[str, Any], 
        field_mappings: Dict[str, List[str]], 
        expected_field: str,
        default: Any = None
    ) -> Any:
        """
        Find a field value using alternative field names.
        
        Args:
            item: Dictionary to search in
            field_mappings: Mapping of expected fields to alternatives
            expected_field: The expected field name
            default: Default value if not found
            
        Returns:
            The field value or default
        """
        alternatives = field_mappings.get(expected_field, [expected_field])
        for alt in alternatives:
            if alt in item:
                return item[alt]
        return default

    def normalize_categories(self, raw_categories: List[Any]) -> List[Dict[str, Any]]:
        """
        Normalize a list of categories to the expected format.
        
        Args:
            raw_categories: List of category items in any format
            
        Returns:
            List of normalized category dictionaries
        """
        normalized = []
        
        for i, cat in enumerate(raw_categories):
            if not isinstance(cat, dict):
                # Handle simple string categories
                normalized.append({
                    'id': str(cat).lower().replace(' ', '_'),
                    'name': str(cat),
                    'keywords': [str(cat).lower()],
                    'description': '',
                    'subcategories': []
                })
                continue
            
            # Find and map fields
            cat_id = self._find_field_value(cat, self.CATEGORY_FIELD_MAPPINGS, 'id')
            cat_name = self._find_field_value(cat, self.CATEGORY_FIELD_MAPPINGS, 'name')
            
            # Generate ID from name if not present
            if not cat_id:
                if cat_name:
                    cat_id = cat_name.lower().replace(' ', '_').replace('-', '_')
                else:
                    cat_id = f"category_{i}"
            
            # Use ID as name if name not present
            if not cat_name:
                cat_name = cat_id.replace('_', ' ').title()
            
            # Get keywords
            keywords = self._find_field_value(cat, self.CATEGORY_FIELD_MAPPINGS, 'keywords', [])
            if not keywords and cat_name:
                # Generate basic keywords from name
                keywords = [cat_name.lower()]
            
            normalized.append({
                'id': cat_id,
                'name': cat_name,
                'description': self._find_field_value(cat, self.CATEGORY_FIELD_MAPPINGS, 'description', ''),
                'keywords': keywords if isinstance(keywords, list) else [keywords],
                'subcategories': self._find_field_value(cat, self.CATEGORY_FIELD_MAPPINGS, 'subcategories', [])
            })
        
        return normalized

    def normalize_severity_rules(self, raw_severity: Any) -> Dict[str, Any]:
        """
        Normalize severity rules to the expected format.
        
        Args:
            raw_severity: Raw severity configuration (dict or list)
            
        Returns:
            Normalized severity rules dictionary
        """
        normalized = {}
        
        if not raw_severity:
            # Return default severity rules
            return self._get_default_severity_rules()
        
        if isinstance(raw_severity, dict):
            for key, value in raw_severity.items():
                # Map the severity level name
                normalized_level = self._map_severity_level(key)
                
                if isinstance(value, dict):
                    normalized[normalized_level] = {
                        'score': self._find_field_value(value, self.SEVERITY_FIELD_MAPPINGS, 'score', 
                                                        self._get_default_score(normalized_level)),
                        'keywords': self._find_field_value(value, self.SEVERITY_FIELD_MAPPINGS, 'keywords', []),
                        'conditions': self._find_field_value(value, self.SEVERITY_FIELD_MAPPINGS, 'conditions', [])
                    }
                elif isinstance(value, (int, float)):
                    # Simple score value
                    normalized[normalized_level] = {
                        'score': int(value),
                        'keywords': [],
                        'conditions': []
                    }
                elif isinstance(value, list):
                    # List of keywords
                    normalized[normalized_level] = {
                        'score': self._get_default_score(normalized_level),
                        'keywords': value,
                        'conditions': []
                    }
        elif isinstance(raw_severity, list):
            # List format - try to extract levels
            for item in raw_severity:
                if isinstance(item, dict):
                    level_name = item.get('level') or item.get('name') or item.get('type', 'medium')
                    normalized_level = self._map_severity_level(str(level_name))
                    normalized[normalized_level] = {
                        'score': item.get('score', self._get_default_score(normalized_level)),
                        'keywords': item.get('keywords', []),
                        'conditions': item.get('conditions', [])
                    }
        
        # Ensure all standard levels exist
        for level in ['critical', 'high', 'medium', 'low', 'minimal']:
            if level not in normalized:
                normalized[level] = {
                    'score': self._get_default_score(level),
                    'keywords': [],
                    'conditions': []
                }
        
        return normalized

    def _map_severity_level(self, level: str) -> str:
        """Map a severity level name to the standard name."""
        level_lower = level.lower().strip()
        for standard, alternatives in self.SEVERITY_LEVEL_MAPPINGS.items():
            if level_lower in alternatives or level_lower == standard:
                return standard
        # Default mapping based on keywords
        if 'crit' in level_lower or 'emer' in level_lower:
            return 'critical'
        elif 'high' in level_lower or 'major' in level_lower:
            return 'high'
        elif 'low' in level_lower or 'minor' in level_lower:
            return 'low'
        elif 'min' in level_lower or 'triv' in level_lower:
            return 'minimal'
        return 'medium'

    def _get_default_score(self, level: str) -> int:
        """Get default score for a severity level."""
        scores = {'critical': 5, 'high': 4, 'medium': 3, 'low': 2, 'minimal': 1}
        return scores.get(level, 3)

    def _get_default_severity_rules(self) -> Dict[str, Any]:
        """Return default severity rules."""
        return {
            'critical': {'score': 5, 'keywords': ['emergency', 'critical', 'urgent'], 'conditions': []},
            'high': {'score': 4, 'keywords': ['important', 'high priority'], 'conditions': []},
            'medium': {'score': 3, 'keywords': ['issue', 'problem'], 'conditions': []},
            'low': {'score': 2, 'keywords': ['minor', 'low priority'], 'conditions': []},
            'minimal': {'score': 1, 'keywords': ['info', 'question'], 'conditions': []}
        }

    def normalize_routing_rules(self, raw_routing: Any) -> List[Dict[str, Any]]:
        """
        Normalize routing rules to the expected format.
        
        Args:
            raw_routing: Raw routing configuration (list or dict)
            
        Returns:
            List of normalized routing rule dictionaries
        """
        normalized = []
        
        if not raw_routing:
            # Return default routing rule
            return self._get_default_routing_rules()
        
        # Convert dict to list if needed
        if isinstance(raw_routing, dict):
            raw_routing = [{'name': k, **v} if isinstance(v, dict) else {'name': k} 
                          for k, v in raw_routing.items()]
        
        if not isinstance(raw_routing, list):
            return self._get_default_routing_rules()
        
        has_default = False
        
        for rule in raw_routing:
            if not isinstance(rule, dict):
                continue
            
            name = self._find_field_value(rule, self.ROUTING_FIELD_MAPPINGS, 'name', 'general_team')
            display_name = self._find_field_value(rule, self.ROUTING_FIELD_MAPPINGS, 'display_name')
            if not display_name:
                display_name = name.replace('_', ' ').title()
            
            # Handle conditions
            conditions = self._find_field_value(rule, self.ROUTING_FIELD_MAPPINGS, 'conditions', {})
            if isinstance(conditions, list):
                # Convert list of categories to proper format
                conditions = {'categories': conditions}
            elif not isinstance(conditions, dict):
                conditions = {}
            
            # Check for alternative condition formats
            for_types = rule.get('for_types') or rule.get('handles') or rule.get('for_categories')
            if for_types and 'categories' not in conditions:
                conditions['categories'] = for_types if isinstance(for_types, list) else [for_types]
            
            if conditions.get('default'):
                has_default = True
            
            normalized.append({
                'name': name,
                'display_name': display_name,
                'conditions': conditions,
                'sla_hours': self._find_field_value(rule, self.ROUTING_FIELD_MAPPINGS, 'sla_hours', 24),
                'escalation_path': self._find_field_value(rule, self.ROUTING_FIELD_MAPPINGS, 'escalation_path', 'supervisor'),
                'notes': self._find_field_value(rule, self.ROUTING_FIELD_MAPPINGS, 'notes')
            })
        
        # Ensure there's a default rule
        if not has_default:
            normalized.append({
                'name': 'general_intake',
                'display_name': 'General Intake Queue',
                'conditions': {'default': True},
                'sla_hours': 48,
                'escalation_path': 'supervisor',
                'notes': None
            })
        
        return normalized

    def _get_default_routing_rules(self) -> List[Dict[str, Any]]:
        """Return default routing rules."""
        return [{
            'name': 'general_intake',
            'display_name': 'General Intake Queue',
            'conditions': {'default': True},
            'sla_hours': 48,
            'escalation_path': 'supervisor',
            'notes': None
        }]

    def normalize_risk_flags(self, raw_flags: Any) -> Dict[str, List[str]]:
        """
        Normalize risk flags to the expected format.
        
        Args:
            raw_flags: Raw risk flags configuration
            
        Returns:
            Normalized risk flags dictionary
        """
        if not raw_flags:
            return {}
        
        if isinstance(raw_flags, dict):
            normalized = {}
            for key, value in raw_flags.items():
                if isinstance(value, list):
                    normalized[key] = value
                elif isinstance(value, str):
                    normalized[key] = [value]
            return normalized
        
        if isinstance(raw_flags, list):
            # Convert list to dict with generic key
            return {'general': raw_flags}
        
        return {}

    def normalize_thresholds(self, raw_thresholds: Any) -> Dict[str, Any]:
        """
        Normalize sampling thresholds to the expected format.
        
        Args:
            raw_thresholds: Raw thresholds configuration
            
        Returns:
            Normalized thresholds dictionary
        """
        defaults = {
            'confidence_for_auto_route': 0.85,
            'confidence_for_hitl': 0.6,
            'high_risk_always_review': True
        }
        
        if not raw_thresholds or not isinstance(raw_thresholds, dict):
            return defaults
        
        # Map alternative keys
        threshold_mappings = {
            'confidence_for_auto_route': ['confidence_for_auto_route', 'auto_route', 'auto_route_threshold', 'auto_confidence'],
            'confidence_for_hitl': ['confidence_for_hitl', 'hitl', 'human_review', 'review_threshold'],
            'high_risk_always_review': ['high_risk_always_review', 'always_review_high_risk', 'review_high_risk']
        }
        
        result = defaults.copy()
        for expected, alternatives in threshold_mappings.items():
            for alt in alternatives:
                if alt in raw_thresholds:
                    result[expected] = raw_thresholds[alt]
                    break
        
        # Include any extra thresholds
        for key, value in raw_thresholds.items():
            if key not in result:
                result[key] = value
        
        return result

    def normalize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize any configuration to the expected format.
        
        This is the main entry point for normalizing configurations.
        It handles both standard and non-standard formats.
        
        Args:
            config: Configuration dictionary in any format
            
        Returns:
            Normalized configuration dictionary
        """
        # If already in standard format, return as-is (with minor fixes if needed)
        if self.is_standard_format(config):
            logger.info("Configuration is already in standard format")
            return config
        
        logger.info("Normalizing non-standard configuration format")
        
        # Detect schema
        schema_mapping = self.detect_schema(config)
        logger.debug(f"Detected schema mapping: {schema_mapping}")
        
        # Find industry/domain name
        industry_key = self._find_mapped_key(config, 'industry')
        industry = config.get(industry_key, 'generic') if industry_key else 'generic'
        
        # Normalize categories
        categories_key = self._find_mapped_key(config, 'categories')
        raw_categories = config.get(categories_key, []) if categories_key else []
        categories = self.normalize_categories(raw_categories)
        
        # Normalize severity rules
        severity_key = self._find_mapped_key(config, 'severity_rules')
        raw_severity = config.get(severity_key, {}) if severity_key else {}
        severity_rules = self.normalize_severity_rules(raw_severity)
        
        # Normalize routing rules
        routing_key = self._find_mapped_key(config, 'routing_rules')
        raw_routing = config.get(routing_key, []) if routing_key else []
        routing_rules = self.normalize_routing_rules(raw_routing)
        
        # Normalize risk flags
        risk_key = self._find_mapped_key(config, 'risk_flags')
        raw_risks = config.get(risk_key, {}) if risk_key else {}
        risk_flags = self.normalize_risk_flags(raw_risks)
        
        # Normalize thresholds
        threshold_key = self._find_mapped_key(config, 'sampling_thresholds')
        raw_thresholds = config.get(threshold_key, {}) if threshold_key else {}
        sampling_thresholds = self.normalize_thresholds(raw_thresholds)
        
        # Build normalized config
        normalized = {
            'industry': industry,
            'name': config.get('name', f'{industry.title()} Configuration'),
            'description': config.get('description', f'Configuration for {industry}'),
            'categories': categories,
            'severity_rules': severity_rules,
            'risk_flags': risk_flags,
            'routing_rules': routing_rules,
            'sampling_thresholds': sampling_thresholds
        }
        
        logger.info(f"Normalized config: {len(categories)} categories, "
                   f"{len(routing_rules)} routing rules")
        
        return normalized

    def discover_schema_via_llm(self, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Use LLM to discover schema mapping for unknown configurations.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dictionary mapping config keys to expected keys
        """
        llm = self._get_llm_client()
        if not llm or not llm.api_key:
            logger.warning("LLM not available for schema discovery")
            return {}
        
        # Build prompt with config structure
        config_structure = json.dumps(
            {k: type(v).__name__ for k, v in config.items()},
            indent=2
        )
        
        prompt = f"""Analyze this configuration structure and map each key to one of these expected keys:
- industry (domain/sector identifier)
- categories (list of classification categories)
- severity_rules (priority/urgency levels)
- routing_rules (team/queue assignments)
- risk_flags (warning indicators)
- sampling_thresholds (confidence settings)

Configuration structure:
{config_structure}

Sample of first category if available:
{json.dumps(config.get(list(config.keys())[0]) if config else {}, indent=2)[:500]}

Respond with a JSON object mapping source keys to target keys.
Example: {{"complaint_types": "categories", "priority_levels": "severity_rules"}}
Only include keys that clearly map to one of the expected keys."""

        try:
            client = llm._get_client()
            response = client.chat.completions.create(
                model=llm.model,
                messages=[
                    {"role": "system", "content": "You are a schema mapping assistant. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            return json.loads(result_text)
        except Exception as e:
            logger.error(f"LLM schema discovery failed: {e}")
            return {}


# Global singleton instance
_yaml_adapter: Optional[GenericYAMLAdapter] = None


def get_yaml_adapter() -> GenericYAMLAdapter:
    """Get the global YAML adapter instance."""
    global _yaml_adapter
    if _yaml_adapter is None:
        _yaml_adapter = GenericYAMLAdapter()
    return _yaml_adapter
