#!/usr/bin/env python3
"""
Test the intelligent conversation analyzer with the sample conversation data
"""

import json
import sys
from light_ai.agents.conversation_analyzer import get_conversation_analyzer

# Sample conversation data
sample_conversation = {
    "conversation_id": "CONV-009",
    "messages": [
        {
            "role": "user",
            "timestamp": "2026-01-11T09:00:00Z",
            "content": "Hey, before we start, I want to tell you a bit about myself so you can respond better."
        },
        {
            "role": "assistant",
            "timestamp": "2026-01-11T09:00:05Z",
            "content": "Sure! Go ahead—I'll tailor my responses based on what you share."
        },
        {
            "role": "user",
            "timestamp": "2026-01-11T09:01:00Z",
            "content": "I'm a 31-year-old data analyst working in the retail sector. I've been in this field for around 7 years."
        },
        {
            "role": "assistant",
            "timestamp": "2026-01-11T09:01:10Z",
            "content": "Nice! I'll keep the retail and data-analytics context in mind."
        },
        {
            "role": "user",
            "timestamp": "2026-01-11T09:02:00Z",
            "content": "I mostly work with SQL, Python, and Power BI. I prefer short, practical answers instead of long theory."
        },
        {
            "role": "assistant",
            "timestamp": "2026-01-11T09:02:10Z",
            "content": "Got it—concise, practical, and tool-focused responses coming up."
        },
        {
            "role": "user",
            "timestamp": "2026-01-11T09:03:00Z",
            "content": "My current goal is to move into a senior analytics role and eventually lead a small team."
        },
        {
            "role": "assistant",
            "timestamp": "2026-01-11T09:03:10Z",
            "content": "That's a great goal. I'll align my advice toward leadership growth and senior-level thinking."
        },
        {
            "role": "user",
            "timestamp": "2026-01-11T09:04:00Z",
            "content": "One challenge I face is explaining technical insights to non-technical stakeholders."
        },
        {
            "role": "assistant",
            "timestamp": "2026-01-11T09:04:15Z",
            "content": "Understood. I'll focus on simple explanations, analogies, and business-friendly language for you."
        }
    ]
}

def main():
    print("=" * 80)
    print("Testing Intelligent Conversation Analyzer")
    print("=" * 80)
    print()
    
    # Get the analyzer
    analyzer = get_conversation_analyzer()
    
    # Analyze the conversation
    print("Analyzing conversation data...")
    print()
    
    persona, context = analyzer.analyze_data(sample_conversation)
    
    # Display results
    if persona:
        print("PERSONA EXTRACTION:")
        print("-" * 80)
        print(analyzer.format_persona_for_output(persona))
        print()
        print()
    else:
        print("ERROR: No persona extracted!")
        print()
    
    if context:
        print("CONTEXT EXTRACTION:")
        print("-" * 80)
        print(analyzer.format_context_for_output(context))
        print()
        print()
    else:
        print("ERROR: No context extracted!")
        print()
    
    # Show raw extraction data
    if persona:
        print("RAW PERSONA DATA:")
        print("-" * 80)
        print(f"Demographics: {persona.demographics}")
        print(f"Professional: {persona.professional}")
        print(f"Goals: {persona.goals}")
        print(f"Challenges: {persona.challenges}")
        print(f"Preferences: {persona.preferences}")
        print(f"Traits: {persona.traits}")
        print(f"Confidence: {persona.confidence_score:.2f}")
        print()
    
    if context:
        print("RAW CONTEXT DATA:")
        print("-" * 80)
        print(f"Domain: {context.domain}")
        print(f"Situation: {context.situation}")
        print(f"Temporal: {context.temporal}")
        print(f"Relationships: {context.relationships}")
        print(f"Environment: {context.environment}")
        print(f"Confidence: {context.confidence_score:.2f}")
        print()
    
    print("=" * 80)
    print("Test Complete!")
    print("=" * 80)
    
    return 0 if (persona and context) else 1

if __name__ == "__main__":
    sys.exit(main())
