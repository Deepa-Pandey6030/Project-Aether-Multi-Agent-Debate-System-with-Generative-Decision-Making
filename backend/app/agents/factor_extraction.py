"""
Factor Extraction Agent - Agent 1
Decides what is worth debating
"""

from typing import Dict, Any, List
import json
import uuid
from app.agents.base import BaseAgent
from app.models.debate import DebateState, AgentRole, Factor


class FactorExtractionAgent(BaseAgent):
    """
    Agent responsible for extracting decision factors from topic
    - Abstract, not literal
    - Selective, not exhaustive
    - Time-aware
    """
    
    def __init__(self):
        super().__init__(AgentRole.FACTOR_EXTRACTION)
    
    async def execute(self, state: DebateState, **kwargs) -> Dict[str, Any]:
        """
        Extract minimal set of decision factors
        
        Args:
            state: Current debate state
            
        Returns:
            Dict containing extracted factors
        """
        # Calculate max factors based on time budget
        max_factors = self._calculate_max_factors(state.time_budget)
        
        system_prompt = self._build_system_prompt(max_factors)
        user_prompt = self._build_user_prompt(state)
        
        response = await self._call_llm(
            system_prompt,
            user_prompt,
            debate_id=state.debate_id,
            event_prefix="factor_extraction",
        )
        
        # Parse factors from response
        factors = self._parse_factors(response)
        
        return {
            "factors": factors,
            "raw_response": response
        }
    
    def _calculate_max_factors(self, time_budget: int) -> int:
        """Determine how many factors to extract based on time"""
        if time_budget <= 300:  # 5 min
            return 1
        elif time_budget <= 600:  # 10 min
            return 2
        elif time_budget <= 900:  # 15 min
            return 3
        else:  # 20 min
            return 4
    
    def _build_system_prompt(self, max_factors: int) -> str:
        """Build system prompt for factor extraction"""
        return f"""You are the Factor Extraction Agent in Project AETHER.

Your role: Decide what is worth debating given limited time.

Key principles:
- Extract DIMENSIONS, not sentences
- Be ABSTRACT, not literal
- Be SELECTIVE, not exhaustive
- Drop low-impact or non-debatable factors
- Maximum {max_factors} factors

Output format (JSON):
{{
  "factors": [
    {{
      "name": "Short factor name",
      "description": "One sentence describing the dimension",
      "importance": 0.0-1.0
    }}
  ],
  "reasoning": "Why these factors matter most"
}}

Do NOT argue for or against anything. Just identify what's worth debating."""
    
    def _build_user_prompt(self, state: DebateState) -> str:
        """Build user prompt with topic and context"""
        prompt = f"Topic to analyze:\n{state.topic}\n\n"
        
        if state.time_budget:
            prompt += f"Time available: {state.time_budget} seconds\n\n"
        
        prompt += "Extract the minimal set of decision factors worth debating."
        
        return prompt
    
    def _parse_factors(self, response: str) -> List[Factor]:
        """Parse JSON response into Factor objects"""
        try:
            # Try to extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                
                factors = []
                for factor_data in data.get("factors", []):
                    factor = Factor(
                        id=str(uuid.uuid4()),
                        name=factor_data["name"],
                        description=factor_data["description"],
                        importance=factor_data.get("importance", 0.5)
                    )
                    factors.append(factor)
                
                return factors
            else:
                raise ValueError("No JSON found in response")
        
        except Exception as e:
            # Fallback: create a single generic factor
            print(f"Factor parsing error: {e}")
            return [
                Factor(
                    id=str(uuid.uuid4()),
                    name="Primary Decision Factor",
                    description="The main consideration for this decision",
                    importance=1.0
                )
            ]