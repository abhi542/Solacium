# Solacium


Solacium is a premium, AI-powered mental health companion designed specifically for the Gen Z era. It combines deep psychological reflection with a modern, high-tier aesthetic to help you navigate life's chaos without the "cringe."

---

## ✨ Features

- **🧠 Reflection Engine**: Real-time analysis of your emotional state using our custom reflection logic.
- **🎙️ Voice Journaling**: Integrated voice-to-text transcription powered by Vosk, allowing you to vent out loud.
- **📼 Multimodal Memory**: A hierarchical database schema that remembers your "vibe" across sessions.
- **🌑 Premium Dark Mode**: A sleek, glassmorphic UI built for maximum comfort and high-end feel.
- **💬 Vibe-Encoded Chat**: AI responses that actually speak your language, avoiding clinical boredom.

## 🛠️ Tech Stack

### **Frontend**
- **Next.js 15+** (App Router)
- **Tailwind CSS** (Custom Design System)
- **Lucide Icons**
- **Framer Motion** (Subtle Micro-animations)

### **Backend**
- **FastAPI** (High-performance Python framework)
- **MongoDB** (Motor for async ORM)
- **Vosk API** (Local, privacy-first STT)
- **OpenAI/OpenRouter** (Deep Emotional Logic)

---

## 🏗️ Technical Architecture

### **Core Components**
- **Reflection Engine (Backend)**: Uses specialized prompts to analyze user emotional state, identifying patterns like overthinking, looping, or anxiety.
- **Vibe Tracker (Memory)**: A stateful memory system that bridges short-term buffers with long-term MongoDB persistence.
- **Streaming Pipeline**: Real-time WebSocket connection (`/ws/chat`) for low-latency AI responses with embedded emotional analysis.
- **Audio Processor**: Local Vosk-based STT (Speech-to-Text) for privacy-first voice journaling.

---

## 📡 API Reference

### **Session Management**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions/{user_id}` | `GET` | Retrieve metadata-only list of all sessions for a user. |
| `/session/{session_id}` | `GET` | Retrieve full message history for a specific session. |
| `/session/save/{user_id}` | `POST` | Upsert the current in-memory buffer to the database. |
| `/session/clear/{user_id}` | `POST` | Clear the active short-term memory and session pointer. |
| `/session-action/rename/{id}`| `POST` | Update the `title` attribute of a session document. |
| `/session-action/delete/{id}`| `POST` | Delete session metadata and associated messages. |

### **Communication & AI**
| Endpoint | Type | Description |
|----------|------|-------------|
| `/ws/chat` | `WS` | Bidirectional stream for user messages and AI analysis/responses. |
| `/transcribe` | `POST` | Process 16kHz Mono WAV files into text using local Vosk models. |
| `/analyze-message` | `POST` | Pre-submission analysis for emotional tone or overthinking. |

---

## 🚀 Getting Started

### **Prerequisites**
- Python 3.10+
- Node.js 18+
- MongoDB (Local or Atlas)

### **1. Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  
# or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  
# Add your MONGODB_URI and OPENAI_API_KEY
python3 main.py
```

### **2. Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to start your session.

---

## 📑 Environment Variables

### **Backend (.env)**
| Variable | Description |
|----------|-------------|
| `MONGODB_URI` | Your MongoDB connection string |
| `DB_NAME` | Database name (default: genz_therapy) |
| `OPENAI_API_KEY` | Your AI model provider key |

### **Frontend (.env.local)**
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_BASE_URL` | http://localhost:8000 (Backend API) |
| `NEXT_PUBLIC_WS_URL` | ws://localhost:8000/ws/chat (Backend WebSocket) |

---
## Screenshot of Web App in action 

<img width="2940" height="1602" alt="image" src="https://github.com/user-attachments/assets/aa259966-9bdc-4afd-8e2b-cc662ef4d8f2" />

---

## License
Distributed under the MIT License. Developed by [abhinavbhatt](https://github.com/abhi542).

