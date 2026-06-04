"use client";

import { useState, useEffect, useRef } from "react";
import { Send, Terminal, Cpu, User, Key, Trash2, Plus, AlertTriangle } from "lucide-react";

interface ApiKeyEntry {
  provider: string;
  key: string;
}

export default function Home() {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([
    { role: "ai", content: "System initialized. Multi-Tenant Key Architecture Active. Configure your cluster keys in the panel below, Chief." }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [token, setToken] = useState("");
  const [systemState, setSystemState] = useState("CONNECTED");
  
  // BYOK Key Pool States
  const [keyPool, setKeyPool] = useState<ApiKeyEntry[]>([]);
  const [selectedProvider, setSelectedProvider] = useState("gemini");
  const [inputKey, setInputKey] = useState("");

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load key pool from local storage on mount
  useEffect(() => {
    const savedPool = localStorage.getItem("jarvish_key_pool");
    if (savedPool) {
      try { setKeyPool(JSON.parse(savedPool)); } catch (e) { console.error(e); }
    }
  }, []);

  // Save key pool changes
  const savePool = (updatedPool: ApiKeyEntry[]) => {
    setKeyPool(updatedPool);
    localStorage.setItem("jarvish_key_pool", JSON.stringify(updatedPool));
  };

  const addKey = () => {
    if (!inputKey.trim()) return;
    const exists = keyPool.findIndex(k => k.provider === selectedProvider);
    let updated = [...keyPool];
    if (exists >= 0) {
      updated[exists].key = inputKey.trim();
    } else {
      updated.push({ provider: selectedProvider, key: inputKey.trim() });
    }
    savePool(updated);
    setInputKey("");
  };

  const removeKey = (provider: string) => {
    const updated = keyPool.filter(k => k.provider !== provider);
    savePool(updated);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(() => { scrollToBottom(); }, [messages]);

  // Authentication Handshake
  useEffect(() => {
    const authenticate = async () => {
      try {
        const formData = new URLSearchParams();
        formData.append("username", "Manish");
        formData.append("password", "admin123");

        const res = await fetch("http://127.0.0.1:8001/login", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: formData,
        });
        
        if (res.ok) {
          const data = await res.json();
          setToken(data.access_token);
        }
      } catch (error) {
        console.error("Core Engine Unreachable.", error);
      }
    };
    authenticate();
  }, []);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !token) return;

    const userText = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setIsLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8001/api/v1/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
          "X-Key-Pool": JSON.stringify(keyPool) 
        },
        body: JSON.stringify({ prompt: userText, session_id: "frontend-cluster-node" }),
      });

      const data = await res.json();

      // --- NEW ERROR HANDLING LOGIC ---
      if (!res.ok) {
        setSystemState("NODE_OFFLINE");
        setMessages((prev) => [...prev, { 
          role: "ai", 
          content: `CRITICAL ERROR [HTTP ${res.status}]: ${data.detail || "Connection refused."}` 
        }]);
        setIsLoading(false);
        return;
      }
      // --------------------------------

      setSystemState(data.system_state || "CLOUD_ACTIVE");
      
      setMessages((prev) => [...prev, { 
        role: "ai", 
        content: data.response || "No transmission received." 
      }]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "ai", content: "CRITICAL FAILURE: Pipeline routing disconnected." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100 font-sans">
      {/* Sidebar Control Deck */}
      <div className="w-80 border-r border-zinc-800 bg-zinc-900/40 p-4 hidden md:flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-2 mb-6 text-emerald-400">
            <Cpu size={22} />
            <h1 className="font-bold text-md tracking-wider">AI OS DESKTOP CORE</h1>
          </div>
          
          <div className="text-[10px] text-zinc-500 uppercase tracking-widest mb-3 font-semibold">Cluster Topology</div>
          <div className="space-y-2 mb-6 bg-zinc-950/50 p-3 rounded-lg border border-zinc-800 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-zinc-400">Node Connectivity:</span>
              <span className="text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span> Online
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-400">Active Pipeline Strategy:</span>
              <span className="text-zinc-300 font-mono text-[10px] bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-700 max-w-[120px] truncate">
                {systemState}
              </span>
            </div>
          </div>

          {/* BYOK Core Section */}
          <div className="text-[10px] text-zinc-500 uppercase tracking-widest mb-3 font-semibold flex items-center gap-1">
            <Key size={12} /> Dynamic Key Pool Management
          </div>

          {/* Key Input Fields */}
          <div className="space-y-2 bg-zinc-950/40 p-3 rounded-lg border border-zinc-800 mb-4">
            <select 
              value={selectedProvider} 
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 text-xs rounded p-2 focus:ring-1 focus:ring-emerald-500 outline-none text-zinc-200"
            >
              <option value="gemini">Google Gemini (Free/Paid)</option>
              <option value="groq">Groq Cloud (Free Tier)</option>
              <option value="openai">OpenAI GPT Architecture</option>
              <option value="deepseek">DeepSeek API Engine</option>
            </select>
            <div className="flex gap-2">
              <input 
                type="password"
                placeholder="Paste API authentication token..."
                value={inputKey}
                onChange={(e) => setInputKey(e.target.value)}
                className="flex-1 bg-zinc-900 border border-zinc-800 text-xs rounded p-2 focus:ring-1 focus:ring-emerald-500 outline-none font-mono text-zinc-300"
              />
              <button onClick={addKey} className="p-2 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 rounded transition-colors">
                <Plus size={14} />
              </button>
            </div>
          </div>

          {/* Key Pool Monitor */}
          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {keyPool.length === 0 ? (
              <div className="text-[11px] text-zinc-500 italic text-center py-2 flex items-center justify-center gap-1 bg-amber-500/5 rounded border border-amber-500/10 text-amber-500/80">
                <AlertTriangle size={12} /> No cluster keys active. Defaulting to Local Ollama Node.
              </div>
            ) : (
              keyPool.map((k) => (
                <div key={k.provider} className="flex items-center justify-between text-xs bg-zinc-900/80 border border-zinc-800 p-2 rounded">
                  <span className="font-mono text-zinc-300 uppercase text-[10px] bg-zinc-800 px-1.5 py-0.5 rounded border border-zinc-700">
                    {k.provider}
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="text-zinc-500 text-[10px] font-mono">••••••••</span>
                    <button onClick={() => removeKey(k.provider)} className="text-zinc-500 hover:text-red-400 transition-colors">
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
        
        <div className="text-[10px] text-zinc-600 font-mono border-t border-zinc-800/60 pt-2">
          Kubernetes Stateless Topology Layer v1.0.0
        </div>
      </div>

      {/* Primary Terminal Hub */}
      <div className="flex-1 flex flex-col relative">
        <header className="h-14 border-b border-zinc-800 flex items-center px-6 bg-zinc-950/80 backdrop-blur-md sticky top-0 z-10">
          <h2 className="text-xs font-medium text-zinc-400 flex items-center gap-2 tracking-wide">
            <Terminal size={14} className="text-zinc-500" />
            Neural Router Interface
          </h2>
        </header>

        {/* Chat History Container */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
              <div className={`w-7 h-7 rounded flex items-center justify-center shrink-0 text-xs ${msg.role === "user" ? "bg-zinc-800 text-zinc-300 border border-zinc-700" : "bg-emerald-950/60 text-emerald-400 border border-emerald-800/50"}`}>
                {msg.role === "user" ? <User size={14} /> : <Cpu size={14} />}
              </div>
              <div className={`max-w-[85%] rounded p-3 text-sm leading-relaxed ${msg.role === "user" ? "bg-zinc-900/60 text-zinc-200 border border-zinc-800" : "bg-zinc-900 text-zinc-300 border border-zinc-800"}`}>
                <pre className="whitespace-pre-wrap font-sans text-xs">
                  {msg.content}
                </pre>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded flex items-center justify-center shrink-0 bg-emerald-950/60 text-emerald-400 border border-emerald-800/50">
                <Cpu size={14} />
              </div>
              <div className="bg-zinc-900 border border-zinc-800 text-zinc-500 rounded p-3 text-xs flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Console Command Input Bar */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-950">
          <form onSubmit={sendMessage} className="max-w-4xl mx-auto relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={keyPool.length === 0 ? "Commanding Core Engine via Local Ollama Node..." : "Commanding Dynamic Cloud Mesh..."}
              disabled={!token || isLoading}
              className="w-full bg-zinc-900 border border-zinc-800 text-zinc-100 font-mono text-xs rounded-lg p-3.5 pr-10 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-all placeholder:text-zinc-600"
            />
            <button 
              type="submit" 
              disabled={!token || isLoading || !input.trim()}
              className="absolute right-2 p-1.5 text-emerald-400 hover:bg-emerald-500/10 rounded disabled:opacity-30 transition-colors"
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}