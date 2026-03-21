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
        analysis_prompt = f"""Analyze this user message and return psychological markers.
Message: {message}

Return ONLY a flat JSON object. No markdown, no backticks, no preamble.

{{
  "emotions": ["emotion1", "emotion2"],
  "intent": "venting" | "advice" | "overthinking" | "relationship" | "self-doubt",
  "distortions": ["dist1", "dist2"],
  "mode_selection": "Validate" | "Reality Check" | "Deep Dive",
  "is_looping": boolean,
  "summary": "one sentence summary"
}}

Rules:
- summary MUST be under 15 words and have NO newlines.
- intent MUST be one of the listed 5 options.
- mode_selection MUST be one of the 3 options.
- If unsure, use "Deep Dive" and "venting"."""

        try:
            response = await self.llm_client.client.chat.completions.create(
                model=self.llm_client.model,
                messages=[
                    {"role": "system", "content": "You are a JSON-only API. Never use markdown. Never use backticks. Output absolute valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=512,
                temperature=0.1 # Low temperature for more stable JSON
            )
            
            raw_content = response.choices[0].message.content
            analysis_data = json.loads(raw_content)
            return ReflectionAnalysis(**analysis_data)
            
        except Exception as e:
            print(f"Reflection Analysis failed: {e}")
            # Fallback to a safe default if JSON fails
            return ReflectionAnalysis(
                emotions=["processing"],
                intent="venting",
                distortions=["none"],
                mode_selection="Validate",
                is_looping=False,
                summary="Just vibing and processing... 🥀"
            )
