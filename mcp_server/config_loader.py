"""
Configuration Loader Module
Handles loading and managing YAML/JSON configuration files for different industries.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache


class ConfigLoader:
    """Load and manage industry configuration files."""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration loader.

        Args:
            config_dir: Path to the configuration directory. Defaults to ../configs/
        """
        if config_dir is None:
            # Default to configs directory relative to this file
            self.config_dir = Path(__file__).parent.parent / "configs"
        else:
            self.config_dir = Path(config_dir)

        self._cache: Dict[str, Dict[str, Any]] = {}

    def list_industries(self) -> List[str]:
        """
        List all available industry configurations.

        Returns:
            List of industry names (without file extensions)
        """
        industries = []
        for file in self.config_dir.glob("*.yaml"):
            industries.append(file.stem)
        for file in self.config_dir.glob("*.yml"):
            if file.stem not in industries:
                industries.append(file.stem)
        for file in self.config_dir.glob("*.json"):
            if file.stem not in industries:
                industries.append(file.stem)
        return sorted(industries)

    def load_config(self, industry: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load configuration for a specific industry.

        Args:
            industry: Industry name (e.g., 'banking', 'healthcare')
            force_reload: If True, bypass cache and reload from file

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration file is invalid
        """
        if not force_reload and industry in self._cache:
            return self._cache[industry]

        config = self._load_file(industry)
        self._validate_config(config, industry)
        self._cache[industry] = config
        return config

    def _load_file(self, industry: str) -> Dict[str, Any]:
        """Load configuration file (YAML or JSON)."""
        # Try YAML first
        yaml_path = self.config_dir / f"{industry}.yaml"
        yml_path = self.config_dir / f"{industry}.yml"
        json_path = self.config_dir / f"{industry}.json"

        if yaml_path.exists():
            with open(yaml_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        elif yml_path.exists():
            with open(yml_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        elif json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            available = self.list_industries()
            raise FileNotFoundError(
                f"Configuration for industry '{industry}' not found. "
                f"Available industries: {available}"
            )

    def _validate_config(self, config: Dict[str, Any], industry: str) -> None:
        """Validate configuration structure."""
        required_keys = ['industry', 'categories', 'severity_rules', 'routing_rules']
        missing = [key for key in required_keys if key not in config]
        if missing:
            raise ValueError(
                f"Configuration for '{industry}' is missing required keys: {missing}"
            )

        # Validate categories
        if not isinstance(config['categories'], list) or len(config['categories']) == 0:
            raise ValueError(f"Configuration for '{industry}' must have at least one category")

        # Validate each category has required fields
        for i, category in enumerate(config['categories']):
            cat_required = ['id', 'name', 'keywords']
            cat_missing = [key for key in cat_required if key not in category]
            if cat_missing:
                raise ValueError(
                    f"Category {i} in '{industry}' is missing required keys: {cat_missing}"
                )

    def get_categories(self, industry: str) -> List[Dict[str, Any]]:
        """Get categories for an industry."""
        config = self.load_config(industry)
        return config.get('categories', [])

    def get_severity_rules(self, industry: str) -> Dict[str, Any]:
        """Get severity rules for an industry."""
        config = self.load_config(industry)
        return config.get('severity_rules', {})

    def get_risk_flags(self, industry: str) -> Dict[str, List[str]]:
        """Get risk flag dictionaries for an industry."""
        config = self.load_config(industry)
        return config.get('risk_flags', {})

    def get_routing_rules(self, industry: str) -> List[Dict[str, Any]]:
        """Get routing rules for an industry."""
        config = self.load_config(industry)
        return config.get('routing_rules', [])

    def get_sampling_thresholds(self, industry: str) -> Dict[str, Any]:
        """Get sampling thresholds for an industry."""
        config = self.load_config(industry)
        return config.get('sampling_thresholds', {
            'confidence_for_auto_route': 0.85,
            'confidence_for_hitl': 0.6,
            'high_risk_always_review': True
        })

    def reload_all(self) -> None:
        """Clear cache and reload all configurations."""
        self._cache.clear()


# Global singleton instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """Get the global configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def load_config(industry: str) -> Dict[str, Any]:
    """
    Convenience function to load configuration for an industry.

    Args:
        industry: Industry name (e.g., 'banking', 'healthcare')

    Returns:
        Configuration dictionary
    """
    return get_config_loader().load_config(industry)
