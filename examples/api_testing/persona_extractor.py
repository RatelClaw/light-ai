"""
AI-Powered Persona and Context Extraction for API Testing

This module provides utilities to extract user personas and context from data patterns
to enable intelligent API testing and validation of persona-based adaptations.
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PersonaProfile:
    """Extracted persona profile from data analysis."""
    persona_type: str
    expertise_level: str
    domain_focus: List[str]
    analysis_preferences: Dict[str, str]
    technical_depth: str
    business_context: str
    confidence_score: float


@dataclass
class DataContext:
    """Extracted context from data content."""
    sector: str
    data_types: List[str]
    complexity_level: str
    business_metrics: List[str]
    analysis_opportunities: List[str]
    recommended_queries: List[str]


class PersonaExtractor:
    """Extract user personas and context from data patterns and query styles."""
    
    def __init__(self):
        self.persona_patterns = self._load_persona_patterns()
        self.sector_indicators = self._load_sector_indicators()
    
    def _load_persona_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load persona identification patterns."""
        return {
            "data_analyst": {
                "keywords": ["statistical", "correlation", "regression", "hypothesis", "p-value", "confidence interval"],
                "query_patterns": [
                    r"perform.*statistical.*analysis",
                    r"calculate.*significance",
                    r"test.*hypothesis",
                    r"correlation.*between",
                    r"regression.*model"
                ],
                "technical_indicators": ["SQL", "Python", "R", "statistical methods", "data modeling"],
                "complexity_preference": "high",
                "detail_level": "comprehensive"
            },
            "business_executive": {
                "keywords": ["ROI", "KPI", "strategic", "revenue", "profit", "market share", "competitive"],
                "query_patterns": [
                    r"what.*impact.*revenue",
                    r"strategic.*opportunities",
                    r"key.*performance.*indicators",
                    r"competitive.*position",
                    r"market.*analysis"
                ],
                "technical_indicators": ["dashboard", "executive summary", "high-level insights"],
                "complexity_preference": "medium",
                "detail_level": "summary"
            },
            "researcher": {
                "keywords": ["methodology", "peer-review", "publication", "experimental", "control group", "sample size"],
                "query_patterns": [
                    r"power.*analysis",
                    r"experimental.*design",
                    r"control.*group",
                    r"sample.*size",
                    r"methodology"
                ],
                "technical_indicators": ["research design", "statistical power", "publication quality"],
                "complexity_preference": "very_high",
                "detail_level": "rigorous"
            },
            "operations_manager": {
                "keywords": ["efficiency", "optimization", "process", "bottleneck", "throughput", "utilization"],
                "query_patterns": [
                    r"optimize.*process",
                    r"identify.*bottleneck",
                    r"improve.*efficiency",
                    r"reduce.*cost",
                    r"increase.*throughput"
                ],
                "technical_indicators": ["process improvement", "operational metrics", "cost reduction"],
                "complexity_preference": "medium",
                "detail_level": "actionable"
            },
            "marketing_specialist": {
                "keywords": ["campaign", "conversion", "engagement", "segmentation", "customer", "acquisition"],
                "query_patterns": [
                    r"customer.*segment",
                    r"campaign.*performance",
                    r"conversion.*rate",
                    r"customer.*lifetime.*value",
                    r"acquisition.*cost"
                ],
                "technical_indicators": ["marketing analytics", "customer insights", "campaign optimization"],
                "complexity_preference": "medium",
                "detail_level": "marketing_focused"
            }
        }
    
    def _load_sector_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Load sector identification indicators."""
        return {
            "healthcare": {
                "keywords": ["patient", "diagnosis", "treatment", "hospital", "clinical", "medical", "readmission"],
                "data_fields": ["patient_id", "diagnosis", "length_of_stay", "treatment_cost", "satisfaction_score"],
                "metrics": ["readmission_rate", "mortality_rate", "patient_satisfaction", "clinical_outcomes"]
            },
            "finance": {
                "keywords": ["loan", "credit", "risk", "portfolio", "investment", "capital", "default"],
                "data_fields": ["loan_amount", "credit_score", "risk_rating", "probability_of_default"],
                "metrics": ["value_at_risk", "return_on_investment", "default_rate", "capital_ratio"]
            },
            "retail": {
                "keywords": ["customer", "product", "sales", "inventory", "campaign", "conversion", "revenue"],
                "data_fields": ["customer_id", "product_id", "purchase_amount", "conversion_rate"],
                "metrics": ["customer_lifetime_value", "inventory_turnover", "sales_growth", "profit_margin"]
            },
            "manufacturing": {
                "keywords": ["production", "supplier", "inventory", "quality", "efficiency", "downtime"],
                "data_fields": ["facility_id", "supplier_id", "production_volume", "quality_score"],
                "metrics": ["capacity_utilization", "defect_rate", "on_time_delivery", "cost_per_unit"]
            },
            "education": {
                "keywords": ["student", "course", "grade", "performance", "learning", "retention"],
                "data_fields": ["student_id", "course_id", "gpa", "completion_rate"],
                "metrics": ["graduation_rate", "student_satisfaction", "learning_outcomes", "retention_rate"]
            },
            "real_estate": {
                "keywords": ["property", "price", "market", "neighborhood", "investment", "rental"],
                "data_fields": ["property_id", "listing_price", "square_feet", "neighborhood"],
                "metrics": ["price_per_sqft", "days_on_market", "rental_yield", "appreciation_rate"]
            },
            "technology": {
                "keywords": ["user", "feature", "engagement", "conversion", "platform", "subscription"],
                "data_fields": ["user_id", "session_count", "feature_usage", "subscription_tier"],
                "metrics": ["user_engagement", "churn_rate", "feature_adoption", "revenue_per_user"]
            }
        }
    
    def extract_persona_from_query(self, query: str) -> PersonaProfile:
        """Extract persona profile from a natural language query."""
        query_lower = query.lower()
        persona_scores = {}
        
        # Score each persona based on keyword and pattern matching
        for persona_name, patterns in self.persona_patterns.items():
            score = 0
            
            # Keyword matching
            for keyword in patterns["keywords"]:
                if keyword.lower() in query_lower:
                    score += 2
            
            # Pattern matching
            for pattern in patterns["query_patterns"]:
                if re.search(pattern, query_lower):
                    score += 3
            
            # Technical indicator matching
            for indicator in patterns["technical_indicators"]:
                if indicator.lower() in query_lower:
                    score += 1
            
            persona_scores[persona_name] = score
        
        # Find best matching persona
        best_persona = max(persona_scores, key=persona_scores.get)
        confidence = persona_scores[best_persona] / max(sum(persona_scores.values()), 1)
        
        patterns = self.persona_patterns[best_persona]
        
        return PersonaProfile(
            persona_type=best_persona,
            expertise_level=self._map_complexity_to_expertise(patterns["complexity_preference"]),
            domain_focus=patterns["technical_indicators"],
            analysis_preferences={
                "complexity": patterns["complexity_preference"],
                "detail_level": patterns["detail_level"],
                "technical_depth": patterns["complexity_preference"]
            },
            technical_depth=patterns["complexity_preference"],
            business_context=best_persona.replace("_", " ").title(),
            confidence_score=confidence
        )
    
    def extract_context_from_data(self, data: Dict[str, Any]) -> DataContext:
        """Extract context and sector information from data structure."""
        data_str = json.dumps(data).lower()
        sector_scores = {}
        
        # Score each sector based on keyword and field matching
        for sector_name, indicators in self.sector_indicators.items():
            score = 0
            
            # Keyword matching
            for keyword in indicators["keywords"]:
                score += data_str.count(keyword.lower()) * 2
            
            # Data field matching
            for field in indicators["data_fields"]:
                if field.lower() in data_str:
                    score += 3
            
            # Metrics matching
            for metric in indicators["metrics"]:
                if metric.lower() in data_str:
                    score += 1
            
            sector_scores[sector_name] = score
        
        # Find best matching sector
        best_sector = max(sector_scores, key=sector_scores.get)
        
        # Extract data characteristics
        data_types = self._identify_data_types(data)
        complexity_level = self._assess_complexity(data)
        business_metrics = self._extract_business_metrics(data, best_sector)
        analysis_opportunities = self._identify_analysis_opportunities(data, best_sector)
        recommended_queries = self._generate_recommended_queries(data, best_sector)
        
        return DataContext(
            sector=best_sector,
            data_types=data_types,
            complexity_level=complexity_level,
            business_metrics=business_metrics,
            analysis_opportunities=analysis_opportunities,
            recommended_queries=recommended_queries
        )
    
    def _map_complexity_to_expertise(self, complexity: str) -> str:
        """Map complexity preference to expertise level."""
        mapping = {
            "low": "Beginner",
            "medium": "Intermediate", 
            "high": "Advanced",
            "very_high": "Expert"
        }
        return mapping.get(complexity, "Intermediate")
    
    def _identify_data_types(self, data: Dict[str, Any]) -> List[str]:
        """Identify types of data present."""
        types = set()
        
        def analyze_value(value):
            if isinstance(value, dict):
                types.add("nested_objects")
                for v in value.values():
                    analyze_value(v)
            elif isinstance(value, list):
                types.add("arrays")
                for item in value:
                    analyze_value(item)
            elif isinstance(value, (int, float)):
                types.add("numerical")
            elif isinstance(value, str):
                types.add("categorical")
            elif isinstance(value, bool):
                types.add("boolean")
        
        analyze_value(data)
        return list(types)
    
    def _assess_complexity(self, data: Dict[str, Any]) -> str:
        """Assess the complexity level of the data."""
        def count_depth(obj, depth=0):
            if isinstance(obj, dict):
                return max([count_depth(v, depth + 1) for v in obj.values()] + [depth])
            elif isinstance(obj, list) and obj:
                return max([count_depth(item, depth + 1) for item in obj] + [depth])
            return depth
        
        max_depth = count_depth(data)
        total_fields = len(json.dumps(data).split(','))
        
        if max_depth > 4 or total_fields > 100:
            return "high"
        elif max_depth > 2 or total_fields > 50:
            return "medium"
        else:
            return "low"
    
    def _extract_business_metrics(self, data: Dict[str, Any], sector: str) -> List[str]:
        """Extract business metrics relevant to the sector."""
        data_str = json.dumps(data).lower()
        sector_metrics = self.sector_indicators.get(sector, {}).get("metrics", [])
        
        found_metrics = []
        for metric in sector_metrics:
            if metric.lower() in data_str:
                found_metrics.append(metric)
        
        return found_metrics
    
    def _identify_analysis_opportunities(self, data: Dict[str, Any], sector: str) -> List[str]:
        """Identify potential analysis opportunities."""
        opportunities = []
        
        # Generic opportunities based on data structure
        data_str = json.dumps(data).lower()
        
        if "rate" in data_str or "percentage" in data_str:
            opportunities.append("Rate and percentage analysis")
        
        if "cost" in data_str or "revenue" in data_str or "price" in data_str:
            opportunities.append("Financial impact analysis")
        
        if "time" in data_str or "date" in data_str:
            opportunities.append("Temporal trend analysis")
        
        if "score" in data_str or "rating" in data_str:
            opportunities.append("Performance benchmarking")
        
        # Sector-specific opportunities
        sector_opportunities = {
            "healthcare": ["Patient outcome analysis", "Cost-effectiveness studies", "Quality improvement"],
            "finance": ["Risk assessment", "Portfolio optimization", "Stress testing"],
            "retail": ["Customer segmentation", "Sales forecasting", "Inventory optimization"],
            "manufacturing": ["Process optimization", "Quality control", "Predictive maintenance"],
            "education": ["Learning outcome analysis", "Resource allocation", "Performance prediction"],
            "real_estate": ["Market analysis", "Investment evaluation", "Price prediction"],
            "technology": ["User behavior analysis", "Feature optimization", "Churn prediction"]
        }
        
        opportunities.extend(sector_opportunities.get(sector, []))
        return opportunities
    
    def _generate_recommended_queries(self, data: Dict[str, Any], sector: str) -> List[str]:
        """Generate recommended queries based on data and sector."""
        queries = []
        
        # Sector-specific query templates
        sector_queries = {
            "healthcare": [
                "What factors contribute most to patient readmission rates?",
                "How can we improve patient satisfaction scores?",
                "What is the relationship between treatment costs and outcomes?"
            ],
            "finance": [
                "What is our portfolio's risk-adjusted return?",
                "Which loans have the highest default probability?",
                "How would stress test scenarios impact our capital ratios?"
            ],
            "retail": [
                "Which customer segments provide the highest lifetime value?",
                "What products have the best profit margins?",
                "How effective are our marketing campaigns?"
            ],
            "manufacturing": [
                "Where are the bottlenecks in our production process?",
                "Which suppliers pose the highest risk?",
                "How can we optimize our inventory levels?"
            ],
            "education": [
                "What factors predict student success?",
                "How effectively are we using our resources?",
                "Which students are at risk of dropping out?"
            ],
            "real_estate": [
                "What are the market trends in different neighborhoods?",
                "Which properties offer the best investment opportunities?",
                "How do various factors affect property values?"
            ],
            "technology": [
                "What drives user engagement and retention?",
                "Which features are most valuable to users?",
                "How can we optimize our pricing strategy?"
            ]
        }
        
        return sector_queries.get(sector, [
            "What are the key trends in this data?",
            "What factors drive the most important outcomes?",
            "What opportunities exist for improvement?"
        ])


def load_test_data(file_path: str) -> Dict[str, Any]:
    """Load test data from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def analyze_test_scenario(data_file: str, query: str) -> Tuple[PersonaProfile, DataContext]:
    """Analyze a complete test scenario with data and query."""
    extractor = PersonaExtractor()
    
    # Load and analyze data
    data = load_test_data(data_file)
    data_context = extractor.extract_context_from_data(data)
    
    # Analyze query for persona
    persona_profile = extractor.extract_persona_from_query(query)
    
    return persona_profile, data_context


