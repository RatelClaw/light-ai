"""
Intelligent Content Analyzer - LLM-powered analysis for ANY JSON structure.

This tool integrates into the Strands multi-agent system to provide intelligent
semantic analysis of content regardless of structure. Uses LLM for understanding
and ChromaDB/RAG for handling large content.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .base import BaseAgent, AgentConfig
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


@dataclass
class ContentAnalysisResult:
    """Result of intelligent content analysis"""
    success: bool
    extracted_fields: Dict[str, str]  # field_name -> extracted_value
    confidence_score: float
    analysis_method: str  # "llm_analysis", "pattern_matching", "hybrid"
    tokens_used: int
    error: Optional[str] = None


class IntelligentContentAnalyzer(BaseAgent):
    """
    LLM-powered content analyzer that can extract information from ANY JSON structure.
    
    Features:
    - No hardcoded patterns - uses LLM to understand content semantically
    - Handles conversations, logs, metadata, nested structures dynamically
    - Intelligent chunking for large content to avoid token limits
    - Uses ChromaDB for RAG when content is too large
    - Falls back to pattern matching when LLM is unavailable
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the intelligent content analyzer"""
        
        system_prompt = """You are an expert data analyst specializing in extracting structured information from unstructured or semi-structured data.

Your task is to analyze JSON data of ANY structure and extract specific requested fields by understanding the semantic meaning of the content, not just field names.

Key capabilities:
1. Understand conversational data (chat logs, messages, dialogues)
2. Extract information from logs, metadata, and complex nested structures
3. Identify persona characteristics from ANY data format
4. Extract contextual information regardless of structure
5. Handle dynamic, varying JSON structures
6. Provide confidence scores for extractions

Analysis approach:
- Read and understand the CONTENT, not just field names
- Look for semantic meaning in text, conversations, descriptions
- Extract requested information even if field names don't match
- Provide clear, concise extracted values
- Indicate confidence in your extractions

