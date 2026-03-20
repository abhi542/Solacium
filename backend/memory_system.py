import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

class MemorySystem:
    def __init__(self):
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            raise ValueError("MONGODB_URI not found in environment variables")
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[os.getenv("DB_NAME", "genz_therapy")]
        self.users_collection = self.db["users"]
        self.sessions_collection = self.db["sessions"] # Renamed from conversations for clarity
        # In-memory short-term buffer per user session (user_id -> list of messages)
        self.short_term_memory: Dict[str, List[Dict[str, str]]] = {}
        # Tracks which session is currently active per user (user_id -> session_id)
        self.active_sessions: Dict[str, str] = {}

    async def get_recent_messages(self, user_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """Retrieves last N messages from short-term buffer."""
        if user_id not in self.short_term_memory:
            self.short_term_memory[user_id] = []
        return self.short_term_memory[user_id]

    async def add_message(self, user_id: str, role: str, content: str):
        """Adds a message to the short-term buffer."""
        if user_id not in self.short_term_memory:
            self.short_term_memory[user_id] = []
        
        self.short_term_memory[user_id].append({"role": role, "content": content})
        
        # Keep buffer at 20 messages
        if len(self.short_term_memory[user_id]) > 20:
            self.short_term_memory[user_id] = self.short_term_memory[user_id][-20:]

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves all past conversation sessions for a user."""
        cursor = self.sessions_collection.find(
            {"user_id": user_id},
            {"messages": 1, "timestamp": 1, "title": 1, "_id": 1}
        ).sort("timestamp", -1)
        
        sessions = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            sessions.append(doc)
        return sessions

    async def save_session(self, user_id: str):
        """Persists the current short-term buffer. Updates active session if exists, else inserts new."""
        if user_id in self.short_term_memory and len(self.short_term_memory[user_id]) > 0:
            active_id = self.active_sessions.get(user_id)
            now = datetime.now()
            from bson import ObjectId

            if active_id:
                # UPDATE existing active session
                await self.sessions_collection.update_one(
                    {"_id": ObjectId(active_id)},
                    {"$set": {"messages": self.short_term_memory[user_id], "updated_at": now}}
                )
                return active_id
            else:
                # INSERT new session
                title = "New vibe 🥀"
                for msg in self.short_term_memory[user_id]:
                    if msg["role"] == "user":
                        content = msg["content"]
                        title = content[:40] + ("..." if len(content) > 40 else "")
                        break
                
                res = await self.sessions_collection.insert_one({
                    "user_id": user_id,
                    "title": title,
                    "messages": self.short_term_memory[user_id],
                    "timestamp": now,
                    "updated_at": now
                })
                session_id = str(res.inserted_id)
                self.active_sessions[user_id] = session_id

                await self.users_collection.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {"last_active": now},
                        "$addToSet": {"session_ids": session_id}
                    },
                    upsert=True
                )
                return session_id

    async def update_session_title(self, session_id: str, new_title: str):
        """Updates the title of a specific session."""
        from bson import ObjectId
        await self.sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"title": new_title, "updated_at": datetime.now()}}
        )

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Retrieves patterns, emotional trends, etc., for a user."""
        profile = await self.users_collection.find_one({"user_id": user_id})
        if not profile:
            profile = {
                "user_id": user_id,
                "patterns": [],
                "emotional_trends": [],
                "past_events": [],
                "last_updated": datetime.now()
            }
            await self.users_collection.insert_one(profile)
        return profile

    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]):
        """Updates the user profile with new patterns or trends."""
        updates["last_updated"] = datetime.now()
        await self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": updates},
            upsert=True
        )

    async def add_pattern(self, user_id: str, pattern: str):
        """Adds a new pattern to the user profile."""
        await self.users_collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"patterns": pattern}, "$set": {"last_updated": datetime.now()}},
            upsert=True
        )
