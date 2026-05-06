import { useState, useEffect } from "react";
import { Shield, CheckCircle2, XCircle, AlertTriangle, Edit3, Send, Clock, RefreshCw, Eye, FileText, ArrowRight } from "lucide-react";
import toast from "react-hot-toast";
import ReactMarkdown from "react-markdown";
import { screeningAPI, documentsAPI, patientSearchAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";

const STAGE_BADGE = {
  ai_generated:          "badge-yellow",
  hitl_in_review:        "badge-blue",
  hitl_edited:           "badge-green",
  hitl_accepted:         "badge-green",
  hitl_rejected:         "badge-red",
  hitl_escalated:        "badge-red",
  doctor_consent_active: "badge-blue",
  doctor_reviewed:       "badge-green",
};

function QueueCard({ item, onSelect }) {
  return (
    <div
      className="card p-4 hover:shadow-card-hover transition-shadow cursor-pointer"
      onClick={() => onSelect(item.screening_id)}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
            item.critical_count > 0 ? "bg-red-50" : item.abnormality_count > 0 ? "bg-amber-50" : "bg-green-50"
          }`}>
            {item.critical_count > 0 ? (
              <AlertTriangle className="w-5 h-5 text-red-500" />
            ) : item.abnormality_count > 0 ? (
              <AlertTriangle className="w-5 h-5 text-amber-500" />
            ) : (
              <CheckCircle2 className="w-5 h-5 text-green-500" />
            )}
          </div>
          <div>
            <p className="text-sm font-medium text-surface-800">
              Patient {item.patient_id.slice(0, 8)}…
            </p>
            <p className="text-xs text-surface-400">
              {item.abnormality_count} flags · {item.critical_count} critical
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`badge ${STAGE_BADGE[item.stage] || "badge-gray"}`}>{item.stage?.replace(/_/g, " ")}</span>
          <ArrowRight className="w-4 h-4 text-surface-300" />
        </div>
      </div>
      <p className="text-[10px] text-surface-400 mt-2">
        {new Date(item.summary_date).toLocaleString("en-IN")}
      </p>
    </div>
  );
}

function ReviewPanel({ screeningId, onDone }) {
  const [screening, setScreening] = useState(null);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState(null); // "edit" | "accept" | "reject" | "escalate"
  const [editedSummary, setEditedSummary] = useState("");
  const [editReason, setEditReason] = useState("");
  const [targetDoctor, setTargetDoctor] = useState("");
  const [consentHours, setConsentHours] = useState(24);
  const [rejectionReason, setRejectionReason] = useState("");
  const [escalationReason, setEscalationReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadScreening();
  }, [screeningId]);

  const loadScreening = async () => {
    setLoading(true);
    try {
      const { data } = await screeningAPI.getHitlDetail(screeningId);
      setScreening(data);
      setEditedSummary(data.ai_summary || "");
    } catch (err) {
      toast.error("Failed to load screening");
    } finally { setLoading(false); }
  };

  const handleEditForward = async () => {
    if (!editedSummary.trim() || !editReason.trim() || !targetDoctor.trim()) {
      toast.error("Fill all required fields");
      return;
    }
    setSubmitting(true);
    try {
      await screeningAPI.editForward({
        screening_id: screeningId,
        edited_summary: editedSummary,
        edit_reason: editReason,
        target_doctor_id: targetDoctor,
        consent_duration_hours: consentHours,
      });
      toast.success("Edited & forwarded to doctor");
      onDone();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed");
    } finally { setSubmitting(false); }
  };

  const handleAcceptForward = async () => {
    if (!targetDoctor.trim()) {
      toast.error("Select a target doctor");
      return;
    }
    setSubmitting(true);
    try {
      await screeningAPI.acceptForward({
        screening_id: screeningId,
        target_doctor_id: targetDoctor,
        consent_duration_hours: consentHours,
      });
      toast.success("Accepted & forwarded to doctor");
      onDone();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed");
    } finally { setSubmitting(false); }
  };

  const handleReject = async () => {
    if (!rejectionReason.trim()) {
      toast.error("Provide rejection reason");
      return;
    }
    setSubmitting(true);
    try {
      await screeningAPI.reject({
        screening_id: screeningId,
        rejection_reason: rejectionReason,
        discrepancies: [],
      });
      toast.success("Screening rejected");
      onDone();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed");
    } finally { setSubmitting(false); }
  };

  const handleEscalate = async () => {
    if (!escalationReason.trim()) {
      toast.error("Provide escalation reason");
      return;
    }
    setSubmitting(true);
    try {
      await screeningAPI.escalate({
        screening_id: screeningId,
        escalation_reason: escalationReason,
        escalation_type: "identity_mismatch",
      });
      toast.success("Escalated to admin");
      onDone();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed");
    } finally { setSubmitting(false); }
  };

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;
  if (!screening) return null;

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-surface-800">Review Screening</h3>
        <span className={`badge ${STAGE_BADGE[screening.stage] || "badge-gray"}`}>{screening.stage?.replace(/_/g, " ")}</span>
      </div>

      {/* Abnormalities */}
      {screening.flagged_abnormalities?.length > 0 && (
        <div className="card p-4 border-l-4 border-l-amber-400">
          <p className="text-xs font-semibold text-amber-700 mb-2">Flagged Abnormalities ({screening.abnormality_count})</p>
          <div className="space-y-1">
            {screening.flagged_abnormalities.map((f, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <span className="text-surface-700 font-medium">{f.parameter}</span>
                <span className="flex items-center gap-2">
                  <span className="font-mono">{f.observed_value} {f.unit}</span>
                  <span className={`badge ${f.status === "CRITICAL" ? "badge-red" : f.status === "HIGH" ? "badge-yellow" : "badge-blue"}`}>
                    {f.status}
                  </span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Summary */}
      <div className="card p-4 max-h-64 overflow-y-auto">
        <p className="text-xs font-semibold text-surface-500 mb-2 flex items-center gap-1">
          <Shield className="w-3 h-3" /> AI-Generated Summary (verify against source)
        </p>
        <div className="prose prose-sm text-xs text-surface-700">
          <ReactMarkdown>{screening.ai_summary}</ReactMarkdown>
        </div>
      </div>

      {/* Action Buttons */}
      {!action && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <button onClick={() => setAction("accept")} className="btn-primary text-xs py-2 flex items-center justify-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Accept
          </button>
          <button onClick={() => setAction("edit")} className="btn-ghost text-xs py-2 flex items-center justify-center gap-1 border border-brand-200">
            <Edit3 className="w-3.5 h-3.5" /> Edit
          </button>
          <button onClick={() => setAction("reject")} className="btn-ghost text-xs py-2 flex items-center justify-center gap-1 border border-red-200 text-red-600">
            <XCircle className="w-3.5 h-3.5" /> Reject
          </button>
          <button onClick={() => setAction("escalate")} className="btn-ghost text-xs py-2 flex items-center justify-center gap-1 border border-amber-200 text-amber-600">
            <AlertTriangle className="w-3.5 h-3.5" /> Escalate
          </button>
        </div>
      )}

      {/* Accept Form */}
      {action === "accept" && (
        <div className="card p-4 space-y-3 border-l-4 border-l-green-400">
          <p className="text-xs font-semibold text-green-700">Accept & Forward to Doctor</p>
          <input value={targetDoctor} onChange={e => setTargetDoctor(e.target.value)}
            placeholder="Target Doctor ID" className="input text-xs w-full" />
          <div className="flex items-center gap-2">
            <label className="text-xs text-surface-500">Consent duration:</label>
            <select value={consentHours} onChange={e => setConsentHours(+e.target.value)} className="input text-xs w-24">
              <option value={6}>6 hrs</option>
              <option value={12}>12 hrs</option>
              <option value={24}>24 hrs</option>
              <option value={48}>48 hrs</option>
              <option value={72}>72 hrs</option>
            </select>
          </div>
          <div className="flex gap-2">
            <button onClick={handleAcceptForward} disabled={submitting} className="btn-primary text-xs py-2 flex-1">
              {submitting ? <Spinner size="sm" /> : <><Send className="w-3.5 h-3.5 mr-1" /> Forward</>}
            </button>
            <button onClick={() => setAction(null)} className="btn-ghost text-xs py-2">Cancel</button>
          </div>
        </div>
      )}

      {/* Edit Form */}
      {action === "edit" && (
        <div className="card p-4 space-y-3 border-l-4 border-l-brand-400">
          <p className="text-xs font-semibold text-brand-700">Edit Summary & Forward</p>
          <textarea value={editedSummary} onChange={e => setEditedSummary(e.target.value)}
            rows={8} className="input text-xs w-full font-mono" />
          <input value={editReason} onChange={e => setEditReason(e.target.value)}
            placeholder="Reason for edit" className="input text-xs w-full" />
          <input value={targetDoctor} onChange={e => setTargetDoctor(e.target.value)}
            placeholder="Target Doctor ID" className="input text-xs w-full" />
          <div className="flex items-center gap-2">
            <label className="text-xs text-surface-500">Consent duration:</label>
            <select value={consentHours} onChange={e => setConsentHours(+e.target.value)} className="input text-xs w-24">
              <option value={6}>6 hrs</option>
              <option value={12}>12 hrs</option>
              <option value={24}>24 hrs</option>
              <option value={48}>48 hrs</option>
              <option value={72}>72 hrs</option>
            </select>
          </div>
          <div className="flex gap-2">
            <button onClick={handleEditForward} disabled={submitting} className="btn-primary text-xs py-2 flex-1">
              {submitting ? <Spinner size="sm" /> : <><Send className="w-3.5 h-3.5 mr-1" /> Edit & Forward</>}
            </button>
            <button onClick={() => setAction(null)} className="btn-ghost text-xs py-2">Cancel</button>
          </div>
        </div>
      )}

      {/* Reject Form */}
      {action === "reject" && (
        <div className="card p-4 space-y-3 border-l-4 border-l-red-400">
          <p className="text-xs font-semibold text-red-700">Reject — Data Mismatch</p>
          <textarea value={rejectionReason} onChange={e => setRejectionReason(e.target.value)}
            rows={3} placeholder="Describe what doesn't match the source document..." className="input text-xs w-full" />
          <div className="flex gap-2">
            <button onClick={handleReject} disabled={submitting} className="bg-red-600 text-white px-4 py-2 rounded-lg text-xs flex-1">
              {submitting ? <Spinner size="sm" /> : <><XCircle className="w-3.5 h-3.5 mr-1 inline" /> Confirm Reject</>}
            </button>
            <button onClick={() => setAction(null)} className="btn-ghost text-xs py-2">Cancel</button>
          </div>
        </div>
      )}

      {/* Escalate Form */}
      {action === "escalate" && (
        <div className="card p-4 space-y-3 border-l-4 border-l-amber-400">
          <p className="text-xs font-semibold text-amber-700">Escalate to Admin</p>
          <textarea value={escalationReason} onChange={e => setEscalationReason(e.target.value)}
            rows={3} placeholder="Identity mismatch, inconsistent records, etc..." className="input text-xs w-full" />
          <div className="flex gap-2">
            <button onClick={handleEscalate} disabled={submitting} className="bg-amber-600 text-white px-4 py-2 rounded-lg text-xs flex-1">
              {submitting ? <Spinner size="sm" /> : <><AlertTriangle className="w-3.5 h-3.5 mr-1 inline" /> Confirm Escalate</>}
            </button>
            <button onClick={() => setAction(null)} className="btn-ghost text-xs py-2">Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function HITLDashboard() {
  const { user } = useAuthStore();
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => { loadQueue(); }, []);

  const loadQueue = async () => {
    setLoading(true);
    try {
      const { data } = await screeningAPI.getHitlQueue();
      setQueue(data);
    } catch (err) {
      toast.error("Failed to load queue");
    } finally { setLoading(false); }
  };

  const handleDone = () => {
    setSelectedId(null);
    loadQueue();
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="page-title">HITL Validation Queue</h1>
          <p className="text-surface-500 text-sm mt-1">
            Review AI-generated screenings before they reach doctors
          </p>
        </div>
        <button onClick={loadQueue} className="btn-ghost flex items-center gap-1">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-surface-800">{queue.length}</p>
          <p className="text-xs text-surface-400">Pending Review</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-amber-600">{queue.filter(q => q.critical_count > 0).length}</p>
          <p className="text-xs text-surface-400">Critical Findings</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-brand-600">{queue.filter(q => q.abnormality_count > 0).length}</p>
          <p className="text-xs text-surface-400">With Abnormalities</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Queue List */}
        <div>
          <h2 className="section-title mb-3">Queue ({queue.length})</h2>
          {loading ? (
            <div className="flex justify-center py-12"><Spinner /></div>
          ) : queue.length === 0 ? (
            <EmptyState icon={CheckCircle2} title="All clear" description="No screenings pending review" />
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {queue.map((item) => (
                <QueueCard key={item.screening_id} item={item} onSelect={setSelectedId} />
              ))}
            </div>
          )}
        </div>

        {/* Review Panel */}
        <div>
          {selectedId ? (
            <ReviewPanel screeningId={selectedId} onDone={handleDone} />
          ) : (
            <div className="card p-12 flex flex-col items-center justify-center text-center">
              <Eye className="w-8 h-8 text-surface-300 mb-3" />
              <p className="text-sm text-surface-500">Select a screening to review</p>
              <p className="text-xs text-surface-400 mt-1">Click any item from the queue</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