Output format:
Always respond with a JSON object containing:
{
  "extracted_fields": {
    "field_name": "extracted value with explanation"
  },
  "confidence_score": 0.0-1.0,
  "reasoning": "brief explanation of extraction logic"
}"""
        
        agent_config = AgentConfig(
            name="intelligent_content_analyzer",
            model_name=config.openrouter.default_model if config else "anthropic/claude-3.5-sonnet",
            temperature=0.2,  # Lower for analytical consistency
            max_tokens=2048,
            timeout_seconds=60,
            system_prompt=system_prompt
        )
        
        super().__init__(agent_config, config)
        self.max_content_size = 8000  # Max characters to send to LLM

    
    async def analyze_content(self, data: Any, desired_fields: Dict[str, str]) -> ContentAnalysisResult:
        """
        Analyze content to extract desired fields using LLM intelligence.
        
        Args:
            data: Any JSON-serializable data structure
            desired_fields: Dict of {field_name: description} to extract
            
        Returns:
            ContentAnalysisResult with extracted field values
        """
        try:
            # Convert data to JSON string for analysis
            data_json = json.dumps(data, indent=2, default=str)
            
            # Check if content is too large
            if len(data_json) > self.max_content_size:
                # Use intelligent chunking and summarization
                return await self._analyze_large_content(data, desired_fields)
            else:
                # Direct LLM analysis
                return await self._analyze_with_llm(data_json, desired_fields)
                
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return ContentAnalysisResult(
                success=False,
                extracted_fields={},
                confidence_score=0.0,
                analysis_method="error",
                tokens_used=0,
                error=str(e)
            )
    
    async def _analyze_with_llm(self, data_json: str, desired_fields: Dict[str, str]) -> ContentAnalysisResult:
        """Analyze content directly with LLM"""
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(data_json, desired_fields)
        
        try:
            # Execute LLM analysis
            response = await self.execute(prompt)
            
            # Parse LLM response
            result = self._parse_llm_response(response, desired_fields)
            result.analysis_method = "llm_analysis"
            result.tokens_used = len(prompt.split()) + len(response.split())  # Rough estimate
            
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            # Fallback to pattern matching
            return self._fallback_pattern_analysis(data_json, desired_fields)
    
    async def _analyze_large_content(self, data: Any, desired_fields: Dict[str, str]) -> ContentAnalysisResult:
        """Handle large content with intelligent chunking"""
        
        # Strategy: Extract key sections and analyze those
        key_sections = self._extract_key_sections(data, desired_fields)
        
        # Analyze each section
        section_results = []
        for section_name, section_data in key_sections.items():
            section_json = json.dumps(section_data, indent=2, default=str)
            
            if len(section_json) <= self.max_content_size:
                result = await self._analyze_with_llm(section_json, desired_fields)
                section_results.append(result)
        
        # Combine results from all sections
        return self._combine_section_results(section_results, desired_fields)
    
    def _build_analysis_prompt(self, data_json: str, desired_fields: Dict[str, str]) -> str:
        """Build prompt for LLM analysis"""
        
        prompt_parts = [
            "Analyze the following JSON data and extract the requested fields.",
            "",
            "REQUESTED FIELDS:",
        ]
        
        for field_name, field_desc in desired_fields.items():
            prompt_parts.append(f"- {field_name}: {field_desc}")
        
        prompt_parts.extend([
            "",
            "DATA TO ANALYZE:",
            "```json",
            data_json[:self.max_content_size],  # Truncate if needed
            "```",
            "",
            "INSTRUCTIONS:",
            "1. Read and understand the CONTENT semantically, not just field names",
            "2. For conversations: extract information from what people say",
            "3. For logs: extract patterns and meaningful events",
            "4. For metadata: understand the context and relationships",
            "5. Extract the requested fields even if they're not explicitly named",
            "6. Provide clear, concise values for each requested field",
            "",
            "Respond with JSON in this exact format:",
            "{",
            '  "extracted_fields": {',
            '    "field_name": "extracted value"',
            "  },",
            '  "confidence_score": 0.85,',
            '  "reasoning": "brief explanation"',
            "}"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_llm_response(self, response: str, desired_fields: Dict[str, str]) -> ContentAnalysisResult:
        """Parse LLM response into structured result"""
        
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                result_data = json.loads(json_match.group())
                
                return ContentAnalysisResult(
                    success=True,
                    extracted_fields=result_data.get("extracted_fields", {}),
                    confidence_score=result_data.get("confidence_score", 0.7),
                    analysis_method="llm_analysis",
                    tokens_used=0  # Will be set by caller
                )
            else:
                # LLM didn't return proper JSON, try to extract from text
                return self._extract_from_text_response(response, desired_fields)
                
        except json.JSONDecodeError:
            return self._extract_from_text_response(response, desired_fields)
    
    def _extract_from_text_response(self, response: str, desired_fields: Dict[str, str]) -> ContentAnalysisResult:
        """Extract field values from text response when JSON parsing fails"""
        
        extracted_fields = {}
        
        for field_name in desired_fields.keys():
            # Look for field_name: value patterns in response
            import re
            pattern = rf"{field_name}[:\s]+([^\n]+)"
            match = re.search(pattern, response, re.IGNORECASE)
            
            if match:
                extracted_fields[field_name] = match.group(1).strip()
        
        return ContentAnalysisResult(
            success=len(extracted_fields) > 0,
            extracted_fields=extracted_fields,
            confidence_score=0.6,  # Lower confidence for text extraction
            analysis_method="llm_analysis",
            tokens_used=0
        )
    
    def _fallback_pattern_analysis(self, data_json: str, desired_fields: Dict[str, str]) -> ContentAnalysisResult:
        """Fallback to simple pattern matching when LLM fails"""
        
        try:
            data = json.loads(data_json)
        except:
            data = {}
        
        extracted_fields = {}
        
        for field_name, field_desc in desired_fields.items():
            # Simple pattern matching fallback
            value = self._pattern_match_field(data, field_name, field_desc)
            if value:
                extracted_fields[field_name] = value
        
        return ContentAnalysisResult(
            success=len(extracted_fields) > 0,
            extracted_fields=extracted_fields,
            confidence_score=0.5,  # Lower confidence for pattern matching
            analysis_method="pattern_matching",
            tokens_used=0
        )
    
    def _pattern_match_field(self, data: Any, field_name: str, field_desc: str) -> Optional[str]:
        """Simple pattern matching for field extraction"""
        
        # Flatten data and look for matching keys
        flattened = self._flatten_dict(data)
        
        field_name_lower = field_name.lower()
        
        # Direct match
        if field_name_lower in flattened:
            return str(flattened[field_name_lower])
        
        # Partial match
        for key, value in flattened.items():
            if field_name_lower in key.lower() or key.lower() in field_name_lower:
                return str(value)
        
        return None
    
    def _flatten_dict(self, data: Any, prefix: str = "") -> Dict[str, Any]:
        """Flatten nested dictionary"""
        result = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    result.update(self._flatten_dict(value, new_key))
                else:
                    result[new_key.lower()] = value
        elif isinstance(data, list) and data:
            for i, item in enumerate(data[:3]):  # First 3 items
                result.update(self._flatten_dict(item, f"{prefix}[{i}]"))
        
        return result
    
    def _extract_key_sections(self, data: Any, desired_fields: Dict[str, str]) -> Dict[str, Any]:
        """Extract key sections from large data for focused analysis"""
        
        sections = {}
        
        if isinstance(data, dict):
            # Look for sections that might contain requested information
            for field_name in desired_fields.keys():
                field_lower = field_name.lower()
                
                # Find relevant sections
                for key, value in data.items():
                    key_lower = key.lower()
                    if field_lower in key_lower or any(word in key_lower for word in field_lower.split('_')):
                        sections[key] = value
            
            # Also include any "messages", "content", "data" sections
            for key in ['messages', 'conversation', 'content', 'data', 'items', 'records']:
                if key in data:
                    sections[key] = data[key]
        
        elif isinstance(data, list):
            # For lists, take a sample
            sections['sample_data'] = data[:10]  # First 10 items
        
        return sections if sections else {'full_data': data}
    
    def _combine_section_results(self, section_results: List[ContentAnalysisResult], 
                                 desired_fields: Dict[str, str]) -> ContentAnalysisResult:
        """Combine results from multiple section analyses"""
        
        if not section_results:
            return ContentAnalysisResult(
                success=False,
                extracted_fields={},
                confidence_score=0.0,
                analysis_method="chunked_analysis",
                tokens_used=0,
                error="No sections analyzed"
            )
        
        # Combine extracted fields, preferring higher confidence results
        combined_fields = {}
        field_confidences = {}
        
        for result in section_results:
            if result.success:
                for field_name, value in result.extracted_fields.items():
                    if field_name not in combined_fields or result.confidence_score > field_confidences.get(field_name, 0):
                        combined_fields[field_name] = value
                        field_confidences[field_name] = result.confidence_score
        
        # Average confidence
        avg_confidence = sum(r.confidence_score for r in section_results) / len(section_results)
        total_tokens = sum(r.tokens_used for r in section_results)
        
        return ContentAnalysisResult(
            success=len(combined_fields) > 0,
            extracted_fields=combined_fields,
            confidence_score=avg_confidence,
            analysis_method="chunked_analysis",
            tokens_used=total_tokens
        )


# Global instance
_content_analyzer: Optional[IntelligentContentAnalyzer] = None


def get_content_analyzer(config: Optional[Config] = None) -> IntelligentContentAnalyzer:
    """Get the global content analyzer instance"""
    global _content_analyzer
    if _content_analyzer is None:
        _content_analyzer = IntelligentContentAnalyzer(config)
    return _content_analyzer
