import { useState, useEffect } from "react";
import { FileText, CheckCircle2, Clock, AlertTriangle, Shield, Eye, Edit3, RefreshCw } from "lucide-react";
import ReactMarkdown from "react-markdown";
import toast from "react-hot-toast";
import { screeningAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";

function ScreeningCard({ item, onView }) {
  const expiresAt = item.consent_expires ? new Date(item.consent_expires) : null;
  const hoursLeft = expiresAt ? Math.max(0, Math.round((expiresAt - Date.now()) / 3600000)) : null;

  return (
    <div className="card p-5 hover:shadow-card-hover transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
            item.critical_count > 0 ? "bg-red-50" : item.abnormality_count > 0 ? "bg-amber-50" : "bg-green-50"
          }`}>
            {item.critical_count > 0 ? (
              <AlertTriangle className="w-5 h-5 text-red-500" />
            ) : (
              <FileText className="w-5 h-5 text-brand-500" />
            )}
          </div>
          <div>
            <p className="text-sm font-medium text-surface-800">
              Patient {item.patient_id.slice(0, 8)}…
            </p>
            <p className="text-xs text-surface-400">
              {item.abnormality_count} abnormalities · {item.critical_count} critical
            </p>
          </div>
        </div>
        <button onClick={() => onView(item.screening_id)} className="btn-primary text-xs py-1.5 px-3">
          <Eye className="w-3.5 h-3.5 mr-1" /> Review
        </button>
      </div>

      <div className="flex items-center gap-3 mt-3">
        {item.was_edited && (
          <span className="badge badge-blue flex items-center gap-1">
            <Edit3 className="w-3 h-3" /> HITL Edited
          </span>
        )}
        {hoursLeft !== null && (
          <span className={`badge ${hoursLeft < 4 ? "badge-red" : "badge-yellow"} flex items-center gap-1`}>
            <Clock className="w-3 h-3" /> {hoursLeft}h remaining
          </span>
        )}
        <span className="text-[10px] text-surface-400">
          {new Date(item.summary_date).toLocaleDateString("en-IN")}
        </span>
      </div>
    </div>
  );
}

function ScreeningDetail({ screeningId, onBack }) {
  const [screening, setScreening] = useState(null);
  const [loading, setLoading] = useState(true);
  const [marking, setMarking] = useState(false);

  useEffect(() => { loadScreening(); }, [screeningId]);

  const loadScreening = async () => {
    setLoading(true);
    try {
      const { data } = await screeningAPI.doctorView(screeningId);
      setScreening(data);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Access denied or expired");
      onBack();
    } finally { setLoading(false); }
  };

  const markReviewed = async () => {
    setMarking(true);
    try {
      await screeningAPI.doctorReviewed(screeningId);
      toast.success("Marked as reviewed");
      onBack();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed");
    } finally { setMarking(false); }
  };

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;
  if (!screening) return null;

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Back button */}
      <button onClick={onBack} className="btn-ghost text-xs">← Back to inbox</button>

      {/* Transparency Label */}
      <div className="card p-3 bg-amber-50 border-amber-200">
        <p className="text-xs text-amber-800 flex items-center gap-1">
          <Shield className="w-3.5 h-3.5" />
          {screening.ai_generated_label}
        </p>
        {screening.was_edited_by_hitl && (
          <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
            <Edit3 className="w-3 h-3" /> This summary was edited by the HITL operator before reaching you.
          </p>
        )}
      </div>

      {/* Consent Timer */}
      {screening.consent_expires_at && (
        <div className="flex items-center gap-2 text-xs text-surface-500">
          <Clock className="w-3.5 h-3.5" />
          Access expires: {new Date(screening.consent_expires_at).toLocaleString("en-IN")}
        </div>
      )}

      {/* Abnormalities */}
      {screening.flagged_abnormalities?.length > 0 && (
        <div className="card p-4 border-l-4 border-l-red-400">
          <p className="text-xs font-semibold text-red-700 mb-2">
            Flagged Abnormalities ({screening.abnormality_count})
            {screening.critical_count > 0 && (
              <span className="badge badge-red ml-2">{screening.critical_count} CRITICAL</span>
            )}
          </p>
          <div className="space-y-2">
            {screening.flagged_abnormalities.map((f, i) => (
              <div key={i} className="flex items-center justify-between text-xs bg-surface-50 rounded-lg px-3 py-2">
                <span className="font-medium text-surface-800">{f.parameter}</span>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-surface-600">{f.observed_value} {f.unit}</span>
                  <span className="text-surface-400">Ref: {f.reference_range}</span>
                  <span className={`badge ${
                    f.status === "CRITICAL" ? "badge-red" : f.status === "HIGH" ? "badge-yellow" : "badge-blue"
                  }`}>{f.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Clinical Summary */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-surface-800 mb-3">Clinical Summary</h3>
        <div className="prose prose-sm text-sm text-surface-700 max-h-96 overflow-y-auto">
          <ReactMarkdown>{screening.clinical_summary}</ReactMarkdown>
        </div>
      </div>

      {/* Mark Reviewed */}
      <div className="flex justify-end">
        <button onClick={markReviewed} disabled={marking} className="btn-primary flex items-center gap-2">
          {marking ? <Spinner size="sm" /> : <CheckCircle2 className="w-4 h-4" />}
          Mark as Reviewed
        </button>
      </div>
    </div>
  );
}

export default function ScreeningInbox() {
  const { user } = useAuthStore();
  const [inbox, setInbox] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => { loadInbox(); }, []);

  const loadInbox = async () => {
    setLoading(true);
    try {
      const { data } = await screeningAPI.doctorInbox();
      setInbox(data);
    } catch (err) {
      toast.error("Failed to load screening inbox");
    } finally { setLoading(false); }
  };

  if (selectedId) {
    return <ScreeningDetail screeningId={selectedId} onBack={() => { setSelectedId(null); loadInbox(); }} />;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="page-title">AI Screening Inbox</h1>
          <p className="text-surface-500 text-sm mt-1">
            HITL-verified patient screenings awaiting your review
          </p>
        </div>
        <button onClick={loadInbox} className="btn-ghost flex items-center gap-1">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-surface-800">{inbox.length}</p>
          <p className="text-xs text-surface-400">Pending Review</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-red-600">{inbox.filter(i => i.critical_count > 0).length}</p>
          <p className="text-xs text-surface-400">Critical</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-brand-600">{inbox.filter(i => i.was_edited).length}</p>
          <p className="text-xs text-surface-400">HITL Edited</p>
        </div>
      </div>

      {/* Inbox List */}
      {loading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : inbox.length === 0 ? (
        <EmptyState
          icon={CheckCircle2}
          title="Inbox empty"
          description="No screenings pending your review right now"
        />
      ) : (
        <div className="space-y-3">
          {inbox.map((item) => (
            <ScreeningCard key={item.screening_id} item={item} onView={setSelectedId} />
          ))}
        </div>
      )}
    </div>
  );
}
