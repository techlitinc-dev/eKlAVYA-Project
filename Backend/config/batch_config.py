"""
Batch Configuration for Gemini API - Mentor AI Platform

This module provides centralized configuration management for Gemini batch processing,
including environment-based settings, validation, and dynamic configuration updates.

Features:
- Environment-based configuration loading
- Configuration validation and type checking
- Dynamic configuration updates with hot reload
- Batch size optimization algorithms
- Cost optimization settings
- Performance tuning parameters
- Monitoring and alerting configuration
- Feature flags and experimental settings

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from config.batch_config import BatchConfig, get_batch_config
    >>> 
    >>> # Get configuration
    >>> config = get_batch_config()
    >>> 
    >>> # Update settings
    >>> config.update_batch_size(10)
    >>> 
    >>> # Get optimized batch size
    >>> optimal_size = config.get_optimal_batch_size("question_generation")
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import threading
import time

from services.gemini_batch_service import RequestType, RequestPriority

# Configure logging
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_BATCH_SIZE = 5
DEFAULT_BATCH_TIMEOUT = 30
DEFAULT_MAX_BATCH_SIZE = 20
DEFAULT_MIN_BATCH_SIZE = 2
DEFAULT_AUTO_FLUSH = True
DEFAULT_ENABLE_CACHE = True
DEFAULT_ADAPTIVE_BATCHING = True

# Cost optimization defaults
DEFAULT_COST_SAVINGS_TARGET = 0.5  # 50% cost reduction target
DEFAULT_MAX_COST_PER_HOUR = 50.0  # $50/hour limit
DEFAULT_BUDGET_ALERT_THRESHOLD = 0.8  # 80% of budget

# Performance defaults
DEFAULT_PROCESSING_TIMEOUT = 120  # 2 minutes
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_CONCURRENT_BATCHES = 3

# Monitoring defaults
DEFAULT_ENABLE_MONITORING = True
DEFAULT_METRICS_RETENTION_HOURS = 24 * 7  # 1 week
DEFAULT_ALERT_THRESHOLDS = {
    "cost_per_hour": 10.0,
    "batch_failure_rate": 0.1,
    "average_wait_time": 300,
    "queue_utilization": 0.9,
    "batch_size_efficiency": 0.5
}

class ConfigSource(Enum):
    """Configuration source priority."""
    ENVIRONMENT = "environment"
    FILE = "file"
    DEFAULTS = "defaults"

class OptimizationStrategy(Enum):
    """Batch size optimization strategies."""
    COST_OPTIMIZED = "cost_optimized"
    LATENCY_OPTIMIZED = "latency_optimized"
    BALANCED = "balanced"
    THROUGHPUT_OPTIMIZED = "throughput_optimized"

@dataclass
class BatchTypeConfig:
    """Configuration for specific request type."""
    max_batch_size: int
    optimal_batch_size: int
    processing_timeout: int
    retry_attempts: int
    cost_weight: float  # Relative cost importance
    latency_weight: float  # Relative latency importance
    enable_adaptive: bool = True

@dataclass
class BatchConfig:
    """Comprehensive batch configuration."""
    
    # Core batch settings
    batch_size: int = DEFAULT_BATCH_SIZE
    batch_timeout: int = DEFAULT_BATCH_TIMEOUT
    max_batch_size: int = DEFAULT_MAX_BATCH_SIZE
    min_batch_size: int = DEFAULT_MIN_BATCH_SIZE
    auto_flush_enabled: bool = DEFAULT_AUTO_FLUSH
    cache_enabled: bool = DEFAULT_ENABLE_CACHE
    adaptive_batching: bool = DEFAULT_ADAPTIVE_BATCHING
    
    # Cost optimization
    cost_savings_target: float = DEFAULT_COST_SAVINGS_TARGET
    max_cost_per_hour: float = DEFAULT_MAX_COST_PER_HOUR
    budget_alert_threshold: float = DEFAULT_BUDGET_ALERT_THRESHOLD
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    
    # Performance settings
    processing_timeout: int = DEFAULT_PROCESSING_TIMEOUT
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS
    concurrent_batches: int = DEFAULT_CONCURRENT_BATCHES
    enable_compression: bool = True
    
    # Monitoring and alerts
    enable_monitoring: bool = DEFAULT_ENABLE_MONITORING
    metrics_retention_hours: int = DEFAULT_METRICS_RETENTION_HOURS
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: DEFAULT_ALERT_THRESHOLDS.copy())
    enable_real_time_alerts: bool = True
    
    # Request type specific configs
    type_configs: Dict[RequestType, BatchTypeConfig] = field(default_factory=dict)
    
    # Feature flags
    enable_experimental_features: bool = False
    enable_advanced_optimization: bool = True
    enable_predictive_batching: bool = False
    
    # Configuration metadata
    config_source: ConfigSource = ConfigSource.DEFAULTS
    last_updated: datetime = field(default_factory=datetime.now)
    config_version: str = "1.0.0"
    
    def __post_init__(self):
        """Initialize type-specific configurations."""
        if not self.type_configs:
            self.type_configs = {
                RequestType.QUESTION_GENERATION: BatchTypeConfig(
                    max_batch_size=10,
                    optimal_batch_size=5,
                    processing_timeout=60,
                    retry_attempts=2,
                    cost_weight=0.8,
                    latency_weight=0.2
                ),
                RequestType.ANALYTICS_INSIGHTS: BatchTypeConfig(
                    max_batch_size=20,
                    optimal_batch_size=15,
                    processing_timeout=120,
                    retry_attempts=3,
                    cost_weight=0.9,
                    latency_weight=0.1
                ),
                RequestType.SCHEDULE_GENERATION: BatchTypeConfig(
                    max_batch_size=5,
                    optimal_batch_size=3,
                    processing_timeout=180,
                    retry_attempts=2,
                    cost_weight=0.7,
                    latency_weight=0.3
                ),
                RequestType.VECTOR_SEARCH: BatchTypeConfig(
                    max_batch_size=15,
                    optimal_batch_size=8,
                    processing_timeout=30,
                    retry_attempts=1,
                    cost_weight=0.6,
                    latency_weight=0.4
                ),
                RequestType.CONTEXT_RETRIEVAL: BatchTypeConfig(
                    max_batch_size=8,
                    optimal_batch_size=4,
                    processing_timeout=45,
                    retry_attempts=2,
                    cost_weight=0.5,
                    latency_weight=0.5
                )
            }

class BatchConfigManager:
    """
    Manager for batch configuration with validation and hot reload.
    
    This manager handles configuration loading, validation, updates,
    and provides optimized settings based on current conditions.
    
    Attributes:
        config: Current batch configuration
        config_file: Path to configuration file
        auto_reload: Whether to auto-reload config changes
        validation_rules: Configuration validation rules
    
    Example:
        >>> manager = BatchConfigManager()
        >>> config = manager.get_config()
        >>> optimal_size = manager.get_optimal_batch_size(RequestType.QUESTION_GENERATION)
    """
    
    def __init__(
        self,
        config_file: Optional[str] = None,
        auto_reload: bool = True,
        environment_prefix: str = "GEMINI_BATCH_"
    ):
        """
        Initialize Batch Configuration Manager.
        
        Args:
            config_file: Path to JSON config file
            auto_reload: Enable automatic config reloading
            environment_prefix: Prefix for environment variables
        """
        logger.info("Initializing BatchConfigManager")
        
        self.config_file = config_file or "config/batch_settings.json"
        self.auto_reload = auto_reload
        self.environment_prefix = environment_prefix
        
        # Configuration lock for thread safety
        self.config_lock = threading.RLock()
        
        # Load configuration
        self.config = self._load_configuration()
        
        # Start auto-reload if enabled
        if self.auto_reload:
            self._start_auto_reload()
        
        logger.info(
            f"BatchConfigManager initialized (source: {self.config.config_source.value}, "
            f"auto_reload: {auto_reload})"
        )
    
    def get_config(self) -> BatchConfig:
        """
        Get current batch configuration.
        
        Returns:
            Current BatchConfig instance
        
        Example:
            >>> config = manager.get_config()
            >>> print(f"Batch size: {config.batch_size}")
        """
        with self.config_lock:
            return self.config
    
    def get_optimal_batch_size(
        self, 
        request_type: RequestType,
        current_load: float = 0.5,
        strategy: Optional[OptimizationStrategy] = None
    ) -> int:
        """
        Get optimal batch size for request type and conditions.
        
        Args:
            request_type: Type of request
            current_load: Current system load (0.0-1.0)
            strategy: Optimization strategy override
        
        Returns:
            Optimal batch size
        
        Example:
            >>> size = manager.get_optimal_batch_size(
            ...     RequestType.QUESTION_GENERATION, 
            ...     current_load=0.7
            ... )
        """
        with self.config_lock:
            type_config = self.config.type_configs.get(request_type)
            if not type_config:
                return self.config.batch_size
            
            strategy = strategy or self.config.optimization_strategy
            
            base_size = type_config.optimal_batch_size
            
            # Apply strategy-based adjustments
            if strategy == OptimizationStrategy.COST_OPTIMIZED:
                # Maximize batch size for cost efficiency
                optimal = min(type_config.max_batch_size, base_size * 2)
            elif strategy == OptimizationStrategy.LATENCY_OPTIMIZED:
                # Minimize batch size for lower latency
                optimal = max(self.config.min_batch_size, base_size // 2)
            elif strategy == OptimizationStrategy.THROUGHPUT_OPTIMIZED:
                # Balance for maximum throughput
                optimal = type_config.max_batch_size
            else:  # BALANCED
                optimal = base_size
            
            # Apply load-based adjustments
            if current_load > 0.8:  # High load - reduce batch size
                optimal = max(self.config.min_batch_size, int(optimal * 0.7))
            elif current_load < 0.3:  # Low load - can increase batch size
                optimal = min(type_config.max_batch_size, int(optimal * 1.3))
            
            # Apply adaptive batching if enabled
            if self.config.adaptive_batching and type_config.enable_adaptive:
                optimal = self._apply_adaptive_optimization(
                    request_type, optimal, current_load
                )
            
            logger.debug(
                f"Optimal batch size for {request_type.value}: {optimal} "
                f"(strategy: {strategy.value}, load: {current_load:.2f})"
            )
            
            return optimal
    
    def update_batch_size(self, new_size: int, request_type: Optional[RequestType] = None):
        """
        Update batch size configuration.
        
        Args:
            new_size: New batch size
            request_type: Specific request type (None for global)
        
        Example:
            >>> manager.update_batch_size(10, RequestType.QUESTION_GENERATION)
        """
        with self.config_lock:
            if request_type:
                if request_type in self.config.type_configs:
                    old_size = self.config.type_configs[request_type].optimal_batch_size
                    self.config.type_configs[request_type].optimal_batch_size = new_size
                    logger.info(
                        f"Updated {request_type.value} batch size: {old_size} -> {new_size}"
                    )
            else:
                old_size = self.config.batch_size
                self.config.batch_size = new_size
                logger.info(f"Updated global batch size: {old_size} -> {new_size}")
            
            self.config.last_updated = datetime.now()
            
            # Save configuration
            if self.config_file:
                self._save_configuration()
    
    def update_cost_target(self, new_target: float):
        """
        Update cost savings target.
        
        Args:
            new_target: New cost savings target (0.0-1.0)
        
        Example:
            >>> manager.update_cost_target(0.6)  # 60% savings target
        """
        with self.config_lock:
            if not 0.0 <= new_target <= 1.0:
                raise ValueError("Cost savings target must be between 0.0 and 1.0")
            
            old_target = self.config.cost_savings_target
            self.config.cost_savings_target = new_target
            self.config.last_updated = datetime.now()
            
            logger.info(f"Updated cost savings target: {old_target:.2f} -> {new_target:.2f}")
            
            # Save configuration
            if self.config_file:
                self._save_configuration()
    
    def enable_feature(self, feature_name: str, enabled: bool = True):
        """
        Enable or disable a feature flag.
        
        Args:
            feature_name: Name of the feature
            enabled: Whether to enable the feature
        
        Example:
            >>> manager.enable_feature("predictive_batching", True)
        """
        with self.config_lock:
            if hasattr(self.config, feature_name):
                setattr(self.config, feature_name, enabled)
                self.config.last_updated = datetime.now()
                
                logger.info(f"Feature '{feature_name}' {'enabled' if enabled else 'disabled'}")
                
                # Save configuration
                if self.config_file:
                    self._save_configuration()
            else:
                logger.warning(f"Unknown feature: {feature_name}")
    
    def validate_configuration(self) -> List[str]:
        """
        Validate current configuration.
        
        Returns:
            List of validation errors (empty if valid)
        
        Example:
            >>> errors = manager.validate_configuration()
            >>> if errors:
            ...     print(f"Configuration errors: {errors}")
        """
        errors = []
        
        with self.config_lock:
            # Ensure config is loaded
            if not hasattr(self, 'config') or self.config is None:
                return ["Configuration not loaded"]
            
            # Validate core settings
            if self.config.batch_size < self.config.min_batch_size:
                errors.append("batch_size cannot be less than min_batch_size")
            
            if self.config.batch_size > self.config.max_batch_size:
                errors.append("batch_size cannot be greater than max_batch_size")
            
            if self.config.batch_timeout <= 0:
                errors.append("batch_timeout must be positive")
            
            if self.config.processing_timeout <= 0:
                errors.append("processing_timeout must be positive")
            
            # Validate cost settings
            if not 0.0 <= self.config.cost_savings_target <= 1.0:
                errors.append("cost_savings_target must be between 0.0 and 1.0")
            
            if self.config.max_cost_per_hour <= 0:
                errors.append("max_cost_per_hour must be positive")
            
            # Validate type-specific configs
            for request_type, type_config in self.config.type_configs.items():
                if type_config.max_batch_size < type_config.optimal_batch_size:
                    errors.append(
                        f"{request_type.value}: max_batch_size must be >= optimal_batch_size"
                    )
                
                if type_config.optimal_batch_size < self.config.min_batch_size:
                    errors.append(
                        f"{request_type.value}: optimal_batch_size must be >= min_batch_size"
                    )
                
                if type_config.processing_timeout <= 0:
                    errors.append(
                        f"{request_type.value}: processing_timeout must be positive"
                    )
        
        return errors
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get summary of current configuration.
        
        Returns:
            Dictionary with configuration summary
        
        Example:
            >>> summary = manager.get_configuration_summary()
            >>> print(f"Config version: {summary['version']}")
        """
        with self.config_lock:
            return {
                "version": self.config.config_version,
                "source": self.config.config_source.value,
                "last_updated": self.config.config.last_updated.isoformat(),
                "core_settings": {
                    "batch_size": self.config.batch_size,
                    "batch_timeout": self.config.batch_timeout,
                    "auto_flush_enabled": self.config.auto_flush_enabled,
                    "adaptive_batching": self.config.adaptive_batching
                },
                "cost_optimization": {
                    "cost_savings_target": self.config.cost_savings_target,
                    "max_cost_per_hour": self.config.max_cost_per_hour,
                    "optimization_strategy": self.config.optimization_strategy.value
                },
                "performance_settings": {
                    "processing_timeout": self.config.processing_timeout,
                    "concurrent_batches": self.config.concurrent_batches,
                    "retry_attempts": self.config.retry_attempts
                },
                "monitoring": {
                    "enable_monitoring": self.config.enable_monitoring,
                    "metrics_retention_hours": self.config.metrics_retention_hours,
                    "enable_real_time_alerts": self.config.enable_real_time_alerts
                },
                "type_configs": {
                    req_type.value: {
                        "optimal_batch_size": type_config.optimal_batch_size,
                        "max_batch_size": type_config.max_batch_size,
                        "processing_timeout": type_config.processing_timeout
                    }
                    for req_type, type_config in self.config.type_configs.items()
                },
                "feature_flags": {
                    "enable_experimental_features": self.config.enable_experimental_features,
                    "enable_advanced_optimization": self.config.enable_advanced_optimization,
                    "enable_predictive_batching": self.config.enable_predictive_batching
                }
            }
    
    def _load_configuration(self) -> BatchConfig:
        """Load configuration from multiple sources."""
        # Start with defaults
        config = BatchConfig()
        
        # Try to load from file
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                
                # Update config with file values
                self._update_config_from_dict(config, file_config)
                config.config_source = ConfigSource.FILE
                logger.info(f"Loaded configuration from {self.config_file}")
                
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
        
        # Override with environment variables
        env_config = self._load_from_environment()
        if env_config:
            self._update_config_from_dict(config, env_config)
            if config.config_source == ConfigSource.DEFAULTS:
                config.config_source = ConfigSource.ENVIRONMENT
            elif config.config_source == ConfigSource.FILE:
                # Keep file as primary source, note env overrides
                logger.info("Applied environment variable overrides")
        
        # Validate configuration
        errors = self.validate_configuration()
        if errors:
            logger.warning(f"Configuration validation errors: {errors}")
        
        return config
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}
        
        # Map environment variables to config keys
        env_mappings = {
            f"{self.environment_prefix}SIZE": ("batch_size", int),
            f"{self.environment_prefix}TIMEOUT": ("batch_timeout", int),
            f"{self.environment_prefix}MAX_SIZE": ("max_batch_size", int),
            f"{self.environment_prefix}MIN_SIZE": ("min_batch_size", int),
            f"{self.environment_prefix}AUTO_FLUSH": ("auto_flush_enabled", bool),
            f"{self.environment_prefix}CACHE": ("cache_enabled", bool),
            f"{self.environment_prefix}ADAPTIVE": ("adaptive_batching", bool),
            f"{self.environment_prefix}COST_TARGET": ("cost_savings_target", float),
            f"{self.environment_prefix}MAX_COST_HOUR": ("max_cost_per_hour", float),
            f"{self.environment_prefix}PROCESSING_TIMEOUT": ("processing_timeout", int),
            f"{self.environment_prefix}RETRY_ATTEMPTS": ("retry_attempts", int),
            f"{self.environment_prefix}CONCURRENT_BATCHES": ("concurrent_batches", int),
            f"{self.environment_prefix}MONITORING": ("enable_monitoring", bool),
            f"{self.environment_prefix}RETENTION_HOURS": ("metrics_retention_hours", int),
            f"{self.environment_prefix}EXPERIMENTAL": ("enable_experimental_features", bool)
        }
        
        for env_var, (config_key, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    if value_type == bool:
                        parsed_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        parsed_value = value_type(env_value)
                    
                    env_config[config_key] = parsed_value
                    logger.debug(f"Loaded from environment: {config_key} = {parsed_value}")
                    
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid environment value {env_var}={env_value}: {e}")
        
        return env_config
    
    def _update_config_from_dict(self, config: BatchConfig, updates: Dict[str, Any]):
        """Update configuration from dictionary."""
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                logger.warning(f"Unknown configuration key: {key}")
    
    def _save_configuration(self):
        """Save current configuration to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Convert config to dictionary
            config_dict = {
                "batch_size": self.config.batch_size,
                "batch_timeout": self.config.batch_timeout,
                "max_batch_size": self.config.max_batch_size,
                "min_batch_size": self.config.min_batch_size,
                "auto_flush_enabled": self.config.auto_flush_enabled,
                "cache_enabled": self.config.cache_enabled,
                "adaptive_batching": self.config.adaptive_batching,
                "cost_savings_target": self.config.cost_savings_target,
                "max_cost_per_hour": self.config.max_cost_per_hour,
                "budget_alert_threshold": self.config.budget_alert_threshold,
                "optimization_strategy": self.config.optimization_strategy.value,
                "processing_timeout": self.config.processing_timeout,
                "retry_attempts": self.config.retry_attempts,
                "concurrent_batches": self.config.concurrent_batches,
                "enable_compression": self.config.enable_compression,
                "enable_monitoring": self.config.enable_monitoring,
                "metrics_retention_hours": self.config.metrics_retention_hours,
                "alert_thresholds": self.config.alert_thresholds,
                "enable_real_time_alerts": self.config.enable_real_time_alerts,
                "enable_experimental_features": self.config.enable_experimental_features,
                "enable_advanced_optimization": self.config.enable_advanced_optimization,
                "enable_predictive_batching": self.config.enable_predictive_batching,
                "type_configs": {
                    req_type.value: {
                        "max_batch_size": type_config.max_batch_size,
                        "optimal_batch_size": type_config.optimal_batch_size,
                        "processing_timeout": type_config.processing_timeout,
                        "retry_attempts": type_config.retry_attempts,
                        "cost_weight": type_config.cost_weight,
                        "latency_weight": type_config.latency_weight,
                        "enable_adaptive": type_config.enable_adaptive
                    }
                    for req_type, type_config in self.config.type_configs.items()
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.debug(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def _apply_adaptive_optimization(
        self, 
        request_type: RequestType, 
        base_size: int, 
        current_load: float
    ) -> int:
        """Apply adaptive optimization based on historical performance."""
        # This would integrate with monitoring service to get historical data
        # For now, apply simple load-based adjustment
        
        if current_load > 0.9:  # Very high load
            return max(self.config.min_batch_size, base_size // 2)
        elif current_load > 0.7:  # High load
            return max(self.config.min_batch_size, int(base_size * 0.8))
        elif current_load < 0.2:  # Very low load
            return min(self.config.type_configs[request_type].max_batch_size, base_size * 2)
        else:
            return base_size
    
    def _start_auto_reload(self):
        """Start automatic configuration reloading."""
        def reload_loop():
            last_modified = 0
            
            while True:
                try:
                    if os.path.exists(self.config_file):
                        current_modified = os.path.getmtime(self.config_file)
                        
                        if current_modified > last_modified:
                            logger.info("Configuration file changed, reloading...")
                            
                            with self.config_lock:
                                self.config = self._load_configuration()
                            
                            last_modified = current_modified
                    
                    time.sleep(5)  # Check every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Auto-reload error: {e}")
                    time.sleep(30)  # Wait longer on error
        
        reload_thread = threading.Thread(target=reload_loop, daemon=True)
        reload_thread.start()
        logger.info("Auto-reload started")

# Global configuration manager instance
_config_manager_instance: Optional[BatchConfigManager] = None

def get_batch_config(**kwargs) -> BatchConfigManager:
    """
    Get or create singleton BatchConfigManager instance.
    
    Args:
        **kwargs: Arguments to pass to BatchConfigManager constructor
    
    Returns:
        BatchConfigManager instance
    
    Example:
        >>> manager = get_batch_config(config_file="custom_batch.json")
        >>> config = manager.get_config()
    """
    global _config_manager_instance
    
    if _config_manager_instance is None:
        logger.info("Creating new BatchConfigManager singleton instance")
        _config_manager_instance = BatchConfigManager(**kwargs)
    
    return _config_manager_instance

def get_batch_settings() -> BatchConfig:
    """
    Convenience function to get current batch configuration.
    
    Returns:
        Current BatchConfig instance
    
    Example:
        >>> settings = get_batch_settings()
        >>> print(f"Batch size: {settings.batch_size}")
    """
    manager = get_batch_config()
    return manager.get_config()

# Module initialization
logger.info("Batch configuration module loaded")
logger.info(f"Default batch size: {DEFAULT_BATCH_SIZE}")
logger.info(f"Default timeout: {DEFAULT_BATCH_TIMEOUT}s")