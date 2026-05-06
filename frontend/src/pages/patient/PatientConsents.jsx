import { useState, useEffect, useCallback } from "react";
import { Shield, CheckCircle2, XCircle, Trash2, Clock, RefreshCw, User } from "lucide-react";
import toast from "react-hot-toast";
import { consentAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";
import StatusDot from "../../components/ui/StatusDot";

const SCOPE_LABELS = {
  full:             "Full Access",
  medication_only:  "Medications Only",
  disease_specific: "Disease Specific",
  time_bound:       "Time Bound",
};

const STATUS_BADGE = {
  pending:  "badge-yellow",
  approved: "badge-green",
  denied:   "badge-red",
  revoked:  "badge-gray",
  expired:  "badge-gray",
};

function ConsentCard({ consent, onAction }) {
  const [acting, setActing] = useState(false);

  const act = async (approved) => {
    setActing(true);
    try {
      await consentAPI.grant({ consent_id: consent.consent_id, patient_id: consent.patient_id, approved });
      toast.success(approved ? "Consent approved" : "Consent denied");
      onAction();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Action failed");
    } finally {
      setActing(false);
    }
  };

  const revoke = async () => {
    setActing(true);
    try {
      await consentAPI.revoke(consent.consent_id);
      toast.success("Consent revoked");
      onAction();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Revoke failed");
    } finally {
      setActing(false);
    }
  };

  return (
    <div className="card p-5 hover:shadow-card-hover transition-shadow">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <StatusDot status={consent.status} />
          <span className={`badge ${STATUS_BADGE[consent.status] || "badge-gray"}`}>
            {consent.status}
          </span>
          <span className="badge badge-blue">{SCOPE_LABELS[consent.requested_scope] || consent.requested_scope}</span>
        </div>
        <span className="text-xs text-surface-400">
          {new Date(consent.created_at).toLocaleDateString()}
        </span>
      </div>

      <div className="flex items-center gap-2 mb-2">
        <User className="w-3.5 h-3.5 text-surface-400" />
        <p className="text-xs text-surface-500 font-mono">{consent.doctor_id.slice(0, 16)}…</p>
      </div>

      <p className="text-sm text-surface-700 mb-3 line-clamp-2">{consent.purpose}</p>

      {consent.valid_until && (
        <p className="text-xs text-surface-400 flex items-center gap-1 mb-3">
          <Clock className="w-3 h-3" />
          Expires {new Date(consent.valid_until).toLocaleString()}
        </p>
      )}

      {/* Actions */}
      {consent.status === "pending" && (
        <div className="flex gap-2 pt-3 border-t border-surface-100">
          <button onClick={() => act(true)} disabled={acting} className="btn-primary flex-1 justify-center py-1.5 text-xs">
            {acting ? <Spinner size="sm" /> : <><CheckCircle2 className="w-3.5 h-3.5" /> Approve</>}
          </button>
          <button onClick={() => act(false)} disabled={acting} className="btn-danger flex-1 justify-center py-1.5 text-xs">
            {acting ? <Spinner size="sm" /> : <><XCircle className="w-3.5 h-3.5" /> Deny</>}
          </button>
        </div>
      )}

      {consent.status === "approved" && (
        <div className="pt-3 border-t border-surface-100">
          <button onClick={revoke} disabled={acting} className="btn-ghost text-red-500 hover:bg-red-50 text-xs w-full justify-center">
            {acting ? <Spinner size="sm" /> : <><Trash2 className="w-3.5 h-3.5" /> Revoke Access</>}
          </button>
        </div>
      )}
    </div>
  );
}

export default function PatientConsents() {
  const { user } = useAuthStore();
  const [consents, setConsents] = useState([]);
  const [loading, setLoading]   = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await consentAPI.active(user.user_id);
      setConsents(data);
    } catch {
      toast.error("Failed to load consents");
    } finally {
      setLoading(false);
    }
  }, [user.user_id]);

  useEffect(() => { load(); }, [load]);

  const pending  = consents.filter((c) => c.status === "pending");
  const approved = consents.filter((c) => c.status === "approved");
  const others   = consents.filter((c) => !["pending", "approved"].includes(c.status));

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Consent Manager</h1>
          <p className="text-sm text-surface-500 mt-1">Control who can access your health data and what they can see.</p>
        </div>
        <button onClick={load} className="btn-secondary">
          {loading ? <Spinner size="sm" /> : <RefreshCw className="w-4 h-4" />}
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Pending",  count: pending.length,  color: "text-amber-600",  bg: "bg-amber-50",  border: "border-amber-200" },
          { label: "Active",   count: approved.length, color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200" },
          { label: "Total",    count: consents.length, color: "text-brand-600",  bg: "bg-brand-50",  border: "border-brand-200" },
        ].map((s) => (
          <div key={s.label} className={`card p-4 ${s.bg} border ${s.border}`}>
            <p className={`text-2xl font-bold ${s.color}`}>{s.count}</p>
            <p className="text-xs text-surface-600 mt-0.5">{s.label} Requests</p>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : consents.length === 0 ? (
        <div className="card p-8">
          <EmptyState icon={Shield} title="No consent requests" description="When doctors request access to your records, they'll appear here for your approval." />
        </div>
      ) : (
        <>
          {pending.length > 0 && (
            <div>
              <h2 className="section-title mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-500" />
                Pending Approval ({pending.length})
              </h2>
              <div className="grid gap-3 sm:grid-cols-2">
                {pending.map((c) => <ConsentCard key={c.consent_id} consent={c} onAction={load} />)}
              </div>
            </div>
          )}

          {approved.length > 0 && (
            <div>
              <h2 className="section-title mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                Active Access ({approved.length})
              </h2>
              <div className="grid gap-3 sm:grid-cols-2">
                {approved.map((c) => <ConsentCard key={c.consent_id} consent={c} onAction={load} />)}
              </div>
            </div>
          )}

          {others.length > 0 && (
            <div>
              <h2 className="section-title mb-3 text-surface-500">History</h2>
              <div className="grid gap-3 sm:grid-cols-2">
                {others.map((c) => <ConsentCard key={c.consent_id} consent={c} onAction={load} />)}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
