from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
from llm_client import LLMClient
from reflection_engine import ReflectionAnalysis

class SpecialFeatures:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def overthinking_interrupt(self, analysis: ReflectionAnalysis) -> Optional[str]:
        """Detects if a user is looping and provides a gentle interrupt."""
        if analysis.is_looping:
            return "lowkey you're looping on this — nothing new is getting added, just more stress 💀"
        return None

    async def pattern_callout(self, user_profile: Dict[str, Any], analysis: ReflectionAnalysis) -> Optional[str]:
        """Flags recurring themes based on long-term memory."""
        # Simple heuristic: if the current summary matches any stored patterns partially
        # In a real app, we'd use vector search (Chroma/FAISS) here
        for pattern in user_profile.get("patterns", []):
            if pattern.lower() in analysis.summary.lower():
                return f"ngl this feels similar to what you've mentioned before: '{pattern}'"
        return None

    async def say_it_clearly(self, message: str) -> str:
        """Converts a messy thought/rant into a clear emotional statement."""
        prompt = f"""Convert the following user rant into a single, clean, grounded emotional sentence. Use Gen Z tone but keep it clear and mature.
User: "{message}"
Clear Statement:"""
        response = await self.llm_client.client.chat.completions.create(
            model=self.llm_client.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    async def analyze_message_draft(self, draft: str) -> Dict[str, Any]:
        """Analyses a message draft (e.g., to an ex) and provides feedback."""
        prompt = f"""Analyze this message draft from a psychological and social perspective.
Input: "{draft}"

Output ONLY a JSON object:
- "rating": "✅" | "⚠️" | "❌"
- "feedback": "Short feedback on why."
- "suggestion": "A revised, more grounded version if needed."
"""
        response = await self.llm_client.client.chat.completions.create(
            model=self.llm_client.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
