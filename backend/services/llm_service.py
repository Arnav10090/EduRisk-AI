"""
LLM integration service for generating AI-powered risk summaries.

This module provides the LLMService class that integrates with Groq API
to generate natural language explanations of student placement risk assessments.
Supports both Groq and Anthropic Claude APIs.
"""

import asyncio
from typing import Dict, List, Optional
import os

try:
    import anthropic
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class LLMService:
    """
    Service for generating AI-powered risk summaries using Groq or Claude API.
    
    This service generates concise, plain-English explanations of student
    placement risk assessments for loan officers. It supports both Groq
    (default, free tier available) and Anthropic Claude APIs.
    
    Requirements:
        - 6.1: Generate natural language risk summary using LLM API
        - 6.2: Use high-quality language model
        - 6.3: Include student data and risk factors in prompt
        - 6.4: Limit summary to 2 sentences maximum
        - 6.5: Start summary with risk level and primary driver
        - 6.7: Provide fallback on API failures
    """
    
    def __init__(self, api_key: str, provider: str = "groq"):
        """
        Initialize LLM service with API credentials.
        
        Args:
            api_key: API key for authentication (Groq or Anthropic)
            provider: LLM provider - "groq" (default) or "anthropic"
        """
        self.provider = provider.lower()
        self.api_key = api_key
        
        if self.provider == "groq":
            if not GROQ_AVAILABLE:
                raise ImportError("groq package not installed. Run: pip install groq")
            self.client = AsyncGroq(api_key=api_key)
            self.model = "llama-3.3-70b-versatile"  # Fast and high quality
        elif self.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            self.client = AsyncAnthropic(api_key=api_key)
            self.model = "claude-sonnet-4-20250514"
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'groq' or 'anthropic'")
        
        self.max_tokens = 200
        self.temperature = 0.3
        self.timeout = 5.0  # seconds
        self.fallback_message = (
            "AI summary unavailable - refer to SHAP values for risk drivers."
        )
    
    async def generate_summary(
        self,
        student_data: Dict,
        prediction: Dict,
        top_risk_drivers: List[Dict]
    ) -> str:
        """
        Generate a natural language risk summary for a student.
        
        Creates a 2-sentence plain-English explanation of the student's
        placement risk assessment, suitable for loan officers without
        technical ML knowledge.
        
        Args:
            student_data: Dictionary containing student information with keys:
                - course_type: Type of course (e.g., "Engineering", "MBA")
                - institute_tier: Institute tier (1, 2, or 3)
                - cgpa: Student's CGPA
                - internship_count: Number of internships completed
            prediction: Dictionary containing prediction results with keys:
                - risk_score: Risk score from 0-100
                - risk_level: Risk level ("low", "medium", "high")
                - prob_placed_3m: 3-month placement probability
                - prob_placed_6m: 6-month placement probability
                - prob_placed_12m: 12-month placement probability
            top_risk_drivers: List of top 5 SHAP risk drivers, each with:
                - feature: Feature name
                - value: SHAP value
                - direction: "positive" or "negative"
        
        Returns:
            A 2-sentence natural language summary starting with risk level,
            or fallback message if API call fails.
        
        Requirements:
            - 6.1: Generate summary using Claude API
            - 6.2: Use claude-sonnet-4-20250514 model
            - 6.3: Include all required student and prediction data
            - 6.4: Limit to 2 sentences maximum
            - 6.5: Start with risk level and primary driver
            - 6.7: Return fallback message on API failures
        
        Examples:
            >>> service = LLMService(api_key="...")
            >>> summary = await service.generate_summary(
            ...     student_data={
            ...         "course_type": "Engineering",
            ...         "institute_tier": 2,
            ...         "cgpa": 7.5,
            ...         "internship_count": 1
            ...     },
            ...     prediction={
            ...         "risk_score": 45,
            ...         "risk_level": "medium",
            ...         "prob_placed_3m": 0.55,
            ...         "prob_placed_6m": 0.70,
            ...         "prob_placed_12m": 0.85
            ...     },
            ...     top_risk_drivers=[
            ...         {"feature": "internship_score", "value": -0.15, "direction": "negative"},
            ...         {"feature": "cgpa_normalized", "value": 0.08, "direction": "positive"}
            ...     ]
            ... )
            >>> print(summary)
            "Medium risk student with limited internship experience being the primary concern. 
            Decent CGPA provides some offset, but additional practical experience recommended."
        """
        try:
            # Build the prompt with student and prediction data
            prompt = self._build_prompt(student_data, prediction, top_risk_drivers)
            
            # Call LLM API based on provider
            if self.provider == "groq":
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a credit risk analyst at an Indian NBFC. Provide concise, professional risk assessments."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        max_tokens=self.max_tokens,
                        temperature=self.temperature
                    ),
                    timeout=self.timeout
                )
                summary = response.choices[0].message.content.strip()
                
            elif self.provider == "anthropic":
                response = await asyncio.wait_for(
                    self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    ),
                    timeout=self.timeout
                )
                summary = response.content[0].text.strip()
            
            return summary
            
        except asyncio.TimeoutError:
            # Timeout occurred
            return self.fallback_message
            
        except Exception as e:
            # Any API error (rate limit, auth, network, etc.)
            return self.fallback_message
    
    def _build_prompt(
        self,
        student_data: Dict,
        prediction: Dict,
        top_risk_drivers: List[Dict]
    ) -> str:
        """
        Build the prompt for Claude API with student and prediction data.
        
        Args:
            student_data: Student information dictionary
            prediction: Prediction results dictionary
            top_risk_drivers: List of top SHAP risk drivers
        
        Returns:
            Formatted prompt string for Claude API
        
        Requirements:
            - 6.3: Include course_type, institute_tier, cgpa, internship_count,
                   risk_score, risk_level, and top_risk_drivers in prompt
        """
        # Format top risk drivers for prompt
        drivers_text = ", ".join([
            f"{driver['feature']} ({driver['direction']})"
            for driver in top_risk_drivers[:3]  # Use top 3 for conciseness
        ])
        
        # Format placement probabilities as percentages
        prob_3m_pct = int(prediction["prob_placed_3m"] * 100)
        prob_6m_pct = int(prediction["prob_placed_6m"] * 100)
        prob_12m_pct = int(prediction["prob_placed_12m"] * 100)
        
        # Build the prompt
        prompt = f"""Given this student's placement risk assessment, write a 2-sentence plain-English summary for a loan officer.

Student: {student_data["course_type"]} from Tier-{student_data["institute_tier"]} institute, CGPA {student_data["cgpa"]}, {student_data["internship_count"]} internships
Risk score: {prediction["risk_score"]}/100 ({prediction["risk_level"]} risk)
Top risk drivers: {drivers_text}
Placement probability: 3m={prob_3m_pct}%, 6m={prob_6m_pct}%, 12m={prob_12m_pct}%

Write a concise, professional 2-sentence assessment. Start with the risk level and key reason."""
        
        return prompt
