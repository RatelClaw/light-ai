"""
Base agent configuration and utilities for AI agents.

This module provides the foundation for all AI agents in the system,
using OpenAI client with OpenRouter for simple, direct AI integration.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from openai import OpenAI
from light_ai.config import Config, get_config


@dataclass
class AgentConfig:
    """Configuration for AI agents."""
    name: str
    model_name: str
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout_seconds: int = 60
    system_prompt: str = ""


class BaseAgent:
    """
    Base class for all AI agents in the system.
    
    Uses OpenAI client with OpenRouter for simple, direct AI integration.
    """
    
    def __init__(self, agent_config: AgentConfig, config: Optional[Config] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_config: Agent-specific configuration
            config: Global system configuration (optional)
        """
        self.agent_config = agent_config
        self.config = config or get_config()
        self.logger = self._setup_logging()
        self.client = self._create_openai_client()
        
        self.logger.info(f"Initialized {agent_config.name} agent")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the agent."""
        logger = logging.getLogger(f"light_ai.agents.{self.agent_config.name}")
        logger.setLevel(getattr(logging, self.config.logging.level))
        
        # Create formatter for agent logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add console handler if not already present
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _create_openai_client(self) -> OpenAI:
        """Create OpenAI client configured for OpenRouter."""
        client = OpenAI(
            api_key=self.config.openrouter.api_key,
            base_url=self.config.openrouter.base_url,
            timeout=self.agent_config.timeout_seconds
        )
        
        self.logger.info(f"Created OpenAI client for model: {self.agent_config.model_name}")
        return client
    
    async def execute(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a prompt with the agent.
        
        Args:
            prompt: The prompt to execute
            context: Optional context information
            
        Returns:
            Agent response as string
        """
        try:
            self.logger.debug(f"Executing prompt: {prompt[:100]}...")
            
            # Build messages
            messages = []
            
            # Add system prompt
            if self.agent_config.system_prompt:
                messages.append({
                    "role": "system",
                    "content": self.agent_config.system_prompt
                })
            
            # Add context if provided
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                full_prompt = f"Context:\n{context_str}\n\nQuery: {prompt}"
            else:
                full_prompt = prompt
            
            messages.append({
                "role": "user",
                "content": full_prompt
            })
            
            # Execute with OpenAI client
            response = self.client.chat.completions.create(
                model=self.agent_config.model_name,
                messages=messages,
                temperature=self.agent_config.temperature,
                max_tokens=self.agent_config.max_tokens
            )
            
            result = response.choices[0].message.content
            self.logger.debug(f"Agent response: {result[:100]}...")
            return result
            
        except Exception as e:
            self.logger.error(f"Agent execution failed: {str(e)}")
            raise
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the agent."""
        return {
            "name": self.agent_config.name,
            "model": self.agent_config.model_name,
            "temperature": self.agent_config.temperature,
            "max_tokens": self.agent_config.max_tokens,
            "system_prompt_length": len(self.agent_config.system_prompt)
        }