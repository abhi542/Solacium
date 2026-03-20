import sys
try:
    import audioop
except ImportError:
    try:
        import audioop_lts as audioop
        sys.modules["audioop"] = audioop
    except ImportError:
        pass # Will fail later if needed

import os
import uuid
import json
import asyncio
import logging
import tempfile
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

from llm_client import LLMClient
from memory_system import MemorySystem
from reflection_engine import ReflectionEngine
from special_features import SpecialFeatures
from voice_journal import VoiceJournal

load_dotenv()

app = FastAPI(title="Gen Z Therapist (but actually good)")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
llm_client = LLMClient()
memory_system = MemorySystem()
reflection_engine = ReflectionEngine(llm_client)
special_features = SpecialFeatures(llm_client)
voice_journal = VoiceJournal()

class ChatRequest(BaseModel):
    user_id: str
    message: str

class AnalyzeRequest(BaseModel):
    message: str

class UpdateTitleRequest(BaseModel):
    title: str

@app.post("/session-action/rename/{session_id}")
async def update_session_title(session_id: str, request: UpdateTitleRequest):
    try:
        oid = ObjectId(session_id)
        await memory_system.update_session_title(session_id, request.title)
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Rename failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/session-action/delete/{session_id}")
async def delete_session(session_id: str):
    try:
        oid = ObjectId(session_id)
        await memory_system.sessions_collection.delete_one({"_id": oid})
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Delete failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/user-profile/{user_id}")
async def get_user_profile_data(user_id: str):
    user = await memory_system.users_collection.find_one({"user_id": user_id})
    if not user:
        return {"user_id": user_id, "session_ids": [], "status": "new"}
    return json.loads(json.dumps(user, default=str))

@app.post("/chat")
async def chat(request: ChatRequest):
    user_id = request.user_id
    message = request.message

    # 1. Get context
    history = await memory_system.get_recent_messages(user_id)
    user_profile = await memory_system.get_user_profile(user_id)

    # 2. Analyze reflection
    analysis = await reflection_engine.analyze(user_id, message, history)

    # 3. Check for special features (Overthinking interrupt, etc.) - SILENCED AS REQUESTED
    # interrupt = await special_features.overthinking_interrupt(analysis)
    # if interrupt:
    #     await memory_system.add_message(user_id, "user", message)
    #     await memory_system.add_message(user_id, "assistant", interrupt)
    #     return {"response": interrupt, "analysis": analysis.model_dump()}

    # 4. Generate AI response
    system_prompt = llm_client.get_system_prompt()
    # Add pattern context if available
    pattern_callout = await special_features.pattern_callout(user_profile, analysis)
    if pattern_callout:
        system_prompt += f"\n\nContext: {pattern_callout}"

    response = await llm_client.get_response(system_prompt, history + [{"role": "user", "content": message}])
    ai_content = response.choices[0].message.content

    # 5. Update Memory
    await memory_system.add_message(user_id, "user", message)
    await memory_system.add_message(user_id, "assistant", ai_content)
    
    # Update patterns if LLM detected a strong one (simplified)
    if analysis.is_looping:
        await memory_system.add_pattern(user_id, analysis.summary)

    return {
        "response": ai_content,
        "analysis": analysis.model_dump(),
        "pattern_callout": pattern_callout
    }

@app.get("/memory/{user_id}")
async def get_memory(user_id: str):
    profile = await memory_system.get_user_profile(user_id)
    return profile

@app.get("/sessions/{user_id}")
async def get_sessions(user_id: str):
    sessions = await memory_system.get_user_sessions(user_id)
    # Ensure every session has a title field for the frontend
    for s in sessions:
        if "title" not in s:
            # Fallback for old sessions
            user_msgs = [m for m in s.get("messages", []) if m["role"] == "user"]
            s["title"] = user_msgs[0]["content"][:40] if user_msgs else "New vibe 🥀"
    return sessions

@app.get("/session/{session_id}")
async def get_session_content(session_id: str):
    doc = await memory_system.sessions_collection.find_one({"_id": ObjectId(session_id)})
    if doc:
        # Load this session into active short-term memory
        user_id = doc.get("user_id")
        messages = doc.get("messages", []) # Fallback for split-schema docs
        
        if not messages:
             # Try to load from messages collection if it exists (legacy of my previous refactor)
             try:
                 messages = await memory_system.get_session_messages(session_id)
             except AttributeError:
                 messages = []

        if user_id:
             memory_system.short_term_memory[user_id] = messages
             memory_system.active_sessions[user_id] = session_id
        return {
            "messages": messages,
            "title": doc.get("title", "New vibe 🥀")
        }
    return {"messages": [], "title": "New vibe 🥀"}



@app.post("/session/save/{user_id}")
async def save_session(user_id: str):
    await memory_system.save_session(user_id)
    return {"status": "success"}

@app.post("/session/clear/{user_id}")
async def clear_session(user_id: str):
    memory_system.short_term_memory[user_id] = []
    if user_id in memory_system.active_sessions:
        del memory_system.active_sessions[user_id]
    return {"status": "success"}

@app.post("/analyze-message")
async def analyze_message(request: AnalyzeRequest):
    feedback = await special_features.analyze_message_draft(request.message)
    return feedback

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    temp_path = None
    try:
        logging.info(f"Received transcription request: {file.filename}")
        content = await file.read()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(content)
            temp_path = temp_audio.name

        # Transcribe using Vosk (expecting 16kHz Mono WAV from frontend)
        text = voice_journal.transcribe_audio(temp_path)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        temp_path = None
        
        logging.info(f"Transcription result: {text}")
        return {"text": text}
    except Exception as e:
        logging.error(f"Transcription failed: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            req = json.loads(data)
            user_id = req.get("user_id")
            message = req.get("message")

            if not user_id or not message:
                await websocket.send_text(json.dumps({"error": "Missing user_id or message"}))
                continue

            # (Similar logic to /chat but streaming)
            history = await memory_system.get_recent_messages(user_id)
            analysis = await reflection_engine.analyze(user_id, message, history)
            
            # Send analysis first
            await websocket.send_text(json.dumps({"type": "analysis", "data": analysis.model_dump()}))

            # Stream response
            system_prompt = llm_client.get_system_prompt()
            stream = await llm_client.get_response(
                system_prompt, 
                history + [{"role": "user", "content": message}],
                stream=True
            )

            full_response = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    await websocket.send_text(json.dumps({"type": "content", "data": content}))

            # Finalize
            await memory_system.add_message(user_id, "user", message)
            await memory_system.add_message(user_id, "assistant", full_response)
            await websocket.send_text(json.dumps({"type": "end"}))

    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
