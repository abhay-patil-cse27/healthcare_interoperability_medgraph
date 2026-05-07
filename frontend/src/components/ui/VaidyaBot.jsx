import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import { vaidyaAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";

// ── SVG icons ─────────────────────────────────────────────────────────────────
const IconClose = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);
const IconSend = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
);
const IconClear = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
  </svg>
);
const IconShield = () => (
  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
);

// ── Vaidya avatar ─────────────────────────────────────────────────────────────
function VaidyaMark({ size = 32, glow = false }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%",
      background: "linear-gradient(135deg, #163300 0%, #2d5a00 100%)",
      display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
      boxShadow: glow
        ? "0 0 0 3px rgba(159,232,112,0.35), 0 4px 20px rgba(22,51,0,0.4)"
        : "0 2px 8px rgba(22,51,0,0.25)",
      transition: "box-shadow 0.3s ease",
    }}>
      <span style={{ fontSize: size * 0.45, lineHeight: 1, userSelect: "none" }}>वै</span>
    </div>
  );
}

// ── Typing dots ───────────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div style={{ display: "flex", gap: 4, padding: "10px 14px", alignItems: "center" }}>
      {[0, 1, 2].map((i) => (
        <span key={i} style={{
          width: 7, height: 7, borderRadius: "50%", background: "#9fe870",
          display: "inline-block",
          animation: `vaidya-bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
    </div>
  );
}

// ── Message bubble ────────────────────────────────────────────────────────────
function Bubble({ msg }) {
  const isBot      = msg.role === "assistant";
  const isBlocked  = msg.guardrail === "BLOCKED";

  return (
    <div style={{
      display: "flex", gap: 8,
      flexDirection: isBot ? "row" : "row-reverse",
      alignItems: "flex-start",
      animation: "vaidya-slide-in 0.25s ease-out both",
    }}>
      {isBot && <div style={{ paddingTop: 2 }}><VaidyaMark size={26} /></div>}
      <div style={{
        maxWidth: "82%",
        padding: isBot ? "10px 14px" : "9px 14px",
        borderRadius: isBot ? "4px 18px 18px 18px" : "18px 4px 18px 18px",
        background: isBlocked
          ? "#fff8e6"
          : isBot
            ? "#ffffff"
            : "linear-gradient(135deg, #163300 0%, #2d5a00 100%)",
        color: isBot ? "#0e0f0c" : "#ffffff",
        fontSize: 13, lineHeight: 1.55,
        border: isBlocked ? "1px solid #ffd300" : isBot ? "1px solid #e8ebe6" : "none",
        boxShadow: isBot ? "0 1px 4px rgba(0,0,0,0.06)" : "0 2px 10px rgba(22,51,0,0.3)",
        wordBreak: "break-word",
      }}>
        {/* Guardrail blocked badge */}
        {isBlocked && (
          <div style={{
            display: "flex", alignItems: "center", gap: 4,
            marginBottom: 6, color: "#92600a",
            fontSize: 10, fontWeight: 600,
          }}>
            <IconShield /> Safety filter applied
          </div>
        )}

        {isBot ? (
          <ReactMarkdown components={{
            p:      ({ children }) => <p style={{ margin: "0 0 6px", fontSize: 13, color: "#454745", lineHeight: 1.55 }}>{children}</p>,
            ul:     ({ children }) => <ul style={{ margin: "4px 0 6px", paddingLeft: 18 }}>{children}</ul>,
            li:     ({ children }) => <li style={{ fontSize: 13, color: "#454745", marginBottom: 2 }}>{children}</li>,
            strong: ({ children }) => <strong style={{ fontWeight: 600, color: "#163300" }}>{children}</strong>,
            code:   ({ children }) => <code style={{ background: "#e8ebe6", borderRadius: 4, padding: "1px 5px", fontSize: 11.5, fontFamily: "monospace", color: "#163300" }}>{children}</code>,
            h3:     ({ children }) => <h3 style={{ fontSize: 13, fontWeight: 700, color: "#163300", margin: "8px 0 4px" }}>{children}</h3>,
          }}>
            {msg.content}
          </ReactMarkdown>
        ) : (
          <span>{msg.content}</span>
        )}
      </div>
    </div>
  );
}

// ── Suggested prompts (role-aware) ────────────────────────────────────────────
const SUGGESTIONS_BY_ROLE = {
  patient:          ["How do I upload documents?", "How does consent work?", "What can my doctor see?"],
  doctor:           ["How do I search a patient by MRN?", "How do I request consent?", "Explain FHIR exchange"],
  nurse:            ["How do I log vitals?", "How do I view my assigned patients?"],
  pharmacist:       ["How do I dispense a prescription?", "What is the prescription queue?"],
  hospital_admin:   ["How do I invite staff?", "How do I create a department?"],
  default:          ["What is MedGraph AI?", "How does consent work?", "What is FHIR exchange?", "What is ABHA?"],
};

// ── Main component — AUTH ONLY ────────────────────────────────────────────────
export default function VaidyaBot() {
  const { user, isAuthenticated } = useAuthStore();

  // ── Gate: only render when logged in ──────────────────────────────────────
  if (!isAuthenticated || !user) return null;

  return <VaidyaBotInner user={user} />;
}

function VaidyaBotInner({ user }) {
  const [open,          setOpen]         = useState(false);
  const [messages,      setMessages]     = useState([]);
  const [input,         setInput]        = useState("");
  const [loading,       setLoading]      = useState(false);
  const [pulse,         setPulse]        = useState(true);
  const [showGreeting,  setShowGreeting] = useState(true);   // floating "hello" bubble
  const scrollRef  = useRef(null);
  const inputRef   = useRef(null);

  const suggestions = SUGGESTIONS_BY_ROLE[user?.role] || SUGGESTIONS_BY_ROLE.default;

  // Stop FAB pulse after 10s
  useEffect(() => {
    const t = setTimeout(() => setPulse(false), 10000);
    return () => clearTimeout(t);
  }, []);

  // Hide greeting bubble when chat opens
  useEffect(() => {
    if (open) setShowGreeting(false);
  }, [open]);

  // Auto-hide greeting after 8s
  useEffect(() => {
    const t = setTimeout(() => setShowGreeting(false), 8000);
    return () => clearTimeout(t);
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loading]);

  // Focus input on open
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 120);
  }, [open]);

  // Greeting message on first open
  useEffect(() => {
    if (open && messages.length === 0) {
      const name = user.name || user.email || "there";
      const role = user.role?.replace(/_/g, " ") || "user";
      setMessages([{
        role: "assistant",
        content: `Namaste! 🙏 I'm **Vaidya** (वैद्य), your MedGraph guide.\n\nYou're logged in as **${name}** (${role}). How can I help you navigate the platform today?`,
      }]);
    }
  }, [open]);

  const buildHistoryPayload = useCallback((msgs) =>
    msgs.map((m) => ({ role: m.role, content: m.content }))
  , []);

  const sendMessage = useCallback(async (text) => {
    const query = (text || input).trim();
    if (!query || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");
    setLoading(true);

    try {
      const { data } = await vaidyaAPI.chat(
        query,
        buildHistoryPayload(messages),
        user?.role || null,
      );

      setMessages((prev) => [...prev, {
        role:      "assistant",
        content:   data.reply,
        guardrail: data.guardrail_action,   // "NONE" | "BLOCKED"
      }]);
    } catch {
      setMessages((prev) => [...prev, {
        role:    "assistant",
        content: "I'm having a moment of silence 🙏. Please try again shortly.",
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [input, messages, loading, user, buildHistoryPayload]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const clearChat = () => {
    setMessages([]);
    setTimeout(() => {
      const name = user.name || user.email || "there";
      const role = user.role?.replace(/_/g, " ") || "user";
      setMessages([{
        role:    "assistant",
        content: `Namaste! 🙏 I'm **Vaidya** (वैद्य), your MedGraph guide.\n\nYou're logged in as **${name}** (${role}). How can I help you navigate the platform today?`,
      }]);
    }, 40);
  };

  return (
    <>
      {/* ── Keyframes ──────────────────────────────────────────────────────── */}
      <style>{`
        @keyframes vaidya-bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.5; }
          40%            { transform: translateY(-6px); opacity: 1; }
        }
        @keyframes vaidya-slide-in {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes vaidya-pop-in {
          0%   { opacity: 0; transform: scale(0.88) translateY(12px); }
          70%  { transform: scale(1.02) translateY(-2px); }
          100% { opacity: 1; transform: scale(1) translateY(0); }
        }
        @keyframes vaidya-pulse-ring {
          0%   { box-shadow: 0 0 0 0   rgba(159,232,112,0.55), 0 4px 20px rgba(22,51,0,0.4); }
          70%  { box-shadow: 0 0 0 10px rgba(159,232,112,0),   0 4px 20px rgba(22,51,0,0.4); }
          100% { box-shadow: 0 0 0 0   rgba(159,232,112,0),   0 4px 20px rgba(22,51,0,0.4); }
        }
        @keyframes vaidya-greeting-in {
          from { opacity: 0; transform: translateX(12px) scale(0.95); }
          to   { opacity: 1; transform: translateX(0)    scale(1); }
        }
        @keyframes vaidya-greeting-out {
          from { opacity: 1; }
          to   { opacity: 0; pointer-events: none; }
        }
      `}</style>

      {/* ── Floating greeting bubble (above FAB, disappears on open/timeout) ── */}
      {showGreeting && !open && (
        <div
          onClick={() => { setOpen(true); setShowGreeting(false); }}
          style={{
            position:   "fixed",
            bottom:     100,
            right:      28,
            zIndex:     9997,
            background: "#ffffff",
            border:     "1px solid #e8ebe6",
            borderRadius: "18px 18px 4px 18px",
            padding:    "10px 14px",
            boxShadow:  "0 8px 30px rgba(0,0,0,0.12), 0 0 0 1px rgba(22,51,0,0.06)",
            cursor:     "pointer",
            maxWidth:   220,
            animation:  "vaidya-greeting-in 0.4s cubic-bezier(0.34,1.56,0.64,1) both",
            display:    "flex",
            flexDirection: "column",
            gap:        4,
          }}
        >
          {/* Small avatar row */}
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
            <VaidyaMark size={20} />
            <span style={{ fontSize: 11, fontWeight: 700, color: "#163300" }}>Vaidya — वैद्य</span>
          </div>
          <p style={{ margin: 0, fontSize: 13, color: "#0e0f0c", lineHeight: 1.4, fontWeight: 500 }}>
            👋 Hello! How can I help you?
          </p>
          <p style={{ margin: 0, fontSize: 11, color: "#868685" }}>
            Ask me anything about MedGraph
          </p>
          {/* dismiss × */}
          <button
            onClick={(e) => { e.stopPropagation(); setShowGreeting(false); }}
            style={{
              position: "absolute", top: 6, right: 8,
              background: "none", border: "none", cursor: "pointer",
              color: "#868685", fontSize: 14, lineHeight: 1, padding: 2,
            }}
          >×</button>
        </div>
      )}

      {/* ── FAB ────────────────────────────────────────────────────────────── */}
      <button
        id="vaidya-fab"
        onClick={() => { setOpen((v) => !v); setPulse(false); setShowGreeting(false); }}
        aria-label="Open Vaidya AI Guide"
        style={{
          position:     "fixed",
          bottom:       28,
          right:        28,
          zIndex:       9999,
          width:        60,
          height:       60,
          borderRadius: "50%",
          background:   "linear-gradient(135deg, #163300 0%, #2d5a00 100%)",
          border:       "2.5px solid rgba(159,232,112,0.5)",
          cursor:       "pointer",
          display:      "flex",
          alignItems:   "center",
          justifyContent: "center",
          transition:   "transform 0.2s ease, box-shadow 0.2s ease",
          animation:    pulse ? "vaidya-pulse-ring 2s ease-in-out infinite" : "none",
          boxShadow:    "0 4px 20px rgba(22,51,0,0.4)",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.1)")}
        onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
      >
        {open
          ? <span style={{ color: "#9fe870" }}><IconClose /></span>
          : <span style={{ fontSize: 26, lineHeight: 1, color: "#9fe870" }}>वै</span>
        }
      </button>

      {/* ── Chat panel ─────────────────────────────────────────────────────── */}
      {open && (
        <div style={{
          position:   "fixed",
          bottom:     100,
          right:      28,
          zIndex:     9998,
          width:      384,
          maxWidth:   "calc(100vw - 40px)",
          height:     572,
          maxHeight:  "calc(100vh - 130px)",
          borderRadius: 24,
          background: "#f7f9f6",
          boxShadow:  "0 24px 64px rgba(0,0,0,0.18), 0 0 0 1px rgba(22,51,0,0.10)",
          display:    "flex",
          flexDirection: "column",
          overflow:   "hidden",
          animation:  "vaidya-pop-in 0.32s cubic-bezier(0.34,1.56,0.64,1) both",
        }}>

          {/* Header */}
          <div style={{
            background: "linear-gradient(135deg, #163300 0%, #2d5a00 100%)",
            padding:    "14px 16px",
            display:    "flex",
            alignItems: "center",
            gap:        10,
            flexShrink: 0,
          }}>
            <VaidyaMark size={34} glow />
            <div style={{ flex: 1 }}>
              <p style={{ color: "#9fe870", fontWeight: 700, fontSize: 15, lineHeight: 1.2, margin: 0 }}>
                Vaidya — वैद्य
              </p>
              <p style={{ color: "rgba(159,232,112,0.6)", fontSize: 11, margin: 0 }}>
                MedGraph AI · Platform Guide
              </p>
            </div>

            {/* Guardrail badge */}
            <div style={{
              display: "flex", alignItems: "center", gap: 4,
              background: "rgba(159,232,112,0.15)",
              border:     "1px solid rgba(159,232,112,0.25)",
              borderRadius: 20,
              padding:    "3px 8px",
              marginRight: 4,
            }}>
              <IconShield />
              <span style={{ fontSize: 10, color: "rgba(159,232,112,0.8)", fontWeight: 600 }}>
                Guardrails ON
              </span>
            </div>

            <div style={{ display: "flex", gap: 4 }}>
              <button onClick={clearChat} title="Clear conversation"
                style={{ background: "rgba(255,255,255,0.1)", border: "none", borderRadius: 8, padding: "5px 7px", cursor: "pointer", color: "rgba(159,232,112,0.7)", display: "flex", alignItems: "center", transition: "background 0.15s" }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.18)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.1)")}
              ><IconClear /></button>
              <button onClick={() => setOpen(false)} title="Close"
                style={{ background: "rgba(255,255,255,0.1)", border: "none", borderRadius: 8, padding: "5px 7px", cursor: "pointer", color: "rgba(159,232,112,0.7)", display: "flex", alignItems: "center", transition: "background 0.15s" }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.18)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.1)")}
              ><IconClose /></button>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} style={{
            flex: 1, overflowY: "auto", padding: "14px 14px 8px",
            display: "flex", flexDirection: "column", gap: 12,
            scrollbarWidth: "thin", scrollbarColor: "#e8ebe6 transparent",
          }}>
            {messages.map((msg, i) => <Bubble key={i} msg={msg} />)}
            {loading && (
              <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                <VaidyaMark size={26} />
                <div style={{ background: "#ffffff", border: "1px solid #e8ebe6", borderRadius: "4px 18px 18px 18px", boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
                  <TypingDots />
                </div>
              </div>
            )}
          </div>

          {/* Suggestion chips (only on first message) */}
          {messages.length <= 1 && !loading && (
            <div style={{ padding: "0 12px 8px", display: "flex", flexWrap: "wrap", gap: 6, flexShrink: 0 }}>
              {suggestions.map((s) => (
                <button key={s} onClick={() => sendMessage(s)}
                  style={{ padding: "5px 10px", borderRadius: 20, border: "1px solid #d4e8c8", background: "#edf7e6", color: "#163300", fontSize: 11.5, fontWeight: 500, cursor: "pointer", transition: "all 0.15s", lineHeight: 1.4 }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = "#9fe870"; e.currentTarget.style.borderColor = "#9fe870"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = "#edf7e6"; e.currentTarget.style.borderColor = "#d4e8c8"; }}
                >{s}</button>
              ))}
            </div>
          )}

          {/* Input */}
          <div style={{
            borderTop: "1px solid #e8ebe6", padding: "10px 12px",
            background: "#ffffff", flexShrink: 0,
            display: "flex", gap: 8, alignItems: "flex-end",
          }}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask Vaidya anything about MedGraph..."
              rows={1}
              disabled={loading}
              style={{
                flex: 1, resize: "none",
                border: "1.5px solid #e8ebe6", borderRadius: 12,
                padding: "9px 12px", fontSize: 13,
                fontFamily: "inherit", color: "#0e0f0c",
                background: "#f7f9f6", outline: "none",
                transition: "border-color 0.15s",
                maxHeight: 90, overflowY: "auto", lineHeight: 1.45,
              }}
              onFocus={(e) => (e.target.style.borderColor = "#163300")}
              onBlur={(e)  => (e.target.style.borderColor = "#e8ebe6")}
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              style={{
                width: 38, height: 38, borderRadius: "50%",
                background: input.trim() && !loading
                  ? "linear-gradient(135deg, #9fe870 0%, #7dd956 100%)"
                  : "#e8ebe6",
                border: "none",
                cursor: input.trim() && !loading ? "pointer" : "not-allowed",
                display: "flex", alignItems: "center", justifyContent: "center",
                color: input.trim() && !loading ? "#163300" : "#868685",
                transition: "all 0.2s", flexShrink: 0,
                boxShadow: input.trim() && !loading ? "0 2px 10px rgba(159,232,112,0.4)" : "none",
              }}
            ><IconSend /></button>
          </div>

          {/* Disclaimer */}
          <p style={{
            textAlign: "center", fontSize: 10, color: "#868685",
            padding: "4px 12px 8px", background: "#ffffff",
            margin: 0, flexShrink: 0,
          }}>
            Vaidya cannot access health records · Not medical advice · Guardrails active
          </p>
        </div>
      )}
    </>
  );
}
