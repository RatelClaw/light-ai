"""
Intelligent Content Analyzer for Dynamic JSON Analysis.

This module uses LLM-powered analysis to extract meaningful information from ANY JSON structure,
whether it's conversations, logs, metadata, or complex nested data. No hardcoded patterns.
Uses RAG with ChromaDB for large content and intelligent chunking for LLM calls.
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio

from ..logger import get_logger
from .base import BaseAgent, AgentConfig
from ..config import get_config

logger = get_logger(__name__)


@dataclass
class PersonaExtraction:
    """Extracted persona information from conversation"""
    demographics: Dict[str, str]  # age, occupation, location, etc.
    professional: Dict[str, str]  # role, experience, skills, tools
    goals: List[str]  # aspirations, objectives
    challenges: List[str]  # pain points, difficulties
    preferences: Dict[str, str]  # communication style, learning preferences
    traits: List[str]  # personality characteristics
    confidence_score: float


@dataclass
class ContextExtraction:
    """Extracted context information from conversation"""
    domain: str  # retail, education, healthcare, etc.
    situation: str  # current circumstances
    temporal: Dict[str, str]  # time-related context
    relationships: List[str]  # mentioned relationships
    environment: Dict[str, str]  # work environment, tools, systems
    confidence_score: float


class ConversationAnalyzer:
    """
    Analyzes conversational data to extract persona and context.
    
    This analyzer understands various conversation formats:
    - Chat logs with user/assistant messages
    - Interview transcripts
    - Survey responses
    - Customer support conversations
    """
    
    def __init__(self):
        """Initialize the conversation analyzer"""
        self.persona_indicators = self._build_persona_indicators()
        self.context_indicators = self._build_context_indicators()
    
    def analyze_data(self, data: Any) -> Tuple[Optional[PersonaExtraction], Optional[ContextExtraction]]:
        """
        Analyze data to extract persona and context.
        
        Args:
            data: Input data (dict, list, or string)
            
        Returns:
            Tuple of (PersonaExtraction, ContextExtraction)
        """
        try:
            # Detect data format and extract conversation
            conversation = self._extract_conversation(data)
            
            if not conversation:
                logger.warning("No conversation content found in data")
                return None, None
            
            # Extract persona and context from conversation
            persona = self._extract_persona_from_conversation(conversation)
            context = self._extract_context_from_conversation(conversation)
            
            return persona, context
            
        except Exception as e:
            logger.error(f"Conversation analysis failed: {e}")
            return None, None
    
    def _extract_conversation(self, data: Any) -> List[Dict[str, str]]:
        """
        Extract conversation messages from various data formats.
        
        Returns list of {role, content} dictionaries
        """
        conversation = []
        
        if isinstance(data, dict):
            # Check for common conversation formats
            if "messages" in data:
                # Format: {"messages": [{role, content}, ...]}
                messages = data["messages"]
                if isinstance(messages, list):
                    for msg in messages:
                        if isinstance(msg, dict):
                            role = msg.get("role", msg.get("sender", msg.get("from", "unknown")))
                            content = msg.get("content", msg.get("text", msg.get("message", "")))
                            if content:
                                conversation.append({"role": role, "content": str(content)})
            
            elif "conversation" in data:
                # Format: {"conversation": [...]}
                return self._extract_conversation(data["conversation"])
            
            elif "dialog" in data or "dialogue" in data:
                # Format: {"dialog": [...]}
                dialog_key = "dialog" if "dialog" in data else "dialogue"
                return self._extract_conversation(data[dialog_key])
            
            elif "role" in data and "content" in data:
                # Single message format
                conversation.append({
                    "role": data["role"],
                    "content": str(data["content"])
                })
            
            else:
                # Try to find any text fields that might contain conversation
                for key, value in data.items():
                    if isinstance(value, (list, dict)):
                        nested_conv = self._extract_conversation(value)
                        conversation.extend(nested_conv)
                    elif isinstance(value, str) and len(value) > 50:
                        # Might be conversation text
                        conversation.append({"role": "unknown", "content": value})
        
        elif isinstance(data, list):
            # List of messages
            for item in data:
                if isinstance(item, dict):
                    nested_conv = self._extract_conversation(item)
                    conversation.extend(nested_conv)
                elif isinstance(item, str):
                    conversation.append({"role": "unknown", "content": item})
        
        elif isinstance(data, str):
            # Plain text - might be a single message or transcript
            conversation.append({"role": "unknown", "content": data})
        
        return conversation
    
    def _extract_persona_from_conversation(self, conversation: List[Dict[str, str]]) -> PersonaExtraction:
        """Extract persona characteristics from conversation content"""
        
        demographics = {}
        professional = {}
        goals = []
        challenges = []
        preferences = {}
        traits = []
        
        # Analyze each message
        for msg in conversation:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            
            # Focus on user messages for persona extraction
            if role in ["user", "customer", "client", "participant"]:
                # Extract demographics
                demographics.update(self._extract_demographics(content))
                
                # Extract professional information
                professional.update(self._extract_professional_info(content))
                
                # Extract goals
                goals.extend(self._extract_goals(content))
                
                # Extract challenges
                challenges.extend(self._extract_challenges(content))
                
                # Extract preferences
                preferences.update(self._extract_preferences(content))
                
                # Extract personality traits
                traits.extend(self._extract_traits(content))
        
        # Calculate confidence based on amount of information extracted
        info_count = (
            len(demographics) + len(professional) + len(goals) + 
            len(challenges) + len(preferences) + len(traits)
        )
        confidence_score = min(0.95, 0.3 + (info_count * 0.05))
        
        return PersonaExtraction(
            demographics=demographics,
            professional=professional,
            goals=list(set(goals)),  # Remove duplicates
            challenges=list(set(challenges)),
            preferences=preferences,
            traits=list(set(traits)),
            confidence_score=confidence_score
        )
    
    def _extract_context_from_conversation(self, conversation: List[Dict[str, str]]) -> ContextExtraction:
        """Extract contextual information from conversation"""
        
        domain_indicators = []
        situation_parts = []
        temporal = {}
        relationships = []
        environment = {}
        
        # Analyze conversation for context
        for msg in conversation:
            content = msg.get("content", "")
            
            # Extract domain indicators
            domain_indicators.extend(self._extract_domain_indicators(content))
            
            # Extract situation
            situation_parts.extend(self._extract_situation(content))
            
            # Extract temporal context
            temporal.update(self._extract_temporal_context(content))
            
            # Extract relationships
            relationships.extend(self._extract_relationships(content))
            
            # Extract environment
            environment.update(self._extract_environment(content))
        
        # Determine primary domain
        domain = self._determine_domain(domain_indicators)
        
        # Build situation description
        situation = " ".join(situation_parts[:3]) if situation_parts else "General conversation"
        
        # Calculate confidence
        context_elements = len(domain_indicators) + len(temporal) + len(relationships) + len(environment)
        confidence_score = min(0.95, 0.4 + (context_elements * 0.05))
        
        return ContextExtraction(
            domain=domain,
            situation=situation,
            temporal=temporal,
            relationships=list(set(relationships)),
            environment=environment,
            confidence_score=confidence_score
        )
    
    def _extract_demographics(self, text: str) -> Dict[str, str]:
        """Extract demographic information from text"""
        demographics = {}
        text_lower = text.lower()
        
        # Age extraction
        age_patterns = [
            r"i'?m\s+(?:a\s+)?(\d{1,2})[\s-]year",
            r"(\d{1,2})\s*-?\s*year[\s-]old",
            r"age\s+(?:is\s+)?(\d{1,2})",
            r"(\d{1,2})\s+years?\s+old"
        ]
        for pattern in age_patterns:
            match = re.search(pattern, text_lower)
            if match:
                age = match.group(1)
                if 10 <= int(age) <= 99:  # Reasonable age range
                    demographics["age"] = age
                    break
        
        # Occupation extraction
        occupation_patterns = [
            r"i'?m\s+(?:a\s+)?(\d{1,2})[\s-]year[\s-]old\s+(\w+(?:\s+\w+){0,2})\s+working",
            r"i'?m\s+a\s+(\w+(?:\s+\w+){0,2})\s+(?:working|in|at)",
            r"work\s+as\s+(?:a\s+|an\s+)?(\w+(?:\s+\w+){0,2})",
            r"(?:job|role|position)\s+(?:is|as)\s+(?:a\s+|an\s+)?(\w+(?:\s+\w+){0,2})",
            r"i'?m\s+(?:a\s+|an\s+)?(\w+(?:\s+\w+){0,2})\s+(?:working|in\s+the)",
            r"(\w+(?:\s+\w+){0,2})\s+working\s+in"
        ]
        for pattern in occupation_patterns:
            match = re.search(pattern, text_lower)
            if match:
                # For patterns with age, get the second group (occupation)
                occupation = match.group(2) if match.lastindex >= 2 else match.group(1)
                occupation = occupation.strip()
                # Filter out common words that aren't occupations
                if len(occupation) > 3 and occupation not in ["the", "and", "for", "this", "that", "been", "year", "old", "years"]:
                    demographics["occupation"] = occupation
                    break
        
        # Location extraction
        location_patterns = [
            r"(?:from|in|based in|located in|living in) ([A-Z][a-z]+(?:,?\s+[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+,\s+[A-Z]{2})",  # City, State
        ]
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                demographics["location"] = match.group(1)
                break
        
        return demographics
    
    def _extract_professional_info(self, text: str) -> Dict[str, str]:
        """Extract professional information from text"""
        professional = {}
        text_lower = text.lower()
        
        # Experience extraction
        experience_patterns = [
            r"(\d+)\s+years?\s+(?:of\s+)?experience",
            r"(?:been|working)\s+(?:in|for)\s+(?:this\s+)?(?:field|role|position)\s+(?:for\s+)?(\d+)\s+years?",
            r"(\d+)\+?\s+years?\s+in"
        ]
        for pattern in experience_patterns:
            match = re.search(pattern, text_lower)
            if match:
                professional["experience_years"] = match.group(1)
                break
        
        # Skills extraction
        skill_indicators = ["work with", "use", "skilled in", "proficient in", "expert in", "familiar with"]
        for indicator in skill_indicators:
            if indicator in text_lower:
                # Extract text after indicator
                idx = text_lower.find(indicator)
                after_text = text[idx + len(indicator):idx + len(indicator) + 100]
                # Look for comma-separated list or "and" separated items
                skills_match = re.search(r"([A-Za-z0-9\s,]+(?:and\s+[A-Za-z0-9\s]+)?)", after_text)
                if skills_match:
                    skills_text = skills_match.group(1).strip()
                    professional["skills"] = skills_text
                    break
        
        # Tools/Technologies extraction
        common_tools = ["SQL", "Python", "Excel", "Power BI", "Tableau", "R", "Java", "JavaScript", 
                       "AWS", "Azure", "Docker", "Kubernetes", "Git", "Jira", "Salesforce"]
        found_tools = [tool for tool in common_tools if tool.lower() in text_lower]
        if found_tools:
            professional["tools"] = ", ".join(found_tools)
        
        # Industry/Sector extraction
        sector_patterns = [
            r"(?:in|for)\s+the\s+(\w+)\s+(?:sector|industry|field)",
            r"(\w+)\s+(?:sector|industry)",
            r"work(?:ing)?\s+in\s+(\w+)"
        ]
        for pattern in sector_patterns:
            match = re.search(pattern, text_lower)
            if match:
                sector = match.group(1)
                if sector not in ["the", "this", "that", "my"]:
                    professional["sector"] = sector
                    break
        
        return professional
    
    def _extract_goals(self, text: str) -> List[str]:
        """Extract goals and aspirations from text"""
        goals = []
        text_lower = text.lower()
        
        goal_indicators = [
            "goal is", "want to", "hope to", "plan to", "aim to", "aspire to",
            "looking to", "trying to", "working towards", "objective is",
            "move into", "transition to", "become a", "eventually"
        ]
        
        for indicator in goal_indicators:
            if indicator in text_lower:
                idx = text_lower.find(indicator)
                # Extract the goal statement (next 50-100 characters)
                goal_text = text[idx:idx + 100]
                # Find the sentence
                sentence_end = re.search(r'[.!?]', goal_text)
                if sentence_end:
                    goal = goal_text[:sentence_end.start()].strip()
                    if len(goal) > 10:
                        goals.append(goal)
        
        return goals
    
    def _extract_challenges(self, text: str) -> List[str]:
        """Extract challenges and pain points from text"""
        challenges = []
        text_lower = text.lower()
        
        challenge_indicators = [
            "challenge", "difficulty", "struggle", "problem", "issue", "hard to",
            "difficult to", "trouble", "pain point", "obstacle", "barrier"
        ]
        
        for indicator in challenge_indicators:
            if indicator in text_lower:
                idx = text_lower.find(indicator)
                # Extract context around the challenge
                start = max(0, idx - 50)
                end = min(len(text), idx + 100)
                challenge_text = text[start:end]
                
                # Find complete sentence
                sentences = re.split(r'[.!?]', challenge_text)
                for sentence in sentences:
                    if indicator in sentence.lower() and len(sentence.strip()) > 15:
                        challenges.append(sentence.strip())
                        break
        
        return challenges
    
    def _extract_preferences(self, text: str) -> Dict[str, str]:
        """Extract preferences and communication style"""
        preferences = {}
        text_lower = text.lower()
        
        # Communication style preferences
        if "short" in text_lower or "concise" in text_lower or "brief" in text_lower:
            preferences["communication_style"] = "concise"
        elif "detailed" in text_lower or "thorough" in text_lower or "comprehensive" in text_lower:
            preferences["communication_style"] = "detailed"
        
        if "practical" in text_lower or "hands-on" in text_lower:
            preferences["learning_style"] = "practical"
        elif "theory" in text_lower or "conceptual" in text_lower:
            preferences["learning_style"] = "theoretical"
        
        # Preference indicators
        prefer_patterns = [
            r"prefer (\w+(?:\s+\w+){0,3})",
            r"like (\w+(?:\s+\w+){0,3}) (?:better|more|instead)",
            r"instead of (\w+(?:\s+\w+){0,3})"
        ]
        for pattern in prefer_patterns:
            match = re.search(pattern, text_lower)
            if match:
                pref = match.group(1).strip()
                if len(pref) > 3:
                    preferences["preference"] = pref
                    break
        
        return preferences
    
    def _extract_traits(self, text: str) -> List[str]:
        """Extract personality traits from text"""
        traits = []
        text_lower = text.lower()
        
        # Trait indicators in first-person statements
        trait_patterns = {
            "analytical": ["analyze", "data-driven", "metrics", "analytical"],
            "detail-oriented": ["detail", "thorough", "precise", "accurate"],
            "collaborative": ["team", "collaborate", "work with others", "group"],
            "independent": ["independently", "self-motivated", "autonomous", "on my own"],
            "creative": ["creative", "innovative", "think outside", "new ideas"],
            "organized": ["organized", "structured", "systematic", "methodical"],
            "adaptable": ["adapt", "flexible", "change", "versatile"],
            "ambitious": ["ambitious", "driven", "motivated", "achieve"]
        }
        
        for trait, keywords in trait_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                traits.append(trait)
        
        return traits
    
    def _extract_domain_indicators(self, text: str) -> List[str]:
        """Extract domain/industry indicators from text"""
        indicators = []
        text_lower = text.lower()
        
        domain_keywords = {
            "retail": ["retail", "store", "customer", "sales", "merchandise", "shopping"],
            "education": ["student", "teacher", "school", "university", "course", "academic", "learning"],
            "healthcare": ["patient", "medical", "hospital", "clinic", "healthcare", "doctor", "nurse"],
            "finance": ["financial", "banking", "investment", "portfolio", "trading", "accounting"],
            "technology": ["software", "developer", "programming", "tech", "IT", "system", "application"],
            "manufacturing": ["production", "manufacturing", "factory", "assembly", "supply chain"],
            "marketing": ["marketing", "campaign", "brand", "advertising", "promotion"],
            "analytics": ["data", "analytics", "analysis", "insights", "metrics", "reporting"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                indicators.append(domain)
        
        return indicators
    
    def _extract_situation(self, text: str) -> List[str]:
        """Extract current situation descriptions"""
        situations = []
        text_lower = text.lower()
        
        situation_indicators = [
            "currently", "right now", "at the moment", "these days",
            "working on", "dealing with", "focused on"
        ]
        
        for indicator in situation_indicators:
            if indicator in text_lower:
                idx = text_lower.find(indicator)
                # Extract situational context
                context = text[idx:idx + 80]
                sentence_end = re.search(r'[.!?]', context)
                if sentence_end:
                    situation = context[:sentence_end.start()].strip()
                    if len(situation) > 10:
                        situations.append(situation)
        
        return situations
    
    def _extract_temporal_context(self, text: str) -> Dict[str, str]:
        """Extract time-related context"""
        temporal = {}
        
        # Extract timestamps if present
        timestamp_patterns = [
            r'"timestamp":\s*"([^"]+)"',
            r'"created_at":\s*"([^"]+)"',
            r'"date":\s*"([^"]+)"'
        ]
        for pattern in timestamp_patterns:
            match = re.search(pattern, text)
            if match:
                temporal["timestamp"] = match.group(1)
                break
        
        # Extract time references
        time_references = ["recently", "last week", "last month", "yesterday", "today", "this year"]
        for ref in time_references:
            if ref in text.lower():
                temporal["time_reference"] = ref
                break
        
        return temporal
    
    def _extract_relationships(self, text: str) -> List[str]:
        """Extract mentioned relationships"""
        relationships = []
        text_lower = text.lower()
        
        relationship_keywords = [
            "team", "manager", "colleague", "coworker", "supervisor", "boss",
            "client", "customer", "stakeholder", "partner", "vendor",
            "report to", "work with", "collaborate with"
        ]
        
        for keyword in relationship_keywords:
            if keyword in text_lower:
                relationships.append(keyword)
        
        return relationships
    
    def _extract_environment(self, text: str) -> Dict[str, str]:
        """Extract work environment information"""
        environment = {}
        text_lower = text.lower()
        
        # Work setting
        if "remote" in text_lower or "work from home" in text_lower:
            environment["work_setting"] = "remote"
        elif "office" in text_lower or "on-site" in text_lower:
            environment["work_setting"] = "office"
        elif "hybrid" in text_lower:
            environment["work_setting"] = "hybrid"
        
        # Company size indicators
        size_indicators = {
            "startup": ["startup", "small company", "small team"],
            "enterprise": ["large company", "enterprise", "corporation", "big company"],
            "mid-size": ["mid-size", "medium company"]
        }
        for size, keywords in size_indicators.items():
            if any(kw in text_lower for kw in keywords):
                environment["company_size"] = size
                break
        
        return environment
    
    def _determine_domain(self, indicators: List[str]) -> str:
        """Determine primary domain from indicators"""
        if not indicators:
            return "general"
        
        # Count frequency of each domain
        from collections import Counter
        domain_counts = Counter(indicators)
        
        # Return most common domain
        most_common = domain_counts.most_common(1)
        return most_common[0][0] if most_common else "general"
    
    def _build_persona_indicators(self) -> Dict[str, List[str]]:
        """Build dictionary of persona indicators"""
        return {
            "demographics": ["age", "gender", "location", "occupation", "role"],
            "professional": ["experience", "skills", "tools", "sector", "industry"],
            "goals": ["goal", "want", "hope", "plan", "aim", "aspire"],
            "challenges": ["challenge", "difficulty", "struggle", "problem"],
            "preferences": ["prefer", "like", "style", "approach"],
            "traits": ["personality", "characteristic", "trait", "behavior"]
        }
    
    def _build_context_indicators(self) -> Dict[str, List[str]]:
        """Build dictionary of context indicators"""
        return {
            "domain": ["industry", "sector", "field", "domain"],
            "situation": ["currently", "now", "working on", "dealing with"],
            "temporal": ["timestamp", "date", "time", "when", "recently"],
            "relationships": ["team", "manager", "colleague", "client"],
            "environment": ["office", "remote", "company", "organization"]
        }
    
    def format_persona_for_output(self, persona: PersonaExtraction) -> str:
        """Format persona extraction for human-readable output"""
        if not persona:
            return "Unable to extract persona information from the data."
        
        output_parts = []
        
        if persona.demographics:
            output_parts.append("**Demographics:**")
            for key, value in persona.demographics.items():
                output_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        if persona.professional:
            output_parts.append("\n**Professional Background:**")
            for key, value in persona.professional.items():
                output_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        if persona.goals:
            output_parts.append("\n**Goals & Aspirations:**")
            for goal in persona.goals:
                output_parts.append(f"- {goal}")
        
        if persona.challenges:
            output_parts.append("\n**Challenges:**")
            for challenge in persona.challenges:
                output_parts.append(f"- {challenge}")
        
        if persona.preferences:
            output_parts.append("\n**Preferences:**")
            for key, value in persona.preferences.items():
                output_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        if persona.traits:
            output_parts.append("\n**Personality Traits:**")
            output_parts.append(f"- {', '.join(persona.traits)}")
        
        output_parts.append(f"\n*Confidence Score: {persona.confidence_score:.2f}*")
        
        return "\n".join(output_parts)
    
    def format_context_for_output(self, context: ContextExtraction) -> str:
        """Format context extraction for human-readable output"""
        if not context:
            return "Unable to extract context information from the data."
        
        output_parts = []
        
        output_parts.append(f"**Domain:** {context.domain.title()}")
        output_parts.append(f"\n**Situation:** {context.situation}")
        
        if context.temporal:
            output_parts.append("\n**Temporal Context:**")
            for key, value in context.temporal.items():
                output_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        if context.relationships:
            output_parts.append("\n**Relationships:**")
            output_parts.append(f"- {', '.join(context.relationships)}")
        
        if context.environment:
            output_parts.append("\n**Environment:**")
            for key, value in context.environment.items():
                output_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        output_parts.append(f"\n*Confidence Score: {context.confidence_score:.2f}*")
        
        return "\n".join(output_parts)


# Global instance
_conversation_analyzer: Optional[ConversationAnalyzer] = None


def get_conversation_analyzer() -> ConversationAnalyzer:
    """Get the global conversation analyzer instance"""
    global _conversation_analyzer
    if _conversation_analyzer is None:
        _conversation_analyzer = ConversationAnalyzer()
    return _conversation_analyzer
