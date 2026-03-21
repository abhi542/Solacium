# Solacium 
> **"It's not just therapy, it's a vibe check."**

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

## 🚀 Getting Started

### **Prerequisites**
- Python 3.10+
- Node.js 18+
- MongoDB (Local or Atlas)

### **1. Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # Add your MONGODB_URI and OPENAI_API_KEY
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

---

## 🥀 License
Distributed under the MIT License. See `LICENSE` for more information.

Developed with 🥀 by [abhinavbhatt](https://github.com/abhi542)
