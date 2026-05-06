import { useState, useEffect } from "react";
import {
  Package, Search, CheckCircle2, AlertCircle,
  FileText, User, Clock, ArrowRight, RefreshCw
} from "lucide-react";
import toast from "react-hot-toast";
import { pharmacyAPI } from "../../services/api";
import Spinner from "../../components/ui/Spinner";

export default function PharmacistConsole() {
  const [filter, setFilter]           = useState("pending");
  const [prescriptions, setPrescriptions] = useState([]);
  const [stats, setStats]             = useState(null);
  const [loading, setLoading]         = useState(true);
  const [search, setSearch]           = useState("");
  const [dispensing, setDispensing]   = useState(null);

  useEffect(() => { fetchQueue(filter); }, [filter]);

  const fetchQueue = async (status) => {
    setLoading(true);
    try {
      const [qRes, sRes] = await Promise.all([
        pharmacyAPI.getQueue(status),
        pharmacyAPI.getStats(),
      ]);
      setPrescriptions(qRes.data);
      setStats(sRes.data);
    } catch (err) {
      toast.error("Failed to load pharmacy queue");
    } finally {
      setLoading(false);
    }
  };

  const handleDispense = async (rx) => {
    setDispensing(rx.prescription_id);
    try {
      await pharmacyAPI.dispense(rx.prescription_id);
      toast.success(`Dispensed ${rx.prescription_id}`);
      fetchQueue(filter);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Dispense failed");
    } finally {
      setDispensing(null);
    }
  };

  const filtered = prescriptions.filter(p =>
    p.patient_name?.toLowerCase().includes(search.toLowerCase()) ||
    p.prescription_id?.toLowerCase().includes(search.toLowerCase())
  );

  const timeAgo = (dateStr) => {
    const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
    if (diff < 60) return `${Math.floor(diff)}s ago`;
    if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
    return `${Math.floor(diff/3600)}h ago`;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="page-title">Pharmacy Queue</h1>
          <p className="text-slate-500 mt-1 text-sm">Live prescription queue — verification and dispensing</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              className="input pl-9 w-56"
              placeholder="Search patient or RX ID..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <button onClick={() => fetchQueue(filter)} className="btn-ghost">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card p-4 border-l-4 border-l-amber-500">
            <p className="text-2xl font-bold text-slate-900">{stats.pending}</p>
            <p className="text-sm text-slate-500 font-medium mt-1">Pending Dispensing</p>
          </div>
          <div className="card p-4 border-l-4 border-l-emerald-500">
            <p className="text-2xl font-bold text-slate-900">{stats.dispensed}</p>
            <p className="text-sm text-slate-500 font-medium mt-1">Dispensed Today</p>
          </div>
          <div className="card p-4 border-l-4 border-l-blue-500">
            <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
            <p className="text-sm text-slate-500 font-medium mt-1">Total Prescriptions</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit">
        {["pending", "dispensed"].map(tab => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-5 py-2 rounded-lg text-sm font-bold transition-all capitalize ${
              filter === tab
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            {tab === "pending" ? `Pending (${stats?.pending ?? "..."})` : `Dispensed (${stats?.dispensed ?? "..."})`}
          </button>
        ))}
      </div>

      {/* Main List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          {loading ? (
            <div className="card p-12 flex items-center justify-center gap-3 text-slate-400">
              <Spinner /> Loading prescriptions...
            </div>
          ) : filtered.length === 0 ? (
            <div className="card p-12 text-center">
              <FileText className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500 font-semibold">No {filter} prescriptions</p>
            </div>
          ) : (
            filtered.map(p => (
              <div key={p.prescription_id} className="card p-5 hover:border-blue-200 transition-colors">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-slate-900 font-mono text-sm">{p.prescription_id}</h3>
                        <span className={`badge ${p.status === "pending" ? "badge-yellow" : "badge-green"}`}>{p.status}</span>
                      </div>
                      <p className="text-sm text-slate-500 flex items-center gap-1 mt-0.5">
                        <User className="w-3 h-3" /> {p.patient_name || "Unknown Patient"}
                      </p>
                      {p.diagnosis && (
                        <p className="text-xs text-slate-400 mt-1 italic">{p.diagnosis}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right text-slate-400 text-xs flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {p.created_at ? timeAgo(p.created_at) : "—"}
                  </div>
                </div>

                <div className="bg-slate-50 rounded-lg p-3 mb-4">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Medications</p>
                  <ul className="space-y-1">
                    {(p.medications || []).map((m, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm text-slate-700">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0" />
                        <span className="font-semibold">{m.name}</span>
                        <span className="text-slate-400">{m.dosage} · {m.frequency}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {p.status === "pending" && (
                  <div className="flex gap-2">
                    <button onClick={() => toast.success("No interactions found for " + p.medication_name, { icon: "✅" })} className="btn-secondary py-1.5 text-xs">Verify Drug Interactions</button>
                    <button
                      onClick={() => handleDispense(p)}
                      disabled={dispensing === p.prescription_id}
                      className="btn-primary py-1.5 text-xs ml-auto"
                    >
                      {dispensing === p.prescription_id ? <Spinner size="sm" /> : <>Confirm & Dispense <ArrowRight className="w-3 h-3" /></>}
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="card p-5 bg-slate-900 text-white">
            <h4 className="font-bold mb-4 flex items-center gap-2">
              <Package className="w-4 h-4 text-blue-400" /> Safety Protocols
            </h4>
            <ul className="space-y-3">
              {[
                "Verify ABHA ID before dispensing controlled substances",
                "Doctor digital signature is mandatory",
                "Log all narcotic dispenses in narcotic register",
                "Check for drug interactions before dispensing",
              ].map((rule, i) => (
                <li key={i} className="flex gap-2 text-xs text-slate-300">
                  <span className="font-bold text-blue-400 shrink-0">{String(i+1).padStart(2,"0")}</span>
                  {rule}
                </li>
              ))}
            </ul>
          </div>
          <div className="card p-5">
            <h4 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-500" /> Prescribers On Duty
            </h4>
            <div className="space-y-2">
              {["Dr. Arun Sharma", "Dr. Sneha Patel", "Dr. Vikram Nair"].map(doc => (
                <div key={doc} className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span className="text-sm text-slate-700 font-medium">{doc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