if __name__ == "__main__":
    # Example usage
    extractor = PersonaExtractor()
    
    # Test persona extraction
    test_queries = [
        "Perform a comprehensive statistical analysis of patient readmission patterns",
        "What are the key performance indicators driving our quarterly revenue?",
        "Conduct a power analysis for comparing treatment effectiveness",
        "Identify bottlenecks in our production process and calculate improvement potential",
        "Analyze customer lifetime value across different acquisition channels"
    ]
    
    print("Persona Extraction Results:")
    print("=" * 50)
    
    for query in test_queries:
        persona = extractor.extract_persona_from_query(query)
        print(f"\nQuery: {query}")
        print(f"Detected Persona: {persona.persona_type}")
        print(f"Expertise Level: {persona.expertise_level}")
        print(f"Confidence: {persona.confidence_score:.2f}")
        print(f"Technical Depth: {persona.technical_depth}")
    
    # Test data context extraction
    print("\n\nData Context Extraction Results:")
    print("=" * 50)
    
    # Example with healthcare data
    healthcare_data = {
        "patient_demographics": [
            {
                "patient_id": "PAT-001",
                "diagnosis": "Acute Myocardial Infarction",
                "length_of_stay": 7,
                "treatment_cost": 45000,
                "readmission_30_day": False,
                "satisfaction_score": 4.2
            }
        ],
        "clinical_metrics": {
            "readmission_rate": 0.25,
            "mortality_rate": 0.02,
            "patient_satisfaction": 4.33
        }
    }
    
    context = extractor.extract_context_from_data(healthcare_data)
    print(f"\nDetected Sector: {context.sector}")
    print(f"Data Types: {context.data_types}")
    print(f"Complexity: {context.complexity_level}")
    print(f"Business Metrics: {context.business_metrics}")
    print(f"Analysis Opportunities: {context.analysis_opportunities}")
    print(f"Recommended Queries: {context.recommended_queries}")