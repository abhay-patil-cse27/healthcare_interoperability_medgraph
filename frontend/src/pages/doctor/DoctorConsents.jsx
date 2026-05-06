import { useState } from "react";
import { Shield, RefreshCw, Clock, CheckCircle2, XCircle, Plus, Send } from "lucide-react";
import toast from "react-hot-toast";
import { consentAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";
import Spinner from "../../components/ui/Spinner";
import PatientSearchBar from "../../components/ui/PatientSearchBar";

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

export default function DoctorConsents() {
  const { user }                    = useAuthStore();
  const [selectedPatient, setSelPt] = useState(null);
  const [consents, setConsents]     = useState([]);
  const [loading, setLoading]       = useState(false);
  const [searched, setSearched]     = useState(false);
  const [showForm, setShowForm]     = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [form, setForm]             = useState({ purpose: "", requested_scope: "full", duration_hours: 24 });

  const handleRequestConsent = async (e) => {
    e.preventDefault();
    if (!selectedPatient) return;
    setRequesting(true);
    try {
      await consentAPI.request({
        doctor_id: user.user_id,
        patient_id: selectedPatient.user_id,
        purpose: form.purpose,
        requested_scope: form.requested_scope,
        duration_hours: Number(form.duration_hours),
      });
      toast.success("Consent request sent to patient");
      setShowForm(false);
      setForm({ purpose: "", requested_scope: "full", duration_hours: 24 });
      handleSelect(selectedPatient);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to request consent");
    } finally {
      setRequesting(false);
    }
  };

  const handleSelect = async (patient) => {
    setSelPt(patient);
    setLoading(true);
    setSearched(true);
    try {
      const { data } = await consentAPI.active(patient.user_id);
      setConsents(data.filter((c) => c.doctor_id === user.user_id));
    } catch {
      toast.error("Failed to load consents");
    } finally { setLoading(false); }
  };

  const active  = consents.filter(c => c.status === "approved");
  const pending = consents.filter(c => c.status === "pending");
  const others  = consents.filter(c => !["approved","pending"].includes(c.status));

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-title">My Consent Requests</h1>
        <p className="text-sm text-slate-500 mt-1">
          Track your patient access requests. Search by name, MRN, phone or ABHA ID.
        </p>
      </div>

      {/* Patient Search */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-2">
          <label className="label mb-0">Find Patient</label>
          {selectedPatient && (
            <div className="flex gap-2">
              <button
                onClick={() => handleSelect(selectedPatient)}
                disabled={loading}
                className="btn-ghost text-xs"
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
              </button>
              <button
                onClick={() => setShowForm(!showForm)}
                className="btn-primary text-xs py-1 px-2 h-auto"
              >
                <Plus className="w-3.5 h-3.5 mr-1" /> New Request
              </button>
            </div>
          )}
        </div>
        <PatientSearchBar
          selected={selectedPatient}
          onSelect={handleSelect}
          onClear={() => { setSelPt(null); setConsents([]); setSearched(false); setShowForm(false); }}
          placeholder="Search by name, MRN (AIIMS-2026-00001), phone or ABHA…"
        />
      </div>

      {/* New Consent Form */}
      {selectedPatient && showForm && (
        <div className="card p-5 border-blue-100 bg-blue-50/50 animate-fade-in">
          <h2 className="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Shield className="w-4 h-4 text-blue-500" />
            Request Consent for {selectedPatient.full_name}
          </h2>
          <form onSubmit={handleRequestConsent} className="space-y-4">
            <div>
              <label className="label">Purpose of Access</label>
              <input
                required
                type="text"
                className="input"
                placeholder="e.g. Follow-up consultation for hypertension"
                value={form.purpose}
                onChange={e => setForm({...form, purpose: e.target.value})}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Access Scope</label>
                <select 
                  className="input" 
                  value={form.requested_scope}
                  onChange={e => setForm({...form, requested_scope: e.target.value})}
                >
                  <option value="full">Full Access</option>
                  <option value="medication_only">Medications Only</option>
                  <option value="disease_specific">Disease Specific</option>
                  <option value="time_bound">Time Bound</option>
                </select>
              </div>
              <div>
                <label className="label">Duration (Hours)</label>
                <input
                  required
                  type="number"
                  min="1"
                  max="8760"
                  className="input"
                  value={form.duration_hours}
                  onChange={e => setForm({...form, duration_hours: e.target.value})}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowForm(false)} className="btn-ghost">
                Cancel
              </button>
              <button type="submit" disabled={requesting} className="btn-primary">
                {requesting ? <Spinner className="w-4 h-4 mr-2" /> : <Send className="w-4 h-4 mr-2" />}
                Send Request
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="card p-10 flex items-center justify-center gap-3 text-slate-400">
          <Spinner /> Loading consents…
        </div>
      )}

      {/* Results */}
      {searched && !loading && (
        consents.length === 0 ? (
          <div className="card p-10 text-center">
            <Shield className="w-10 h-10 text-slate-200 mx-auto mb-3" />
            <p className="text-slate-500 font-semibold">No requests found</p>
            <p className="text-slate-400 text-sm mt-1 mb-4">
              You haven't made any consent requests for {selectedPatient?.full_name}.
            </p>
            <button onClick={() => setShowForm(true)} className="btn-primary inline-flex">
              <Plus className="w-4 h-4 mr-2" /> Request Consent
            </button>
          </div>
        ) : (
          <div className="space-y-5">
            <div className="grid grid-cols-3 gap-3">
              {[
                { label:"Active",  count: active.length,  color:"border-l-emerald-500" },
                { label:"Pending", count: pending.length, color:"border-l-amber-500" },
                { label:"Total",   count: consents.length,color:"border-l-blue-500" },
              ].map(s => (
                <div key={s.label} className={`card p-4 border-l-4 ${s.color}`}>
                  <p className="text-2xl font-bold text-slate-900">{s.count}</p>
                  <p className="text-sm text-slate-500 font-medium mt-0.5">{s.label}</p>
                </div>
              ))}
            </div>

            {[
              { list: active,  icon: CheckCircle2, label:"Active Access",     color:"text-emerald-500" },
              { list: pending, icon: Clock,        label:"Awaiting Approval", color:"text-amber-500" },
              { list: others,  icon: XCircle,      label:"History",           color:"text-slate-400" },
            ].map(({ list, icon: Icon, label, color }) =>
              list.length > 0 ? (
                <div key={label}>
                  <h2 className="section-title mb-3 flex items-center gap-2">
                    <Icon className={`w-4 h-4 ${color}`} /> {label} ({list.length})
                  </h2>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {list.map(c => (
                      <div key={c.consent_id} className="card p-4">
                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                          <span className={`badge ${STATUS_BADGE[c.status] || "badge-gray"}`}>{c.status}</span>
                          <span className="badge badge-blue">{SCOPE_LABELS[c.requested_scope] || c.requested_scope}</span>
                        </div>
                        <p className="text-sm text-slate-700 mb-2 line-clamp-2">{c.purpose}</p>
                        {c.valid_until && (
                          <p className="text-xs text-slate-400 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            Expires {new Date(c.valid_until).toLocaleString()}
                          </p>
                        )}
                        <p className="text-xs text-slate-400 mt-1">
                          Requested {new Date(c.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null
            )}
          </div>
        )
      )}

      {!searched && (
        <div className="card p-12 text-center">
          <Shield className="w-10 h-10 text-slate-200 mx-auto mb-3" />
          <p className="text-slate-500 font-semibold">Search for a patient above</p>
          <p className="text-slate-400 text-sm mt-1">
            Type a name, MRN, phone number, or ABHA ID to look up consent requests.
          </p>
        </div>
      )}
    </div>
  );
}
