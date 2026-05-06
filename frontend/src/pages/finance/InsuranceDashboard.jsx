import { useState, useEffect } from "react";
import {
  FileText, CheckCircle2, XCircle, Clock,
  RefreshCw, Search, ChevronDown, AlertCircle, TrendingUp
} from "lucide-react";
import { financeAPI } from "../../services/api";
import toast from "react-hot-toast";
import Spinner from "../../components/ui/Spinner";

const STATUS_META = {
  initiated:        { label:"Initiated",        color:"bg-slate-100 text-slate-700",  dot:"bg-slate-400" },
  pre_auth_pending: { label:"Pre-Auth Pending",  color:"bg-amber-50 text-amber-700",   dot:"bg-amber-500" },
  approved:         { label:"Approved",          color:"bg-emerald-50 text-emerald-700",dot:"bg-emerald-500" },
  rejected:         { label:"Rejected",          color:"bg-red-50 text-red-700",        dot:"bg-red-500" },
  settled:          { label:"Settled",           color:"bg-blue-50 text-blue-700",      dot:"bg-blue-500" },
};

function fmt(n) {
  if (!n && n !== 0) return "—";
  return "₹" + Number(n).toLocaleString("en-IN");
}

function timeAgo(d) {
  if (!d) return "—";
  const diff = (Date.now() - new Date(d).getTime()) / 1000;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function InsuranceDashboard() {
  const [claims, setClaims]       = useState([]);
  const [stats, setStats]         = useState(null);
  const [loading, setLoading]     = useState(true);
  const [filter, setFilter]       = useState("all");
  const [search, setSearch]       = useState("");
  const [updating, setUpdating]   = useState(null);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [claimsRes, statsRes] = await Promise.all([
        financeAPI.listClaims(),
        financeAPI.getClaimStats(),
      ]);
      setClaims(claimsRes.data);
      setStats(statsRes.data);
    } catch (err) {
      toast.error("Failed to load claims data");
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (claimId, newStatus) => {
    setUpdating(claimId);
    try {
      await financeAPI.updateClaim(claimId, newStatus);
      toast.success(`Claim updated → ${newStatus}`);
      fetchAll();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Update failed");
    } finally { setUpdating(null); }
  };

  const filtered = claims.filter(c => {
    const matchStatus = filter === "all" || c.status === filter;
    const matchSearch = !search ||
      c.patient_name?.toLowerCase().includes(search.toLowerCase()) ||
      c.claim_id?.toLowerCase().includes(search.toLowerCase()) ||
      c.tpa_name?.toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="page-title">Insurance Claims</h1>
          <p className="text-slate-500 text-sm mt-1">TPA management, pre-authorization, and settlement</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Patient / Claim ID..." className="input pl-9 w-56" />
          </div>
          <button onClick={fetchAll} className="btn-ghost"><RefreshCw className="w-4 h-4" /></button>
        </div>
      </div>

      {/* Stats Row */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { label:"Initiated",      value: stats.initiated,    color:"border-l-slate-400" },
            { label:"Pre-Auth Pend.", value: stats.pre_auth_pending, color:"border-l-amber-500" },
            { label:"Approved",       value: stats.approved,     color:"border-l-emerald-500" },
            { label:"Rejected",       value: stats.rejected,     color:"border-l-red-500" },
            { label:"Settled",        value: stats.settled,      color:"border-l-blue-500" },
            { label:"Total Settled",  value: fmt(stats.total_settled_amount), color:"border-l-purple-500" },
          ].map(({ label, value, color }) => (
            <div key={label} className={`card p-4 border-l-4 ${color}`}>
              <p className="text-xl font-bold text-slate-900">{value}</p>
              <p className="text-xs text-slate-500 font-medium mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit flex-wrap">
        {[["all","All"], ...Object.entries(STATUS_META).map(([k,v]) => [k, v.label])].map(([val, lbl]) => (
          <button key={val} onClick={() => setFilter(val)}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${filter === val ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
          >{lbl}</button>
        ))}
      </div>

      {/* Claims Table */}
      {loading ? (
        <div className="card p-12 flex items-center justify-center gap-3 text-slate-400"><Spinner />Loading claims...</div>
      ) : filtered.length === 0 ? (
        <div className="card p-12 text-center">
          <FileText className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 font-semibold">No claims found</p>
        </div>
      ) : (
        <div className="card divide-y divide-slate-100">
          {filtered.map(c => {
            const meta = STATUS_META[c.status] || STATUS_META.initiated;
            return (
              <div key={c.claim_id} className="p-4 hover:bg-slate-50 transition-colors">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="flex items-center gap-4 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
                      <FileText className="w-5 h-5 text-blue-600" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-bold text-slate-900 text-sm font-mono">{c.claim_id?.slice(0,15)}…</h3>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border flex items-center gap-1 ${meta.color}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />{meta.label}
                        </span>
                        {c.scheme && <span className="text-[10px] font-bold px-2 py-0.5 bg-purple-50 text-purple-700 rounded-full border border-purple-100">{c.scheme}</span>}
                      </div>
                      <p className="text-sm text-slate-600 font-medium mt-0.5">{c.patient_name}</p>
                      <p className="text-xs text-slate-400">{c.tpa_name} · {c.diagnosis_code} · {timeAgo(c.submitted_at)}</p>
                      {c.notes && <p className="text-xs text-slate-400 mt-1 italic truncate max-w-md">{c.notes}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-6 shrink-0">
                    <div className="text-right">
                      <p className="text-sm font-bold text-slate-900">{fmt(c.claim_amount)}</p>
                      {c.approved_amount && <p className="text-xs text-emerald-600 font-semibold">Approved: {fmt(c.approved_amount)}</p>}
                    </div>
                    {/* Action dropdown based on current status */}
                    {c.status === "initiated" && (
                      <button onClick={() => handleStatusUpdate(c.claim_id, "pre_auth_pending")} disabled={updating === c.claim_id} className="btn-secondary text-xs py-1.5">
                        {updating === c.claim_id ? <Spinner size="sm" /> : "Submit Pre-Auth"}
                      </button>
                    )}
                    {c.status === "pre_auth_pending" && (
                      <div className="flex gap-2">
                        <button onClick={() => handleStatusUpdate(c.claim_id, "approved")} disabled={updating === c.claim_id} className="btn-primary text-xs py-1.5">
                          <CheckCircle2 className="w-3 h-3" /> Approve
                        </button>
                        <button onClick={() => handleStatusUpdate(c.claim_id, "rejected")} disabled={updating === c.claim_id} className="btn-secondary text-xs py-1.5 text-red-600">
                          <XCircle className="w-3 h-3" /> Reject
                        </button>
                      </div>
                    )}
                    {c.status === "approved" && (
                      <button onClick={() => handleStatusUpdate(c.claim_id, "settled")} disabled={updating === c.claim_id} className="btn-primary text-xs py-1.5">
                        {updating === c.claim_id ? <Spinner size="sm" /> : "Mark Settled"}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
