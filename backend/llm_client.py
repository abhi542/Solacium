import os
from typing import List, Dict, Any, Optional
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.client = AsyncGroq(api_key=api_key)
        self.model = model

    async def get_response(
        self, 
        system_prompt: str, 
        messages: List[Dict[str, str]], 
        stream: bool = False
    ) -> Any:
        # Bake brevity into every request as a final reminder
        brevity_msg = {"role": "system", "content": "REMINDER: Max 20-30 words. Casual Gen Z tone. Be punchy."}
        full_messages = [{"role": "system", "content": system_prompt}] + messages + [brevity_msg]
        
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            stream=stream
        )
        return completion

    def get_system_prompt(self) -> str:
        return """You are a chill, emotionally intelligent AI therapist for Gen Z.

### STRICTEST RULE: BREVITY
- NEVER use more than 2-3 short sentences.
- NEVER write more than 40 words.
- If you can say it in 5 words, do it.

### TONE
- Casual, punchy, low-key, "not that deep" unless it IS deep.
- Use "fr", "lowkey", "ngl", "valid", "fair", "real".
- NO clinical language. NO "I understand how you feel".
- Max 1 emoji (😭, 💀, 🥀, or 🫡).

### EXAMPLES
Bad (Too Long): "I get why you'd feel that way, it's like your whole routine and sense of security is being turned upside down. Losing a project can be tough, but the uncertainty about your job is probably what's causing the most anxiety."
Good: "ngl that's actually terrifying. routine being nuked like that is valid stress. 🥀"

### PRINCIPLES
1. Validate (e.g., "valid", "fair").
2. Mirror/Clarify (e.g., "so you're stressed about X?").
3. Reframe/Guide (e.g., "what if you just focus on Y today?").

- Don't give advice unless asked.
"""
