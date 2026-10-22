"""
Analytics Parser for Gemini Analytics Responses - Mentor AI Platform.

This module provides parsing and validation of Gemini-generated analytics responses.
It handles various response formats, extracts JSON content, validates structure,
and converts to Pydantic models.

Features:
- Multiple parsing strategies (direct JSON, markdown extraction, regex patterns)
- Robust error handling with recovery strategies
- JSON repair for common formatting issues
- Field validation with type conversion
- Default value injection for missing fields
- Comprehensive logging for debugging
- Pydantic model validation

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from utils.analytics_parser import AnalyticsParser
    >>> 
    >>> parser = AnalyticsParser()
    >>> analytics = parser.parse_response(gemini_response_text)
    >>> 
    >>> print(f"Strengths: {len(analytics.strengths)}")
    >>> print(f"Weaknesses: {len(analytics.weaknesses)}")
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ValidationError

# Configure logging
logger = logging.getLogger(__name__)


class PriorityLevel(str, Enum):
    """Priority levels for improvement areas."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AnalyticsParserError(Exception):
    """Base exception for analytics parser errors."""
    pass


class AnalyticsStrength(BaseModel):
    """
    Identified strength area.
    
    Attributes:
        topic: Topic name
        subject: Subject name
        accuracy: Accuracy percentage (0-100)
        reason: Explanation of why this is a strength
        recommendation: Recommendation to maintain/leverage strength
    """
    topic: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject name")
    accuracy: float = Field(..., ge=0.0, le=100.0, description="Accuracy percentage")
    reason: str = Field(..., description="Reason for strength")
    recommendation: str = Field(..., description="Recommendation")
    
    @field_validator('accuracy')
    @classmethod
    def validate_accuracy(cls, v: float) -> float:
        """Ensure accuracy is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError(f"Accuracy must be between 0 and 100, got {v}")
        return v


class AnalyticsWeakness(BaseModel):
    """
    Identified weakness area.
    
    Attributes:
        topic: Topic name
        subject: Subject name
        accuracy: Accuracy percentage (0-100)
        reason: Root cause explanation
        priority: Priority level (HIGH/MEDIUM/LOW)
        estimated_study_hours: Estimated hours needed for improvement
        recommendation: Specific actionable recommendations
    """
    topic: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject name")
    accuracy: float = Field(..., ge=0.0, le=100.0, description="Accuracy percentage")
    reason: str = Field(..., description="Reason for weakness")
    priority: PriorityLevel = Field(..., description="Priority level")
    estimated_study_hours: float = Field(..., ge=0.0, description="Estimated study hours")
    recommendation: str = Field(..., description="Specific recommendations")
    
    @field_validator('accuracy')
    @classmethod
    def validate_accuracy(cls, v: float) -> float:
        """Ensure accuracy is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError(f"Accuracy must be between 0 and 100, got {v}")
        return v
    
    @field_validator('priority', mode='before')
    @classmethod
    def normalize_priority(cls, v: Union[str, PriorityLevel]) -> str:
        """Normalize priority to uppercase."""
        if isinstance(v, str):
            return v.upper()
        return v


class AnalyticsInsights(BaseModel):
    """
    Complete analytics insights from performance analysis.
    
    Attributes:
        strengths: List of identified strength areas
        weaknesses: List of identified weakness areas
        learning_patterns: List of detected learning patterns
        overall_assessment: Comprehensive assessment summary
        study_strategy: Detailed study plan and recommendations
        metadata: Optional metadata about the analytics
    """
    strengths: List[AnalyticsStrength] = Field(
        default_factory=list,
        description="Identified strength areas"
    )
    weaknesses: List[AnalyticsWeakness] = Field(
        default_factory=list,
        description="Identified weakness areas"
    )
    learning_patterns: List[str] = Field(
        default_factory=list,
        description="Detected learning patterns"
    )
    overall_assessment: str = Field(
        default="",
        description="Overall performance assessment"
    )
    study_strategy: str = Field(
        default="",
        description="Recommended study strategy"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )
    
    @field_validator('learning_patterns')
    @classmethod
    def validate_patterns(cls, v: List[str]) -> List[str]:
        """Ensure learning patterns are non-empty strings."""
        return [p.strip() for p in v if p and p.strip()]


