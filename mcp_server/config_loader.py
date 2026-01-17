"""
Configuration Loader Module
Handles loading and managing YAML/JSON configuration files for different industries.
Supports plug-and-play functionality with arbitrary YAML structures via GenericYAMLAdapter.
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Load and manage industry configuration files.
    
    Supports both standard format configurations and arbitrary YAML structures
    through automatic normalization via the GenericYAMLAdapter.
    """

    def __init__(self, config_dir: Optional[str] = None, auto_normalize: bool = True):
        """
        Initialize the configuration loader.

        Args:
            config_dir: Path to the configuration directory. Defaults to ../configs/
            auto_normalize: If True, automatically normalize non-standard configs
                           using GenericYAMLAdapter. Defaults to True for plug-and-play.
        """
        if config_dir is None:
            # Default to configs directory relative to this file
            self.config_dir = Path(__file__).parent.parent / "configs"
        else:
            self.config_dir = Path(config_dir)

        self._cache: Dict[str, Dict[str, Any]] = {}
        self._adapter = None
        self.auto_normalize = auto_normalize

    def _get_adapter(self):
        """Lazily initialize the YAML adapter."""
        if self._adapter is None:
            try:
                from .adapters.generic_yaml_adapter import GenericYAMLAdapter
                self._adapter = GenericYAMLAdapter()
            except ImportError as e:
                logger.warning(f"Could not import GenericYAMLAdapter: {e}")
                self._adapter = None
        return self._adapter

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

    def load_config(
        self, 
        industry: str, 
        force_reload: bool = False,
        use_adapter: bool = None
    ) -> Dict[str, Any]:
        """
        Load configuration for a specific industry.

        This method supports plug-and-play functionality:
        - Standard format configs are loaded directly
        - Non-standard configs are automatically normalized if auto_normalize=True

        Args:
            industry: Industry name (e.g., 'banking', 'healthcare')
            force_reload: If True, bypass cache and reload from file
            use_adapter: Override auto_normalize for this call. 
                        If None, uses self.auto_normalize

        Returns:
            Configuration dictionary (normalized to standard format)

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration file is invalid and cannot be normalized
        """
        if not force_reload and industry in self._cache:
            return self._cache[industry]

        config = self._load_file(industry)
        
        # Determine whether to use adapter for normalization
        should_normalize = use_adapter if use_adapter is not None else self.auto_normalize
        
        # Try standard validation first
        try:
            self._validate_config(config, industry)
            # Config is valid as-is
            self._cache[industry] = config
            return config
        except ValueError as e:
            # Config doesn't match standard format
            if should_normalize:
                logger.info(f"Config '{industry}' is non-standard, attempting normalization...")
                config = self._normalize_config(config, industry)
                # Validate normalized config
                self._validate_config(config, industry)
                self._cache[industry] = config
                return config
            else:
                # Re-raise the validation error
                raise

    def load_generic_config(
        self, 
        file_path: str,
        industry_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load and normalize any YAML/JSON configuration file.
        
        This is the primary method for plug-and-play functionality.
        It can load arbitrary YAML files from any location and normalize them.

        Args:
            file_path: Path to the YAML/JSON configuration file
            industry_name: Optional name to use as industry identifier.
                          If not provided, extracted from filename.

        Returns:
            Normalized configuration dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed or normalized
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Determine industry name
        if industry_name is None:
            industry_name = path.stem
        
        # Load the file
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            elif path.suffix == '.json':
                config = json.load(f)
            else:
                # Try YAML first, then JSON
                content = f.read()
                try:
                    config = yaml.safe_load(content)
                except yaml.YAMLError:
                    config = json.loads(content)
        
        # Normalize the config
        config = self._normalize_config(config, industry_name)
        
        # Cache it
        self._cache[industry_name] = config
        
        return config

    def _normalize_config(self, config: Dict[str, Any], industry: str) -> Dict[str, Any]:
        """
        Normalize a configuration using the GenericYAMLAdapter.
        
        Args:
            config: Raw configuration dictionary
            industry: Industry name for logging
            
        Returns:
            Normalized configuration dictionary
        """
        adapter = self._get_adapter()
        if adapter is None:
            raise ValueError(
                f"Configuration for '{industry}' is non-standard and adapter is not available. "
                "Please ensure the adapters module is properly installed."
            )
        
        try:
            normalized = adapter.normalize_config(config)
            
            # Ensure industry name is set
            if not normalized.get('industry'):
                normalized['industry'] = industry
            
            logger.info(f"Successfully normalized config for '{industry}'")
            return normalized
            
        except Exception as e:
            logger.error(f"Failed to normalize config for '{industry}': {e}")
            raise ValueError(f"Could not normalize configuration for '{industry}': {e}")

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


def get_config_loader(auto_normalize: bool = True) -> ConfigLoader:
    """
    Get the global configuration loader instance.
    
    Args:
        auto_normalize: Enable automatic normalization of non-standard configs.
                       Only used when creating a new instance.
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(auto_normalize=auto_normalize)
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


def load_generic_config(file_path: str, industry_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to load and normalize any YAML configuration.
    
    This is the primary entry point for plug-and-play functionality.

    Args:
        file_path: Path to the YAML/JSON configuration file
        industry_name: Optional name to use as industry identifier

    Returns:
        Normalized configuration dictionary
    """
    return get_config_loader().load_generic_config(file_path, industry_name)
