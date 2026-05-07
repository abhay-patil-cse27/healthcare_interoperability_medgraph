import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, BookOpen, Clock, Plus, Trash2, MessageSquare, ChevronRight, Shield } from "lucide-react";
import ReactMarkdown from "react-markdown";
import toast from "react-hot-toast";
import { chatAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";

function MarkdownContent({ content }) {
  return (
    <ReactMarkdown
      components={{
        h3: ({ children }) => <h3 className="text-sm font-semibold text-slate-900 mt-3 mb-1 first:mt-0">{children}</h3>,
        h4: ({ children }) => <h4 className="text-xs font-semibold text-slate-700 mt-2 mb-1">{children}</h4>,
        p: ({ children }) => <p className="text-sm text-slate-800 leading-relaxed mb-2 last:mb-0">{children}</p>,
        ul: ({ children }) => <ul className="space-y-1 mb-2 pl-1">{children}</ul>,
        li: ({ children }) => (
          <li className="text-sm text-slate-800 flex gap-2 leading-relaxed">
            <span className="text-blue-500 mt-1 flex-shrink-0">•</span>
            <span>{children}</span>
          </li>
        ),
        strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
        code: ({ children }) => <code className="px-1 py-0.5 bg-slate-100 rounded text-xs font-mono text-slate-700">{children}</code>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

function Message({ msg }) {
  const isBot = msg.role === "assistant";
  const isBlocked = msg.metadata?.guardrail_action === "BLOCKED";

  return (
    <div className={`flex gap-3 ${isBot ? "" : "flex-row-reverse"} animate-slide-up`}>
      <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
        isBot ? (isBlocked ? "bg-amber-500" : "bg-blue-600") : "bg-slate-200"
      }`}>
        {isBot ? <Bot className="w-4 h-4 text-white" /> : <User className="w-4 h-4 text-slate-600" />}
      </div>
      <div className={`max-w-[78%] ${isBot ? "" : "items-end flex flex-col"}`}>
        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
          isBot
            ? isBlocked
              ? "bg-amber-50 border border-amber-200 text-amber-900 rounded-tl-sm"
              : "bg-white border border-slate-200 text-slate-800 rounded-tl-sm"
            : "bg-blue-600 text-white rounded-tr-sm"
        }`}>
          {isBot && isBlocked && (
            <div className="flex items-center gap-2 mb-2 text-xs font-bold text-amber-700">
              <Shield className="w-3.5 h-3.5" />
              Safety Policy Applied
            </div>
          )}
          {isBot ? <MarkdownContent content={msg.content} /> : msg.content}
        </div>
        {isBot && msg.metadata?.citations?.length > 0 && (
          <div className="mt-2 space-y-1 w-full">
            <p className="text-xs text-slate-400 flex items-center gap-1">
              <BookOpen className="w-3 h-3" /> Sources
            </p>
            {msg.metadata.citations.slice(0, 3).map((c, i) => (
              <div key={i} className="px-3 py-1.5 bg-slate-50 border border-slate-100 rounded-lg">
                <p className="text-xs text-slate-600 line-clamp-2">{c.excerpt}</p>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  {c.source_type} · score {c.relevance_score?.toFixed(3)}
                </p>
              </div>
            ))}
          </div>
        )}
        <p className="text-[10px] text-slate-400 mt-1">
          {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }) : ""}
        </p>
      </div>
    </div>
  );
}

function SessionItem({ session, isActive, onClick, onDelete }) {
  return (
    <div
      className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all ${
        isActive ? "bg-blue-50 border border-blue-200" : "hover:bg-slate-50"
      }`}
      onClick={onClick}
    >
      <MessageSquare className={`w-4 h-4 shrink-0 ${isActive ? "text-blue-600" : "text-slate-400"}`} />
      <div className="flex-1 min-w-0">
        <p className={`text-xs font-medium truncate ${isActive ? "text-blue-700" : "text-slate-700"}`}>
          {session.message_count > 0 ? `${session.message_count} messages` : "New conversation"}
        </p>
        <p className="text-[10px] text-slate-400 truncate">
          {new Date(session.updated_at || session.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
        </p>
      </div>
      <button
        onClick={(e) => { e.stopPropagation(); onDelete(session.session_id); }}
        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-50 hover:text-red-500 text-slate-400 transition-all"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

export default function PatientChat() {
  const { user } = useAuthStore();
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionsLoading, setSessionsLoading] = useState(true);

  // Load sessions on mount
  useEffect(() => { loadSessions(); }, []);

  // Load messages when active session changes
  useEffect(() => {
    if (activeSessionId) loadMessages(activeSessionId);
    else setMessages([]);
  }, [activeSessionId]);

  // Auto-scroll on new messages
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const loadSessions = async () => {
    setSessionsLoading(true);
    try {
      const { data } = await chatAPI.listSessions();
      setSessions(data.sessions || []);
      // Auto-select the most recent session
      if (data.sessions?.length > 0 && !activeSessionId) {
        setActiveSessionId(data.sessions[0].session_id);
      }
    } catch { /* silent */ }
    finally { setSessionsLoading(false); }
  };

  const loadMessages = async (sessionId) => {
    try {
      const { data } = await chatAPI.getSession(sessionId);
      setMessages(data.messages || []);
    } catch {
      setMessages([]);
    }
  };

  const handleNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    inputRef.current?.focus();
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await chatAPI.deleteSession(sessionId);
      toast.success("Conversation deleted");
      setSessions(prev => prev.filter(s => s.session_id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Delete failed");
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    const query = input.trim();
    if (!query || loading) return;

    // Optimistic UI: show user message immediately
    const userMsg = { role: "user", content: query, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const { data } = await chatAPI.query({
        patient_id:     user.user_id,
        requester_id:   user.user_id,
        requester_role: user.role,
        query,
        session_id: activeSessionId || undefined,
      });

      // Set session if this was a new conversation
      if (!activeSessionId && data.session_id) {
        setActiveSessionId(data.session_id);
        loadSessions(); // Refresh sidebar
      }

      // Add assistant response
      const assistantMsg = {
        role: "assistant",
        content: data.response,
        timestamp: new Date().toISOString(),
        metadata: {
          citations: data.citations,
          guardrail_action: data.guardrail_action,
        },
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      const detail = err.response?.data?.detail;
      let errMsg = "Query failed";
      if (typeof detail === "string") errMsg = detail;
      else if (Array.isArray(detail)) errMsg = detail.map(d => d.msg || JSON.stringify(d)).join("; ");
      else if (detail?.reason) errMsg = detail.reason;
      else if (detail) errMsg = JSON.stringify(detail);
      toast.error(errMsg);
      // Remove optimistic message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-64px)] animate-fade-in">
      {/* Session Sidebar */}
      <div className="w-64 border-r border-slate-200 flex flex-col bg-white shrink-0">
        <div className="p-3 border-b border-slate-100">
          <button onClick={handleNewChat} className="btn-primary w-full justify-center text-xs py-2">
            <Plus className="w-4 h-4" /> New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessionsLoading ? (
            <div className="flex justify-center py-8"><Spinner size="sm" /></div>
          ) : sessions.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-8">No conversations yet</p>
          ) : (
            sessions.map(s => (
              <SessionItem
                key={s.session_id}
                session={s}
                isActive={s.session_id === activeSessionId}
                onClick={() => setActiveSessionId(s.session_id)}
                onDelete={handleDeleteSession}
              />
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mb-4">
                <Bot className="w-8 h-8 text-blue-500" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-1">Ask about your health records</h3>
              <p className="text-sm text-slate-500 max-w-sm">
                I can help you understand your lab results, medications, conditions, and medical history.
              </p>
              <div className="flex flex-wrap gap-2 mt-6 max-w-md justify-center">
                {["What are my current medications?", "Summarize my last lab report", "Do I have any allergies?"].map(q => (
                  <button
                    key={q}
                    onClick={() => { setInput(q); inputRef.current?.focus(); }}
                    className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 hover:bg-slate-100 hover:border-slate-300 transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => <Message key={i} msg={msg} />)
          )}
          {loading && (
            <div className="flex gap-3 animate-slide-up">
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="px-4 py-3 bg-white border border-slate-200 rounded-2xl rounded-tl-sm">
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <Spinner size="sm" /> Thinking...
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-slate-200 px-6 py-4 bg-white">
          <form onSubmit={handleSend} className="flex items-center gap-3">
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask about your health records..."
              className="input flex-1"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="btn-primary px-4 py-2.5"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <p className="text-[10px] text-slate-400 mt-2 text-center">
            AI-generated responses are not medical advice. Always consult your doctor.
          </p>
        </div>
      </div>
    </div>
  );
}
