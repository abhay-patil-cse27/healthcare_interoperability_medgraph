import { useState, useEffect } from "react";
import {
  ClipboardList, Clock, CheckCircle2, Search,
  User, Stethoscope, RefreshCw, Plus, Calendar
} from "lucide-react";
import { opdAPI } from "../../services/api";
import toast from "react-hot-toast";
import Spinner from "../../components/ui/Spinner";

const STATUS_COLOR = {
  scheduled:  "badge-blue",
  completed:  "badge-green",
  cancelled:  "badge-red",
  no_show:    "badge-gray",
};

function fmt(d) {
  if (!d) return "—";
  return new Date(d).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

function fmtDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export default function OPDDashboard() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading]           = useState(true);
  const [search, setSearch]             = useState("");
  const [filter, setFilter]             = useState("all");

  useEffect(() => { fetchQueue(); }, []);

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const res = await opdAPI.listAppointments();
      setAppointments(Array.isArray(res.data) ? res.data : []);
    } catch {
      setAppointments([]);
      toast.error("Could not load appointments from server");
    } finally { setLoading(false); }
  };

  const updateStatus = async (id, status) => {
    try {
      await opdAPI.updateStatus(id, status);
      toast.success(`Status → ${status}`);
      fetchQueue();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Update failed");
    }
  };

  const filtered = appointments.filter(a => {
    const matchSearch = !search ||
      a.patient_name?.toLowerCase().includes(search.toLowerCase()) ||
      a.doctor_name?.toLowerCase().includes(search.toLowerCase());
    const matchFilter = filter === "all" || a.status === filter;
    return matchSearch && matchFilter;
  });

  const counts = appointments.reduce((acc, a) => {
    acc[a.status] = (acc[a.status] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="page-title">OPD Queue</h1>
          <p className="text-slate-500 text-sm mt-1">
            {fmtDate(new Date())} · Appointments & patient flow management
          </p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Patient or doctor..." className="input pl-9 w-52" />
          </div>
          <button onClick={fetchQueue} className="btn-ghost"><RefreshCw className="w-4 h-4" /></button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Today",  value: appointments.length, color: "border-l-blue-600" },
          { label: "Scheduled",    value: counts.scheduled  || 0, color: "border-l-amber-500" },
          { label: "Completed",    value: counts.completed  || 0, color: "border-l-emerald-500" },
          { label: "No Shows",     value: counts.no_show    || 0, color: "border-l-red-400" },
        ].map(s => (
          <div key={s.label} className={`card p-4 border-l-4 ${s.color}`}>
            <p className="text-2xl font-bold text-slate-900">{s.value}</p>
            <p className="text-sm text-slate-500 font-medium mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit">
        {["all", "scheduled", "completed", "cancelled"].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all capitalize ${filter === f ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}>
            {f}
          </button>
        ))}
      </div>

      {/* Appointment List */}
      {loading ? (
        <div className="card p-12 flex items-center justify-center gap-3 text-slate-400">
          <Spinner /> Loading appointments...
        </div>
      ) : filtered.length === 0 ? (
        <div className="card p-12 text-center">
          <ClipboardList className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 font-semibold">No appointments found</p>
          <p className="text-slate-400 text-sm mt-1">Appointments will appear here once booked</p>
        </div>
      ) : (
        <div className="card divide-y divide-slate-100">
          {filtered.map(a => (
            <div key={a.appointment_id} className="p-4 hover:bg-slate-50 transition-colors flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
                <Calendar className="w-5 h-5 text-blue-600" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="font-bold text-slate-900 text-sm">{a.patient_name || "Unknown Patient"}</p>
                  <span className={`badge ${STATUS_COLOR[a.status] || "badge-gray"}`}>{a.status}</span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1">
                  <Stethoscope className="w-3 h-3" />{a.doctor_name} · {a.department_name}
                </p>
                <p className="text-xs text-slate-400">{a.reason_for_visit}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-sm font-bold text-slate-900">{fmt(a.scheduled_time)}</p>
                {a.status === "scheduled" && (
                  <div className="flex gap-1 mt-1">
                    <button onClick={() => updateStatus(a.appointment_id, "completed")}
                      className="text-[10px] font-bold px-2 py-1 bg-emerald-50 text-emerald-700 rounded-lg border border-emerald-100 hover:bg-emerald-100 transition-colors">
                      ✓ Done
                    </button>
                    <button onClick={() => updateStatus(a.appointment_id, "no_show")}
                      className="text-[10px] font-bold px-2 py-1 bg-red-50 text-red-700 rounded-lg border border-red-100 hover:bg-red-100 transition-colors">
                      No Show
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
