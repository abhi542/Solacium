"use client";

import React, { useState, useEffect, useRef } from "react";
import { Send, Mic, Info, RefreshCcw, Search, MessageSquare, Plus, History, LogIn, User, Circle, PanelLeftClose, Trash2, Edit3, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Analysis {
  emotions: string[];
  intent: string;
  distortions: string[];
  mode_selection: string;
  is_looping: boolean;
  summary: string;
}

interface Session {
  _id: string;
  title: string;
  messages: Message[];
  timestamp: string;
}

// Robust WAV encoder helper
function encodeWAV(samples: Float32Array, sampleRate: number) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  const writeString = (view: DataView, offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  writeString(view, 0, "RIFF");
  view.setUint32(4, 32 + samples.length * 2, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // Mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(view, 36, "data");
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }

  return new Blob([buffer], { type: "audio/wav" });
}

export default function GenZTherapy() {
  const USER_ID = "abhinav_bhatt"; // Consistent User ID
  const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || "http://127.0.0.1:8000";
  const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000/ws/chat";

  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "yo, what's on your mind? keeping it real only. 🥀" }
  ]);
  const [input, setInput] = useState("");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(true); // Default logged in for demo
  const [sessions, setSessions] = useState<Session[]>([]);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const audioContext = useRef<AudioContext | null>(null);
  const processor = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingData = useRef<number[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "analysis") {
        setAnalysis(data.data);
      } else if (data.type === "content") {
        setIsTyping(false);
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          // Check if we should append to the last assistant message
          if (lastMsg && lastMsg.role === "assistant" &&
            !lastMsg.content.includes("yo, what's on your mind?") &&
            !lastMsg.content.includes("new session, fresh vibes.")) {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = { ...lastMsg, content: lastMsg.content + data.data };
            return newMessages;
          } else {
            return [...prev, { role: "assistant", content: data.data }];
          }
        });
      } else if (data.type === "end") {
        setIsTyping(false);
      }
    };

    setSocket(ws);
    return () => ws.close();
  }, [WS_URL]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Fetch sessions when history is opened
  useEffect(() => {
    if (showHistory) {
      fetchSessions();
    }
  }, [showHistory]);

  const fetchSessions = async () => {
    try {
      const resp = await fetch(`${BASE_URL}/sessions/${USER_ID}`);
      const data = await resp.json();
      if (Array.isArray(data)) {
        setSessions(data);
      } else {
        console.warn("Sessions data is not an array:", data);
        setSessions([]);
      }
    } catch (err) {
      console.error("Failed to fetch sessions", err);
      setSessions([]);
    }
  };

  const handleSend = () => {
    if (!input.trim() || !socket) return;

    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    socket.send(JSON.stringify({
      user_id: USER_ID,
      message: input
    }));

    setInput("");
  };

  const toggleRecording = async () => {
    if (isRecording) {
      setIsRecording(false);
      if (processor.current) processor.current.disconnect();
      if (audioContext.current) {
        if (audioContext.current.state !== 'closed') {
          audioContext.current.close().catch(console.error);
        }
      }
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());

      if (recordingData.current.length < 500) return;

      const samples = new Float32Array(recordingData.current);
      const wavBlob = encodeWAV(samples, 16000);
      const formData = new FormData();
      formData.append("file", wavBlob, "recording.wav");

      try {
        const response = await fetch(`${BASE_URL}/transcribe`, {
          method: "POST",
          body: formData,
        });
        const data = await response.json();
        if (data.text) {
          setInput((prev) => prev + (prev ? " " : "") + data.text);
        }
      } catch (error) {
        console.error("Transcription failed", error);
      }
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;
        const context = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
        audioContext.current = context;
        const source = context.createMediaStreamSource(stream);
        const scriptProcessor = context.createScriptProcessor(4096, 1, 1);
        processor.current = scriptProcessor;
        recordingData.current = [];
        scriptProcessor.onaudioprocess = (e) => {
          const inputData = e.inputBuffer.getChannelData(0);
          recordingData.current.push(...Array.from(inputData));
        };
        source.connect(scriptProcessor);
        scriptProcessor.connect(context.destination);
        setIsRecording(true);
      } catch (err) {
        alert("Please allow mic access. 🥀");
      }
    }
  };

  const startNewChat = async () => {
    const currentMessages = [...messages];
    // 1. Immediate UI Reset
    setMessages([{ role: "assistant", content: "new session, fresh vibes. what's up? 🥀" }]);
    setAnalysis(null);

    try {
      // 2. Background Saving/Clearing
      if (currentMessages.some(m => m.role === "user")) {
        await fetch(`${BASE_URL}/session/save/${USER_ID}`, { method: "POST" });
      }
      await fetch(`${BASE_URL}/session/clear/${USER_ID}`, { method: "POST" });
      fetchSessions(); // Update history list
    } catch (err) {
      console.error("Failed to sync new chat with backend", err);
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      const resp = await fetch(`${BASE_URL}/session/${sessionId}`);
      const data = await resp.json();
      if (data.messages && data.messages.length > 0) {
        // Prepend greeting if missing (fallback for old sessions)
        let loadedMessages = data.messages;
        if (loadedMessages[0].role !== "assistant") {
          loadedMessages = [{ role: "assistant", content: "yo, what's on your mind? keeping it real only. 🥀" }, ...loadedMessages];
        }
        setMessages(loadedMessages);
        setAnalysis(null);
        // On mobile, close history after loading
        if (window.innerWidth < 768) setShowHistory(false);
      }
    } catch (err) {
      console.error("Failed to load session", err);
    }
  };

  const handleRename = async (sessionId: string) => {
    if (!editTitle.trim()) return;
    console.log("Renaming session:", sessionId, "to:", editTitle);
    try {
      const resp = await fetch(`${BASE_URL}/session-action/rename/${sessionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: editTitle })
      });
      if (!resp.ok) throw new Error(await resp.text());
      console.log("Rename successful");
      setEditingSessionId(null);
      fetchSessions();
    } catch (err) {
      console.error("Failed to rename session:", err);
      alert("Rename failed. Check console. 🥀");
    }
  };

  const handleDelete = async (sessionId: string) => {
    if (!confirm("Delete this vibe forever? 🥀")) return;
    console.log("Deleting session:", sessionId);
    try {
      const resp = await fetch(`${BASE_URL}/session-action/delete/${sessionId}`, { method: "POST" });
      if (!resp.ok) throw new Error(await resp.text());
      console.log("Delete successful");
      fetchSessions();
    } catch (err) {
      console.error("Failed to delete session:", err);
      alert("Delete failed. Check console. 🥀");
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0c] text-zinc-100 font-sans selection:bg-purple-500/30 overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-zinc-800/50 backdrop-blur-md bg-zinc-900/30 sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <button onClick={startNewChat} className="p-2 hover:bg-zinc-800 rounded-xl transition-colors text-zinc-400 sm:hidden">
            <Plus className="w-5 h-5" />
          </button>
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-purple-600 to-pink-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
            <MessageSquare className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight">Gen Z Therapist</h1>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-medium">Therapy it seems</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowHistory(!showHistory)} className="p-2 hover:bg-zinc-800 rounded-xl transition-colors text-zinc-400" title="History">
            <History className="w-5 h-5" />
          </button>
          <button onClick={() => setShowInfo(!showInfo)} className="p-2 hover:bg-zinc-800 rounded-xl transition-colors text-zinc-400" title="Info">
            <Info className="w-5 h-5" />
          </button>
          <button
            onClick={() => setIsLoggedIn(!isLoggedIn)}
            className={cn(
              "p-2 rounded-xl transition-colors flex items-center gap-2 h-10 px-3",
              isLoggedIn ? "bg-zinc-800 text-zinc-100" : "bg-purple-600 text-white hover:bg-purple-700"
            )}
          >
            {isLoggedIn ? <User className="w-5 h-5" /> : <LogIn className="w-5 h-5" />}
            <span className="text-xs font-semibold hidden sm:inline">{isLoggedIn ? "Abhinav" : "Sign In"}</span>
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar History (ChatGPT Style) */}
        <AnimatePresence>
          {showHistory && isLoggedIn && (
            <motion.aside
              initial={{ x: -280, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -280, opacity: 0 }}
              className="fixed inset-y-0 left-0 w-64 bg-[#0a0a0c] border-r border-[#1e1e20] p-3 flex flex-col gap-2 z-50 md:relative"
            >
              {/* Sidebar Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 bg-zinc-800 rounded-lg flex items-center justify-center">
                  <MessageSquare className="w-5 h-5 text-purple-400" />
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={fetchSessions}
                    className="p-2 hover:bg-zinc-800 rounded-lg text-zinc-500 transition-colors"
                    title="Refresh history"
                  >
                    <RefreshCcw className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setShowHistory(false)}
                    className="p-2 hover:bg-zinc-800 rounded-lg text-zinc-500 transition-colors"
                  >
                    <PanelLeftClose className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* New Chat Button */}
              <button
                onClick={startNewChat}
                className="w-full h-11 flex items-center gap-3 px-3 rounded-xl hover:bg-zinc-800/50 transition-colors text-zinc-200 group border border-zinc-800/30 font-medium"
              >
                <div className="w-5 h-5 flex items-center justify-center">
                  <Plus className="w-4 h-4" />
                </div>
                <span className="text-sm">New chat</span>
              </button>

              {/* Search */}
              <div className="relative mt-2">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input
                  type="text"
                  placeholder="Search chats"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full h-11 bg-transparent border border-zinc-800/30 rounded-xl pl-10 pr-3 text-sm focus:outline-none focus:border-zinc-700 transition-colors placeholder:text-zinc-600"
                />
              </div>

              {/* Scrollable List */}
              <div className="flex-1 mt-4 overflow-y-auto px-1 custom-scrollbar space-y-1">
                {(sessions || [])
                  .filter(s => (s.title || "New vibe").toLowerCase().includes(searchQuery.toLowerCase()))
                  .map(s => (
                    <div
                      key={s._id}
                      className="group relative flex items-center"
                    >
                      {editingSessionId === s._id ? (
                        <div className="flex-1 flex items-center gap-2 p-2 bg-zinc-800 rounded-lg">
                          <input
                            autoFocus
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleRename(s._id)}
                            className="flex-1 bg-transparent border-none outline-none text-xs text-white"
                          />
                          <button
                            onClick={() => handleRename(s._id)}
                            className="text-emerald-500 hover:text-emerald-400 p-1"
                          >
                            <Plus className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => setEditingSessionId(null)}
                            className="text-zinc-500 hover:text-zinc-400 p-1"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex-1 relative flex items-center group/item">
                          <button
                            onClick={() => loadSession(s._id)}
                            className="flex-1 text-left p-3 rounded-lg hover:bg-zinc-800/50 transition-all text-xs text-zinc-400 hover:text-white truncate pr-16"
                          >
                            {s.title || "New vibe 🥀"}
                          </button>
                          <div className="absolute right-2 flex gap-1 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setEditingSessionId(s._id);
                                setEditTitle(s.title || "");
                              }}
                              className="p-1.5 text-zinc-500 hover:text-purple-400 hover:bg-zinc-800 rounded-md transition-all"
                              title="Rename"
                            >
                              <Edit3 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(s._id);
                              }}
                              className="p-1.5 text-zinc-500 hover:text-red-400 hover:bg-zinc-800 rounded-md transition-all"
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Main Chat Area */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scrollbar-hide relative bg-[radial-gradient(circle_at_50%_0%,_#1a1a20_0%,_#0a0a0c_100%)]">
          <div className="max-w-2xl mx-auto space-y-6 pb-40">
            <AnimatePresence initial={false}>
              {messages.map((msg, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 10, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  className={cn(
                    "flex",
                    msg.role === "user" ? "justify-end" : "justify-start"
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[85%] px-5 py-3 rounded-[24px] text-sm leading-relaxed",
                      msg.role === "user"
                        ? "bg-zinc-100 text-zinc-900 rounded-tr-none font-medium shadow-[0_20px_60px_-15px_rgba(0,0,0,0.5)]"
                        : "bg-zinc-800/80 text-zinc-100 rounded-tl-none border border-zinc-700/50 backdrop-blur-sm shadow-xl shadow-black/60"
                    )}
                  >
                    {msg.content}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            {isTyping && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="bg-zinc-800/50 px-5 py-3 rounded-[24px] rounded-tl-none flex gap-1 items-center">
                  <span className="w-1 h-1 bg-zinc-400 rounded-full animate-bounce" />
                  <span className="w-1 h-1 bg-zinc-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                  <span className="w-1 h-1 bg-zinc-400 rounded-full animate-bounce [animation-delay:0.4s]" />
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Floated Input UI Container */}
          <div className="fixed bottom-0 left-0 right-0 p-4 md:p-8 bg-gradient-to-t from-[#0a0a0c] via-[#0a0a0c]/90 to-transparent pointer-events-none">
            <div className="max-w-2xl mx-auto pointer-events-auto">

              {/* Input Area */}
              <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-[32px] blur opacity-0 group-focus-within:opacity-100 transition duration-500" />
                <div className={cn(
                  "relative flex items-center bg-zinc-900/80 border border-zinc-800 rounded-[28px] p-2 pr-3 shadow-2xl backdrop-blur-md focus-within:border-zinc-700 transition-all",
                  isRecording && "border-red-500/50 bg-red-500/10"
                )}>
                  <button
                    onClick={toggleRecording}
                    className={cn(
                      "p-3 rounded-full transition-all group/mic flex items-center justify-center relative overflow-hidden",
                      isRecording ? "bg-red-500 text-white" : "text-zinc-500 hover:text-zinc-300"
                    )}
                  >
                    {isRecording && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: [1, 1.5, 1] }}
                        transition={{ repeat: Infinity, duration: 1 }}
                        className="absolute inset-0 bg-red-400/30 rounded-full"
                      />
                    )}
                    <Mic className="w-5 h-5 relative z-10" />
                  </button>
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    placeholder={isRecording ? "Listening closely... (Click again to stop)" : "What's been happening?"}
                    className="flex-1 bg-transparent px-2 py-3 outline-none text-sm placeholder:text-zinc-600"
                  />
                  <div className="flex items-center gap-1">
                    <button onClick={startNewChat} className="p-2 text-zinc-500 hover:text-zinc-300 transition-colors hidden sm:block" title="New Chat">
                      <Plus className="w-4 h-4" />
                    </button>
                    <button
                      onClick={handleSend}
                      disabled={!input.trim()}
                      className="bg-zinc-100 text-zinc-950 p-3 rounded-2xl hover:bg-white disabled:opacity-50 disabled:hover:bg-zinc-100 transition-all shadow-lg active:scale-95 ml-2"
                    >
                      <Send className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
              <p className="text-center text-[10px] text-zinc-600 mt-4 uppercase tracking-[0.2em] font-medium opacity-50">
                Not a therapist. 🥀
              </p>
            </div>
          </div>
        </main>

        {/* Info Sidebar (Desktop Right) */}
        {showInfo && (
          <motion.aside
            initial={{ x: 300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 300, opacity: 0 }}
            className="w-72 border-l border-zinc-800/50 bg-zinc-900/20 backdrop-blur-xl p-6 hidden lg:flex flex-col gap-6 z-10"
          >
            <h2 className="text-xs font-bold uppercase tracking-widest text-zinc-500">About the AI</h2>
            <div className="space-y-4">
              <div className="p-4 bg-zinc-800/30 rounded-2xl border border-zinc-800">
                <h3 className="text-sm font-semibold mb-2">Psychological Core</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">
                  Uses grounded CBT principles focused on validation and reframing.
                </p>
              </div>
              <div className="p-4 bg-zinc-800/30 rounded-2xl border border-zinc-800">
                <h3 className="text-sm font-semibold mb-2">Gen Z Tone</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">
                  Communicates in a natural, casual dialect to make emotional clarity accessible.
                </p>
              </div>
              <div className="mt-8">
                <div className="text-[10px] text-zinc-600 uppercase font-bold mb-2">Safety Note</div>
                <p className="text-[10px] text-zinc-500 leading-relaxed">
                  If you're in crisis, please hit up a real human at 988 or your local help line. 🥀
                </p>
              </div>
            </div>
          </motion.aside>
        )}
      </div>
    </div>
  );
}
