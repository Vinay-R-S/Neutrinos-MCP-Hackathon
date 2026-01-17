"""
Adapters Module
Provides adapters for handling various configuration formats.
"""

from .generic_yaml_adapter import GenericYAMLAdapter, get_yaml_adapter

__all__ = ['GenericYAMLAdapter', 'get_yaml_adapter']
