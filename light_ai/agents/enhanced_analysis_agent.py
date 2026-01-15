#!/usr/bin/env python3
"""
Enhanced Analysis Agent that uses the new data retrieval engine
to perform comprehensive persona and context analysis
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re
from datetime import datetime

# Import the new data retrieval engine
from ..data_retrieval_engine import get_retrieval_engine
# Import the conversation analyzer for intelligent persona/context extraction
from .conversation_analyzer import get_conversation_analyzer

logger = logging.getLogger(__name__)

@dataclass
class AnalysisRequest:
    """Request for analysis"""
    client_id: str
    user_id: str
    query: str
    desired_fields: Optional[Dict[str, str]] = None
    optional_fields: Optional[Dict[str, str]] = None

@dataclass
class AnalysisResult:
    """Result of analysis"""
    success: bool
    persona: Optional[str] = None
    context: Optional[str] = None
    insights: Optional[str] = None
    recommendations: Optional[str] = None
    data_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class EnhancedAnalysisAgent:
    """Enhanced analysis agent with robust data retrieval and intelligent conversation analysis"""
    
    def __init__(self):
        self.retrieval_engine = get_retrieval_engine()
        self.conversation_analyzer = get_conversation_analyzer()
        logger.info("Enhanced Analysis Agent initialized with conversation analyzer")
    
    def analyze_user_data(self, request: AnalysisRequest) -> AnalysisResult:
        """Perform comprehensive analysis of user data"""
        try:
            logger.info(f"Starting analysis for user {request.user_id}")
            
            # Get all user data using the new retrieval engine
            all_data = self.retrieval_engine.get_all_user_data(request.client_id, request.user_id)
            
            if all_data["total_resources"] == 0:
                return AnalysisResult(
                    success=False,
                    error="No data found for this user"
                )
            
            # Extract and analyze the data
            analysis_result = self._perform_analysis(all_data, request.query)
            
            # Add data summary
            analysis_result.data_summary = {
                "total_resources": all_data["total_resources"],
                "json_files": len(all_data["data_by_source"]["json_files"]),
                "duckdb_tables": len(all_data["data_by_source"]["duckdb_tables"]),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Analysis completed for user {request.user_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return AnalysisResult(
                success=False,
                error=str(e)
            )
    
    def _perform_analysis(self, all_data: Dict[str, Any], query: str) -> AnalysisResult:
        """Perform the actual analysis on the retrieved data"""
        
        # Combine all JSON data for analysis
        combined_data = {}
        for json_item in all_data["data_by_source"]["json_files"]:
            resource_id = json_item["resource_id"]
            data = json_item["data"]
            combined_data[resource_id] = data
        
        if not combined_data:
            return AnalysisResult(
                success=False,
                error="No JSON data available for analysis"
            )
        
        # Use intelligent conversation analyzer for persona and context extraction
        persona_text = None
        context_text = None
        
        # Try to analyze each resource with the conversation analyzer
        for resource_id, resource_data in combined_data.items():
            persona_extraction, context_extraction = self.conversation_analyzer.analyze_data(resource_data)
            
            if persona_extraction:
                persona_text = self.conversation_analyzer.format_persona_for_output(persona_extraction)
                logger.info(f"Extracted persona from resource {resource_id} with confidence {persona_extraction.confidence_score:.2f}")
            
            if context_extraction:
                context_text = self.conversation_analyzer.format_context_for_output(context_extraction)
                logger.info(f"Extracted context from resource {resource_id} with confidence {context_extraction.confidence_score:.2f}")
            
            # If we found good extractions, use them
            if persona_text and context_text:
                break
        
        # Fallback to pattern-based analysis if conversation analyzer didn't find anything
        if not persona_text:
            persona_text = self._extract_persona(combined_data)
        
        if not context_text:
            context_text = self._extract_context(combined_data)
        
        # Generate insights and recommendations
        insights = self._generate_insights(combined_data)
        recommendations = self._generate_recommendations(combined_data, query)
        
        return AnalysisResult(
            success=True,
            persona=persona_text,
            context=context_text,
            insights=insights,
            recommendations=recommendations
        )
    
    def _extract_persona(self, data: Dict[str, Any]) -> str:
        """Extract persona characteristics from the data"""
        persona_elements = []
        
        for resource_id, resource_data in data.items():
            # Look for common persona indicators
            if isinstance(resource_data, dict):
                persona_info = self._analyze_dict_for_persona(resource_data)
                if persona_info:
                    persona_elements.extend(persona_info)
        
        if not persona_elements:
            return "Unable to extract detailed persona information from the available data."
        
        # Combine persona elements into a coherent description
        persona_text = "Based on the available data, this user exhibits the following characteristics:\n\n"
        
        # Group persona elements by category
        demographics = [p for p in persona_elements if p.get('category') == 'demographic']
        interests = [p for p in persona_elements if p.get('category') == 'interest']
        goals = [p for p in persona_elements if p.get('category') == 'goal']
        traits = [p for p in persona_elements if p.get('category') == 'trait']
        
        if demographics:
            persona_text += "**Demographics:**\n"
            for demo in demographics:
                persona_text += f"- {demo['description']}\n"
            persona_text += "\n"
        
        if interests:
            persona_text += "**Interests & Skills:**\n"
            for interest in interests:
                persona_text += f"- {interest['description']}\n"
            persona_text += "\n"
        
        if goals:
            persona_text += "**Goals & Aspirations:**\n"
            for goal in goals:
                persona_text += f"- {goal['description']}\n"
            persona_text += "\n"
        
        if traits:
            persona_text += "**Personality Traits:**\n"
            for trait in traits:
                persona_text += f"- {trait['description']}\n"
        
        return persona_text.strip()
    
    def _analyze_dict_for_persona(self, data: Dict[str, Any], prefix: str = "") -> List[Dict[str, str]]:
        """Recursively analyze dictionary for persona information"""
        persona_info = []
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Demographic information
            if key_lower in ['name', 'age', 'gender', 'location', 'occupation', 'role', 'position']:
                persona_info.append({
                    'category': 'demographic',
                    'description': f"{key.replace('_', ' ').title()}: {value}"
                })
            
            # Educational/Professional information
            elif key_lower in ['program', 'degree', 'major', 'department', 'company', 'school', 'university']:
                persona_info.append({
                    'category': 'demographic',
                    'description': f"{key.replace('_', ' ').title()}: {value}"
                })
            
            # Performance metrics
            elif key_lower in ['gpa', 'grade', 'score', 'rating', 'performance']:
                persona_info.append({
                    'category': 'trait',
                    'description': f"Academic/Performance level: {key.replace('_', ' ').title()} of {value}"
                })
            
            # Interests and skills
            elif key_lower in ['interests', 'skills', 'hobbies', 'specialties', 'expertise']:
                if isinstance(value, list):
                    interests_str = ", ".join(str(v) for v in value)
                    persona_info.append({
                        'category': 'interest',
                        'description': f"{key.replace('_', ' ').title()}: {interests_str}"
                    })
                else:
                    persona_info.append({
                        'category': 'interest',
                        'description': f"{key.replace('_', ' ').title()}: {value}"
                    })
            
            # Goals and aspirations
            elif key_lower in ['goals', 'career_goals', 'objectives', 'aspirations', 'plans']:
                persona_info.append({
                    'category': 'goal',
                    'description': f"{key.replace('_', ' ').title()}: {value}"
                })
            
            # Personality traits
            elif key_lower in ['personality', 'traits', 'characteristics', 'behavior']:
                if isinstance(value, list):
                    traits_str = ", ".join(str(v) for v in value)
                    persona_info.append({
                        'category': 'trait',
                        'description': f"Personality traits: {traits_str}"
                    })
                else:
                    persona_info.append({
                        'category': 'trait',
                        'description': f"Personality: {value}"
                    })
            
            # Recursive analysis for nested dictionaries
            elif isinstance(value, dict):
                nested_info = self._analyze_dict_for_persona(value, f"{prefix}{key}.")
                persona_info.extend(nested_info)
        
        return persona_info
    
    def _extract_context(self, data: Dict[str, Any]) -> str:
        """Extract contextual information from the data"""
        context_elements = []
        
        for resource_id, resource_data in data.items():
            if isinstance(resource_data, dict):
                context_info = self._analyze_dict_for_context(resource_data)
                if context_info:
                    context_elements.extend(context_info)
        
        if not context_elements:
            return "Limited contextual information available from the current data."
        
        context_text = "**Contextual Analysis:**\n\n"
        
        # Group context by type
        academic = [c for c in context_elements if c.get('type') == 'academic']
        professional = [c for c in context_elements if c.get('type') == 'professional']
        personal = [c for c in context_elements if c.get('type') == 'personal']
        temporal = [c for c in context_elements if c.get('type') == 'temporal']
        
        if academic:
            context_text += "**Academic Context:**\n"
            for item in academic:
                context_text += f"- {item['description']}\n"
            context_text += "\n"
        
        if professional:
            context_text += "**Professional Context:**\n"
            for item in professional:
                context_text += f"- {item['description']}\n"
            context_text += "\n"
        
        if personal:
            context_text += "**Personal Context:**\n"
            for item in personal:
                context_text += f"- {item['description']}\n"
            context_text += "\n"
        
        if temporal:
            context_text += "**Temporal Context:**\n"
            for item in temporal:
                context_text += f"- {item['description']}\n"
        
        return context_text.strip()
    
    def _analyze_dict_for_context(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Analyze dictionary for contextual information"""
        context_info = []
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Academic context
            if key_lower in ['year_level', 'semester', 'academic_year', 'course', 'class']:
                context_info.append({
                    'type': 'academic',
                    'description': f"Currently in {key.replace('_', ' ')}: {value}"
                })
            
            # Professional context
            elif key_lower in ['experience_years', 'position', 'department', 'company_size']:
                context_info.append({
                    'type': 'professional',
                    'description': f"{key.replace('_', ' ').title()}: {value}"
                })
            
            # Personal context
            elif key_lower in ['residence', 'location', 'status', 'enrollment_status']:
                context_info.append({
                    'type': 'personal',
                    'description': f"{key.replace('_', ' ').title()}: {value}"
                })
            
            # Temporal context
            elif key_lower in ['created_at', 'updated_at', 'date', 'timestamp']:
                context_info.append({
                    'type': 'temporal',
                    'description': f"Data from: {value}"
                })
            
            # Recursive analysis
            elif isinstance(value, dict):
                nested_context = self._analyze_dict_for_context(value)
                context_info.extend(nested_context)
        
        return context_info
    
    def _generate_insights(self, data: Dict[str, Any]) -> str:
        """Generate insights from the data"""
        insights = []
        
        # Analyze data patterns
        total_fields = 0
        numeric_fields = 0
        list_fields = 0
        
        for resource_id, resource_data in data.items():
            if isinstance(resource_data, dict):
                field_analysis = self._count_field_types(resource_data)
                total_fields += field_analysis['total']
                numeric_fields += field_analysis['numeric']
                list_fields += field_analysis['lists']
        
        insights.append(f"Data contains {total_fields} total fields across all resources")
        
        if numeric_fields > 0:
            insights.append(f"Found {numeric_fields} quantitative metrics for analysis")
        
        if list_fields > 0:
            insights.append(f"Identified {list_fields} multi-value attributes (interests, skills, etc.)")
        
        # Look for specific patterns
        for resource_id, resource_data in data.items():
            if isinstance(resource_data, dict):
                pattern_insights = self._identify_patterns(resource_data)
                insights.extend(pattern_insights)
        
        if not insights:
            insights.append("Limited insights available from current data structure")
        
        return "**Key Insights:**\n" + "\n".join(f"• {insight}" for insight in insights)
    
    def _count_field_types(self, data: Dict[str, Any]) -> Dict[str, int]:
        """Count different types of fields in the data"""
        counts = {'total': 0, 'numeric': 0, 'lists': 0}
        
        for key, value in data.items():
            counts['total'] += 1
            
            if isinstance(value, (int, float)):
                counts['numeric'] += 1
            elif isinstance(value, list):
                counts['lists'] += 1
            elif isinstance(value, dict):
                nested_counts = self._count_field_types(value)
                counts['total'] += nested_counts['total']
                counts['numeric'] += nested_counts['numeric']
                counts['lists'] += nested_counts['lists']
        
        return counts
    
    def _identify_patterns(self, data: Dict[str, Any]) -> List[str]:
        """Identify interesting patterns in the data"""
        patterns = []
        
        # Look for performance indicators
        if 'gpa' in str(data).lower():
            patterns.append("Academic performance data available for trend analysis")
        
        # Look for growth indicators
        if any(word in str(data).lower() for word in ['goals', 'career', 'aspirations']):
            patterns.append("Future-oriented planning and goal-setting evident")
        
        # Look for skill diversity
        if 'interests' in str(data).lower() or 'skills' in str(data).lower():
            patterns.append("Diverse skill set and interests indicate adaptability")
        
        return patterns
    
    def _generate_recommendations(self, data: Dict[str, Any], query: str) -> str:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Analyze the query for intent
        query_lower = query.lower()
        
        if 'persona' in query_lower:
            recommendations.append("Consider conducting deeper personality assessments for more detailed persona mapping")
        
        if 'context' in query_lower:
            recommendations.append("Gather additional environmental and situational data for richer context")
        
        # Look at the data to suggest improvements
        for resource_id, resource_data in data.items():
            if isinstance(resource_data, dict):
                data_recommendations = self._analyze_data_completeness(resource_data)
                recommendations.extend(data_recommendations)
        
        if not recommendations:
            recommendations.append("Continue collecting structured data to improve analysis accuracy")
        
        return "**Recommendations:**\n" + "\n".join(f"• {rec}" for rec in recommendations[:5])  # Limit to top 5
    
    def _analyze_data_completeness(self, data: Dict[str, Any]) -> List[str]:
        """Analyze data completeness and suggest improvements"""
        recommendations = []
        
        # Check for missing common fields
        common_fields = ['interests', 'skills', 'goals', 'experience', 'preferences']
        missing_fields = [field for field in common_fields if field not in str(data).lower()]
        
        if missing_fields:
            recommendations.append(f"Consider adding data about: {', '.join(missing_fields[:3])}")
        
        # Check for temporal data
        if not any(word in str(data).lower() for word in ['date', 'time', 'year', 'created']):
            recommendations.append("Add temporal data to track changes and trends over time")
        
        return recommendations


# Global instance
_analysis_agent: Optional[EnhancedAnalysisAgent] = None

def get_analysis_agent() -> EnhancedAnalysisAgent:
    """Get the global analysis agent instance"""
    global _analysis_agent
    if _analysis_agent is None:
        _analysis_agent = EnhancedAnalysisAgent()
    return _analysis_agent