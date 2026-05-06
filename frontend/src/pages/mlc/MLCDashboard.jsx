import { useState, useEffect } from "react";
import { Shield, Lock, AlertCircle, RefreshCw, Search, FileText } from "lucide-react";
import { mlcAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";
import toast from "react-hot-toast";
import Spinner from "../../components/ui/Spinner";

function timeAgo(d) {
  if (!d) return "—";
  const diff = (Date.now() - new Date(d).getTime()) / 1000;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

const CASE_COLORS = {
  accident:  "bg-amber-50 text-amber-700 border-amber-100",
  assault:   "bg-red-50 text-red-700 border-red-100",
  poisoning: "bg-purple-50 text-purple-700 border-purple-100",
  burn:      "bg-orange-50 text-orange-700 border-orange-100",
};

export default function MLCDashboard() {
  const { user }          = useAuthStore();
  const [records, setRecords] = useState([]);
  const [stats, setStats]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState("");
  const isPolice = user?.role === "police_interface";

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [recRes, statsRes] = await Promise.all([
        mlcAPI.listRecords(),
        mlcAPI.getStats(),
      ]);
      setRecords(recRes.data);
      setStats(statsRes.data);
    } catch (err) {
      toast.error("Failed to load MLC records");
    } finally { setLoading(false); }
  };

  const filtered = records.filter(r =>
    !search ||
    r.case_type?.toLowerCase().includes(search.toLowerCase()) ||
    r.fir_number?.toLowerCase().includes(search.toLowerCase()) ||
    r.injury_description?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="page-title">Medico-Legal Cases</h1>
          <p className="text-slate-500 text-sm mt-1">
            {isPolice
              ? "Read-only access — police interface (limited fields, time-restricted)"
              : "Forensic MLC record management — immutable after 24h"}
          </p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="FIR / Case type..." className="input pl-9 w-52" />
          </div>
          <button onClick={fetchAll} className="btn-ghost"><RefreshCw className="w-4 h-4" /></button>
        </div>
      </div>

      {/* Police access notice */}
      {isPolice && (
        <div className="flex gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl">
          <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-bold text-amber-900">Police Interface — Read-Only Access</p>
            <p className="text-xs text-amber-700 mt-1">
              You can view case types, FIR numbers, and injury descriptions only.
              Patient identity and clinical details are restricted per DPDP Act 2023.
            </p>
          </div>
        </div>
      )}

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label:"Total Cases",    value: stats.total,    color:"border-l-blue-600" },
            { label:"Open / Active",  value: stats.open,     color:"border-l-amber-500" },
            { label:"Locked (>24h)",  value: stats.locked,   color:"border-l-slate-400" },
            { label:"FIR Filed",      value: stats.with_fir, color:"border-l-red-500" },
          ].map(({ label, value, color }) => (
            <div key={label} className={`card p-4 border-l-4 ${color}`}>
              <p className="text-2xl font-bold text-slate-900">{value}</p>
              <p className="text-sm text-slate-500 font-medium mt-1">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Records */}
      {loading ? (
        <div className="card p-12 flex items-center justify-center gap-3 text-slate-400"><Spinner />Loading records...</div>
      ) : filtered.length === 0 ? (
        <div className="card p-12 text-center">
          <Shield className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 font-semibold">No MLC records found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(r => (
            <div key={r.mlc_id} className={`card p-5 border-l-4 ${r.is_locked ? "border-l-slate-300" : "border-l-red-500"}`}>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="flex items-start gap-4 min-w-0">
                  <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${r.is_locked ? "bg-slate-100" : "bg-red-50"}`}>
                    {r.is_locked
                      ? <Lock className="w-5 h-5 text-slate-400" />
                      : <Shield className="w-5 h-5 text-red-600" />
                    }
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full border capitalize ${CASE_COLORS[r.case_type] || "bg-slate-50 text-slate-600 border-slate-200"}`}>
                        {r.case_type}
                      </span>
                      {r.is_locked && (
                        <span className="text-xs font-bold px-2 py-0.5 bg-slate-100 text-slate-500 rounded-full border border-slate-200 flex items-center gap-1">
                          <Lock className="w-3 h-3" /> Immutable
                        </span>
                      )}
                      {r.fir_number && (
                        <span className="text-xs font-bold px-2 py-0.5 bg-red-50 text-red-700 rounded-full border border-red-100 font-mono">
                          FIR: {r.fir_number}
                        </span>
                      )}
                    </div>
                    {/* Show patient info only to non-police */}
                    {!isPolice && r.patient_name && (
                      <p className="text-sm font-semibold text-slate-900">{r.patient_name}</p>
                    )}
                    <p className="text-sm text-slate-600 mt-1 leading-relaxed">{r.injury_description}</p>
                    {r.police_station && (
                      <p className="text-xs text-slate-400 mt-1">
                        Station: {r.police_station}
                      </p>
                    )}
                    {!isPolice && r.doctor_name && (
                      <p className="text-xs text-slate-400 mt-1">Recorded by: {r.doctor_name}</p>
                    )}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-xs text-slate-400">{timeAgo(r.created_at)}</p>
                  {!isPolice && !r.is_locked && (
                    <span className="text-[10px] text-amber-600 font-bold mt-1 block">Locks in &lt;24h</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