class AnalyticsParser:
    """
    Parser for Gemini analytics responses.
    
    This class handles parsing and validation of LLM responses containing
    educational analytics. It can handle various response formats and
    attempts multiple parsing strategies.
    
    Attributes:
        strict_mode: If True, raises exceptions on validation errors
        allow_partial: If True, returns partial results on missing fields
        log_issues: If True, logs parsing issues for debugging
    
    Example:
        >>> parser = AnalyticsParser()
        >>> analytics = parser.parse_response(gemini_text)
        >>> print(f"Found {len(analytics.weaknesses)} weaknesses")
    """
    
    def __init__(
        self,
        strict_mode: bool = False,
        allow_partial: bool = True,
        log_issues: bool = True
    ):
        """
        Initialize AnalyticsParser.
        
        Args:
            strict_mode: Raise exceptions on validation errors (default: False)
            allow_partial: Return partial results on missing fields (default: True)
            log_issues: Log parsing issues for debugging (default: True)
        """
        self.strict_mode = strict_mode
        self.allow_partial = allow_partial
        self.log_issues = log_issues
        
        logger.info(
            f"AnalyticsParser initialized (strict={strict_mode}, "
            f"partial={allow_partial}, log={log_issues})"
        )
    
    def parse_response(self, text: str) -> AnalyticsInsights:
        """
        Parse Gemini analytics response and return validated insights.
        
        Attempts multiple parsing strategies:
        1. Direct JSON parse
        2. Extract from markdown code blocks
        3. Extract JSON object from text using regex
        4. Attempt JSON repair for common issues
        
        Args:
            text: Raw response text from Gemini
        
        Returns:
            Validated AnalyticsInsights object
        
        Raises:
            AnalyticsParserError: If strict_mode=True and parsing fails
        
        Example:
            >>> analytics = parser.parse_response(gemini_response)
            >>> for weakness in analytics.weaknesses:
            ...     print(f"{weakness.topic}: {weakness.priority}")
        """
        logger.info("Starting analytics response parsing")
        
        if not text or not text.strip():
            logger.error("Empty response text provided")
            if self.strict_mode:
                raise AnalyticsParserError("Response text cannot be empty")
            return AnalyticsInsights()
        
        try:
            # Strategy 1: Try direct JSON parse
            analytics_dict = self._try_direct_parse(text)
            
            if analytics_dict is None:
                # Strategy 2: Extract from markdown code blocks
                analytics_dict = self._extract_from_markdown(text)
            
            if analytics_dict is None:
                # Strategy 3: Extract JSON object using regex
                analytics_dict = self._extract_json_object(text)
            
            if analytics_dict is None:
                # Strategy 4: Try to repair JSON
                analytics_dict = self._try_repair_json(text)
            
            if analytics_dict is None:
                logger.error("All parsing strategies failed")
                if self.strict_mode:
                    raise AnalyticsParserError("Failed to parse JSON from response")
                return AnalyticsInsights()
            
            # Validate and convert to Pydantic model
            analytics = self._validate_and_build(analytics_dict)
            
            logger.info(
                f"Parsing successful: {len(analytics.strengths)} strengths, "
                f"{len(analytics.weaknesses)} weaknesses, "
                f"{len(analytics.learning_patterns)} patterns"
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Unexpected error during parsing: {str(e)}")
            if self.log_issues:
                logger.exception("Full traceback:")
            
            if self.strict_mode:
                raise AnalyticsParserError(f"Failed to parse response: {str(e)}")
            
            return AnalyticsInsights()
    
    def _try_direct_parse(self, text: str) -> Optional[Dict[str, Any]]:
        """Try to parse text directly as JSON."""
        try:
            data = json.loads(text.strip())
            logger.debug("Direct JSON parse successful")
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            logger.debug("Direct JSON parse failed")
            return None
    
    def _extract_from_markdown(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from markdown code blocks."""
        try:
            # Remove markdown code block markers
            patterns = [
                r'```json\s*\n?(.*?)\n?```',  # ```json ... ```
                r'```\s*\n?(.*?)\n?```',       # ``` ... ```
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    json_text = match.group(1).strip()
                    try:
                        data = json.loads(json_text)
                        logger.debug("Markdown extraction successful")
                        return data if isinstance(data, dict) else None
                    except json.JSONDecodeError:
                        continue
            
            logger.debug("Markdown extraction failed")
            return None
            
        except Exception as e:
            logger.debug(f"Markdown extraction error: {str(e)}")
            return None
    
    def _extract_json_object(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from text using regex."""
        try:
            # Find JSON object pattern
            match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
            
            if not match:
                # Try to find the first { and last }
                start = text.find('{')
                end = text.rfind('}')
                
                if start != -1 and end != -1 and end > start:
                    json_text = text[start:end+1]
                else:
                    logger.debug("No JSON object found in text")
                    return None
            else:
                json_text = match.group(0)
            
            data = json.loads(json_text)
            logger.debug("Regex extraction successful")
            return data if isinstance(data, dict) else None
            
        except Exception as e:
            logger.debug(f"Regex extraction error: {str(e)}")
            return None
    
    def _try_repair_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Attempt to repair common JSON formatting issues."""
        try:
            # Extract potential JSON content
            start = text.find('{')
            end = text.rfind('}')
            
            if start == -1 or end == -1 or end <= start:
                return None
            
            json_text = text[start:end+1]
            
            # Common repairs
            repairs = [
                # Fix unescaped quotes in strings
                lambda s: re.sub(r'(?<!\\)"(?=[^,:}\]]*[,:}\]])', r'\"', s),
                # Fix trailing commas
                lambda s: re.sub(r',\s*([}\]])', r'\1', s),
                # Fix single quotes (convert to double quotes)
                lambda s: s.replace("'", '"'),
                # Fix missing commas between array items
                lambda s: re.sub(r'"\s*"', '","', s),
            ]
            
            for repair_func in repairs:
                try:
                    repaired = repair_func(json_text)
                    data = json.loads(repaired)
                    logger.debug("JSON repair successful")
                    return data if isinstance(data, dict) else None
                except:
                    continue
            
            logger.debug("JSON repair failed")
            return None
            
        except Exception as e:
            logger.debug(f"JSON repair error: {str(e)}")
            return None
    
    def _validate_and_build(self, data: Dict[str, Any]) -> AnalyticsInsights:
        """
        Validate dictionary data and build AnalyticsInsights object.
        
        Args:
            data: Parsed dictionary from JSON
        
        Returns:
            Validated AnalyticsInsights object
        
        Raises:
            AnalyticsParserError: If validation fails in strict mode
        """
        try:
            # Apply defaults for missing required fields
            if self.allow_partial:
                data = self._apply_defaults(data)
            
            # Convert and validate individual sections
            strengths = self._parse_strengths(data.get('strengths', []))
            weaknesses = self._parse_weaknesses(data.get('weaknesses', []))
            patterns = data.get('learning_patterns', [])
            assessment = data.get('overall_assessment', '')
            strategy = data.get('study_strategy', '')
            metadata = data.get('metadata')
            
            # Build AnalyticsInsights object
            analytics = AnalyticsInsights(
                strengths=strengths,
                weaknesses=weaknesses,
                learning_patterns=patterns if isinstance(patterns, list) else [],
                overall_assessment=assessment if isinstance(assessment, str) else '',
                study_strategy=strategy if isinstance(strategy, str) else '',
                metadata=metadata
            )
            
            logger.debug("Validation and build successful")
            return analytics
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            if self.log_issues:
                logger.error(f"Validation details: {e.errors()}")
            
            if self.strict_mode:
                raise AnalyticsParserError(f"Validation failed: {str(e)}")
            
            # Return partial results
            return AnalyticsInsights(
                strengths=self._parse_strengths(data.get('strengths', [])),
                weaknesses=self._parse_weaknesses(data.get('weaknesses', [])),
                learning_patterns=data.get('learning_patterns', []) if isinstance(data.get('learning_patterns'), list) else [],
                overall_assessment=data.get('overall_assessment', '') if isinstance(data.get('overall_assessment'), str) else '',
                study_strategy=data.get('study_strategy', '') if isinstance(data.get('study_strategy'), str) else ''
            )
    
    def _apply_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing fields."""
        defaults = {
            'strengths': [],
            'weaknesses': [],
            'learning_patterns': [],
            'overall_assessment': 'Analysis completed with limited data.',
            'study_strategy': 'Focus on identified weak areas and build on strengths.'
        }
        
        for key, default_value in defaults.items():
            if key not in data:
                logger.warning(f"Missing field '{key}', using default")
                data[key] = default_value
        
        return data
    
    def _parse_strengths(self, strengths_data: List[Dict[str, Any]]) -> List[AnalyticsStrength]:
        """Parse and validate strengths list."""
        if not isinstance(strengths_data, list):
            logger.warning("Strengths data is not a list")
            return []
        
        validated_strengths = []
        
        for idx, strength_dict in enumerate(strengths_data):
            try:
                # Ensure required fields exist
                if not isinstance(strength_dict, dict):
                    logger.warning(f"Strength {idx}: Not a dictionary")
                    continue
                
                # Convert accuracy to float if needed
                if 'accuracy' in strength_dict:
                    try:
                        strength_dict['accuracy'] = float(strength_dict['accuracy'])
                    except (ValueError, TypeError):
                        logger.warning(f"Strength {idx}: Invalid accuracy value")
                        continue
                
                # Validate required fields
                required = ['topic', 'subject', 'accuracy', 'reason', 'recommendation']
                if not all(field in strength_dict for field in required):
                    missing = [f for f in required if f not in strength_dict]
                    logger.warning(f"Strength {idx}: Missing fields {missing}")
                    continue
                
                strength = AnalyticsStrength(**strength_dict)
                validated_strengths.append(strength)
                
            except ValidationError as e:
                if self.log_issues:
                    logger.warning(f"Strength {idx} validation failed: {str(e)}")
                continue
            except Exception as e:
                if self.log_issues:
                    logger.warning(f"Strength {idx} parsing error: {str(e)}")
                continue
        
        logger.debug(f"Parsed {len(validated_strengths)} valid strengths")
        return validated_strengths
    
    def _parse_weaknesses(self, weaknesses_data: List[Dict[str, Any]]) -> List[AnalyticsWeakness]:
        """Parse and validate weaknesses list."""
        if not isinstance(weaknesses_data, list):
            logger.warning("Weaknesses data is not a list")
            return []
        
        validated_weaknesses = []
        
        for idx, weakness_dict in enumerate(weaknesses_data):
            try:
                # Ensure required fields exist
                if not isinstance(weakness_dict, dict):
                    logger.warning(f"Weakness {idx}: Not a dictionary")
                    continue
                
                # Convert and validate types
                if 'accuracy' in weakness_dict:
                    try:
                        weakness_dict['accuracy'] = float(weakness_dict['accuracy'])
                    except (ValueError, TypeError):
                        logger.warning(f"Weakness {idx}: Invalid accuracy value")
                        continue
                
                if 'estimated_study_hours' in weakness_dict:
                    try:
                        weakness_dict['estimated_study_hours'] = float(weakness_dict['estimated_study_hours'])
                    except (ValueError, TypeError):
                        logger.warning(f"Weakness {idx}: Invalid estimated_study_hours")
                        continue
                
                # Normalize priority
                if 'priority' in weakness_dict:
                    priority = str(weakness_dict['priority']).upper()
                    if priority not in ['HIGH', 'MEDIUM', 'LOW']:
                        logger.warning(f"Weakness {idx}: Invalid priority '{priority}', defaulting to MEDIUM")
                        weakness_dict['priority'] = 'MEDIUM'
                    else:
                        weakness_dict['priority'] = priority
                
                # Validate required fields
                required = ['topic', 'subject', 'accuracy', 'reason', 'priority', 
                           'estimated_study_hours', 'recommendation']
                if not all(field in weakness_dict for field in required):
                    missing = [f for f in required if f not in weakness_dict]
                    logger.warning(f"Weakness {idx}: Missing fields {missing}")
                    continue
                
                weakness = AnalyticsWeakness(**weakness_dict)
                validated_weaknesses.append(weakness)
                
            except ValidationError as e:
                if self.log_issues:
                    logger.warning(f"Weakness {idx} validation failed: {str(e)}")
                continue
            except Exception as e:
                if self.log_issues:
                    logger.warning(f"Weakness {idx} parsing error: {str(e)}")
                continue
        
        logger.debug(f"Parsed {len(validated_weaknesses)} valid weaknesses")
        return validated_weaknesses
    
    def parse_partial(self, text: str) -> Dict[str, Any]:
        """
        Parse response and return raw dictionary without full validation.
        
        Useful for debugging or when you need access to raw data.
        
        Args:
            text: Raw response text
        
        Returns:
            Parsed dictionary (may be incomplete or invalid)
        
        Example:
            >>> raw_data = parser.parse_partial(gemini_response)
            >>> print(raw_data.keys())
        """
        logger.info("Parsing response as partial (no strict validation)")
        
        # Try all parsing strategies
        data = self._try_direct_parse(text)
        if data is None:
            data = self._extract_from_markdown(text)
        if data is None:
            data = self._extract_json_object(text)
        if data is None:
            data = self._try_repair_json(text)
        
        if data is None:
            logger.warning("Could not parse any JSON from text")
            return {}
        
        return data
