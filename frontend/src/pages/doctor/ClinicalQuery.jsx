import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, BookOpen, Clock, Shield, Plus, Trash2, MessageSquare, AlertCircle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import toast from "react-hot-toast";
import { chatAPI, consentAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";
import Spinner from "../../components/ui/Spinner";
import PatientSearchBar from "../../components/ui/PatientSearchBar";

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
        isBot ? (isBlocked ? "bg-amber-500" : "bg-blue-600") : "bg-slate-700"
      }`}>
        {isBot ? <Bot className="w-4 h-4 text-white" /> : <User className="w-4 h-4 text-white" />}
      </div>
      <div className={`max-w-[78%] ${isBot ? "" : "items-end flex flex-col"}`}>
        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
          isBot
            ? isBlocked
              ? "bg-amber-50 border border-amber-200 text-amber-900 rounded-tl-sm"
              : "bg-white border border-slate-200 text-slate-800 rounded-tl-sm"
            : "bg-slate-800 text-white rounded-tr-sm"
        }`}>
          {isBot && isBlocked && (
            <div className="flex items-center gap-2 mb-2 text-xs font-bold text-amber-700">
              <AlertCircle className="w-3.5 h-3.5" />
              Guardrail Intervention — Response filtered for HIPAA compliance
            </div>
          )}
          {isBot ? <MarkdownContent content={msg.content} /> : msg.content}
        </div>
        {isBot && msg.metadata?.citations?.length > 0 && (
          <div className="mt-2 space-y-1 w-full">
            <p className="text-xs text-slate-400 flex items-center gap-1"><BookOpen className="w-3 h-3" /> Evidence Sources</p>
            {msg.metadata.citations.slice(0, 4).map((c, i) => (
              <div key={i} className="px-3 py-2 bg-slate-50 border border-slate-100 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <span className="badge badge-blue">{c.source_type}</span>
                  <span className="text-[10px] text-slate-400">score {c.relevance_score?.toFixed(3)}</span>
                </div>
                <p className="text-xs text-slate-600 line-clamp-2">{c.excerpt}</p>
              </div>
            ))}
          </div>
        )}
        {isBot && msg.metadata && (
          <p className="text-[10px] text-slate-400 mt-1 flex items-center gap-2">
            <Clock className="w-3 h-3" />
            Retrieval {msg.metadata.retrieval_time_ms || 0}ms · LLM {msg.metadata.llm_time_ms || 0}ms
            {msg.metadata.cache_hit && <span className="badge badge-green text-[9px]">cached</span>}
            {isBlocked && <span className="badge badge-amber text-[9px]">guardrail</span>}
          </p>
        )}
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
          Patient {session.patient_id?.slice(0, 8)}…
        </p>
        <p className="text-[10px] text-slate-400">
          {session.message_count} msgs · {new Date(session.updated_at || session.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
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

export default function ClinicalQuery() {
  const { user } = useAuthStore();
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [activePatientId, setActivePatientId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [showPatientSelect, setShowPatientSelect] = useState(false);

  useEffect(() => { loadSessions(); }, []);

  useEffect(() => {
    if (activeSessionId) loadMessages(activeSessionId);
    else setMessages([]);
  }, [activeSessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const loadSessions = async () => {
    setSessionsLoading(true);
    try {
      const { data } = await chatAPI.listSessions();
      setSessions(data.sessions || []);
      if (data.sessions?.length > 0 && !activeSessionId) {
        setActiveSessionId(data.sessions[0].session_id);
        setActivePatientId(data.sessions[0].patient_id);
      }
    } catch { /* silent */ }
    finally { setSessionsLoading(false); }
  };

  const loadMessages = async (sessionId) => {
    try {
      const { data } = await chatAPI.getSession(sessionId);
      setMessages(data.messages || []);
      setActivePatientId(data.session?.patient_id);
    } catch { setMessages([]); }
  };

  const handleNewChat = () => {
    setShowPatientSelect(true);
  };

  const handlePatientSelected = (patient) => {
    setActivePatientId(patient.user_id);
    setActiveSessionId(null);
    setMessages([]);
    setShowPatientSelect(false);
    inputRef.current?.focus();
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await chatAPI.deleteSession(sessionId);
      toast.success("Conversation deleted");
      setSessions(prev => prev.filter(s => s.session_id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setActivePatientId(null);
        setMessages([]);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Delete failed");
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    const query = input.trim();
    if (!query || loading || !activePatientId) return;

    const userMsg = { role: "user", content: query, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const { data } = await chatAPI.query({
        patient_id: activePatientId,
        query,
        session_id: activeSessionId || undefined,
      });

      if (!activeSessionId && data.session_id) {
        setActiveSessionId(data.session_id);
        loadSessions();
      }

      const assistantMsg = {
        role: "assistant",
        content: data.response,
        timestamp: new Date().toISOString(),
        metadata: {
          citations: data.citations,
          retrieval_time_ms: data.retrieval_time_ms,
          llm_time_ms: data.llm_time_ms,
          cache_hit: data.cache_hit,
          guardrail_action: data.guardrail_action,
        },
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail?.error === "CONSENT_DENIED") {
        toast.error("No active consent for this patient. Request consent first.");
      } else {
        toast.error(typeof detail === "string" ? detail : "Query failed");
      }
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
            <Plus className="w-4 h-4" /> New Query
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
                onClick={() => { setActiveSessionId(s.session_id); setActivePatientId(s.patient_id); }}
                onDelete={handleDeleteSession}
              />
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Patient context bar */}
        {activePatientId && (
          <div className="px-6 py-2 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
            <Shield className="w-3.5 h-3.5 text-emerald-500" />
            <span className="text-xs text-slate-600">
              Querying patient <span className="font-mono font-semibold">{activePatientId.slice(0, 12)}…</span>
            </span>
            <span className="badge badge-green text-[9px]">Consent Active</span>
          </div>
        )}

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {!activePatientId && !showPatientSelect ? (
            <EmptyState
              icon={Bot}
              title="Select a patient to query"
              description="Click 'New Query' to start a clinical conversation"
            />
          ) : showPatientSelect ? (
            <div className="max-w-md mx-auto mt-12">
              <h3 className="text-lg font-bold text-slate-900 mb-4">Select Patient</h3>
              <PatientSearchBar onSelect={handlePatientSelected} />
              <p className="text-xs text-slate-400 mt-3">
                You must have active consent to query a patient's records.
              </p>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mb-4">
                <Bot className="w-8 h-8 text-blue-500" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-1">Clinical Query Engine</h3>
              <p className="text-sm text-slate-500 max-w-sm">
                Ask clinical questions about this patient's records. Responses are grounded in their health data.
              </p>
              <div className="flex flex-wrap gap-2 mt-6 max-w-lg justify-center">
                {[
                  "What medications is this patient on?",
                  "Summarize recent lab results",
                  "Any drug interaction risks?",
                  "History of chronic conditions",
                ].map(q => (
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
                  <Spinner size="sm" /> Retrieving & analyzing...
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
              placeholder={activePatientId ? "Ask a clinical question..." : "Select a patient first"}
              className="input flex-1"
              disabled={loading || !activePatientId}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading || !activePatientId}
              className="btn-primary px-4 py-2.5"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <p className="text-[10px] text-slate-400 mt-2 text-center">
            Consent-gated · RAG-powered · All queries audited
          </p>
        </div>
      </div>
    </div>
  );
}

function EmptyState({ icon: Icon, title, description }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center py-16">
      <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
        <Icon className="w-7 h-7 text-slate-400" />
      </div>
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {description && <p className="text-xs text-slate-400 mt-1 max-w-xs">{description}</p>}
    </div>
  );
}
