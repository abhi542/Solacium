from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
from llm_client import LLMClient

class ReflectionAnalysis(BaseModel):
    emotions: List[str]
    intent: str  # venting, advice, overthinking, relationship, self-doubt
    distortions: List[str]  # overgeneralization, mind-reading, catastrophizing, none
    mode_selection: str  # Validate, Reality Check, Deep Dive
    is_looping: bool
    summary: str

class ReflectionEngine:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def analyze(self, user_id: str, message: str, history: List[Dict[str, str]]) -> ReflectionAnalysis:
        """Analyzes the user message for psychological markers."""
        
        # We'll use a specific analysis prompt for the LLM
        analysis_prompt = f"""Analyze the following user message within the context of their recent chat history.
Extract structured psychological insights.

Output ONLY a JSON object with the following keys:
- "emotions": [list of strings] (e.g., ["anxiety", "frustration"])
- "intent": "venting" | "advice" | "overthinking" | "relationship" | "self-doubt"
- "distortions": [list of strings] (from: "overgeneralization", "mind reading", "catastrophizing", "all-or-nothing thinking", "none")
- "mode_selection": "Validate" | "Reality Check" | "Deep Dive"
- "is_looping": boolean (is the user repeating the same thought or story without progress?)
- "summary": a one-sentence summary of the core issue

User Message: "{message}"
Recent History: {history[-5:] if history else "No history"}

Note: If the message is highly emotional, select "Validate". If it contains clear logical fallacies, select "Reality Check". If it's complex or vague, select "Deep Dive"."""

        # Call the LLM (non-streaming for analysis)
        response = await self.llm_client.client.chat.completions.create(
            model=self.llm_client.model,
            messages=[{"role": "system", "content": "You are a psychological analysis engine. Output ONLY JSON."},
                      {"role": "user", "content": analysis_prompt}],
            response_format={"type": "json_object"}
        )
        
        analysis_data = json.loads(response.choices[0].message.content)
        return ReflectionAnalysis(**analysis_data)
