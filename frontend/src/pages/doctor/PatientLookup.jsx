import { useState, useEffect } from "react";
import {
  Stethoscope, Bed, ClipboardList, Clock, Users,
  Search, RefreshCw, ChevronRight, AlertTriangle,
  FileText, Activity, User, Calendar, ArrowRight,
  HeartPulse, Thermometer, Wind, Droplet
} from "lucide-react";
import { nurseAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";
import toast from "react-hot-toast";
import Spinner from "../../components/ui/Spinner";
import PatientDetailDrawer from "./PatientDetailDrawer";
import { SparkLine } from "../../components/ui/MiniCharts";

function timeAgo(d) {
  if (!d) return "—";
  const diff = (Date.now() - new Date(d).getTime()) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function fmtDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

const STATUS_BADGE = {
  admitted:    "badge-blue",
  completed:   "badge-green",
  scheduled:   "badge-yellow",
  discharged:  "badge-gray",
  dispensed:   "badge-green",
};

export default function PatientLookup() {
  const { user } = useAuthStore();
  const [data, setData]             = useState(null);
  const [loading, setLoading]       = useState(true);
  const [tab, setTab]               = useState("active");
  const [search, setSearch]         = useState("");
  const [selectedPatient, setSelectedPatient] = useState(null);

  useEffect(() => { fetchMyPatients(); }, []);

  const fetchMyPatients = async () => {
    setLoading(true);
    try {
      const res = await nurseAPI.getMyPatients();
      setData(res.data);
    } catch (err) {
      toast.error("Failed to load patient list");
    } finally { setLoading(false); }
  };

  const filterSearch = (items, fields) => {
    if (!search) return items;
    return items.filter(item =>
      fields.some(f => item[f]?.toLowerCase().includes(search.toLowerCase()))
    );
  };

  const tabs = [
    { id: "active",     label: "Active IPD",     count: data?.summary?.active_inpatients },
    { id: "opd",        label: "OPD Queue",       count: data?.summary?.todays_opd },
    { id: "registered", label: "My Patients",     count: data?.summary?.registered_count },
    { id: "history",    label: "Past History",    count: data?.summary?.total_history },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="page-title">My Patients</h1>
          <p className="text-slate-500 text-sm mt-1">
            {user?.full_name} · Active cases, OPD queue, and patient history
          </p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search patients..." className="input pl-9 w-52" />
          </div>
          <button onClick={fetchMyPatients} className="btn-ghost">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {loading ? (
        <div className="grid grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <div key={i} className="card p-5 animate-pulse h-20 bg-slate-100" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label:"Active Inpatients",  value: data?.summary?.active_inpatients ?? 0, color:"border-l-blue-600",   icon: Bed,           spark: [3,4,3,5,4,3,data?.summary?.active_inpatients ?? 3] },
            { label:"Today's OPD",        value: data?.summary?.todays_opd ?? 0,        color:"border-l-amber-500",  icon: Calendar,      spark: [8,12,10,15,9,11,data?.summary?.todays_opd ?? 8] },
            { label:"Registered Patients",value: data?.summary?.registered_count ?? 0,  color:"border-l-emerald-500",icon: Users,         spark: [5,7,9,12,14,18,data?.summary?.registered_count ?? 20] },
            { label:"Total History",      value: data?.summary?.total_history ?? 0,      color:"border-l-purple-500", icon: ClipboardList, spark: [2,4,6,5,8,10,data?.summary?.total_history ?? 12] },
          ].map(({ label, value, color, icon: Icon, spark }) => (
            <div key={label} className={`card p-5 border-l-4 ${color}`}>
              <div className="flex items-center justify-between mb-2">
                <Icon className="w-5 h-5 text-slate-400" />
              </div>
              <p className="text-2xl font-bold text-slate-900">{value}</p>
              <p className="text-sm text-slate-500 font-medium mt-0.5">{label}</p>
              <SparkLine data={spark.map((v,i) => ({value: v}))} color={color.includes("blue") ? "blue" : color.includes("amber") ? "amber" : color.includes("emerald") ? "emerald" : "purple"} height={28} className="mt-2" />
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              tab === t.id ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
            }`}>
            {t.label}
            {t.count != null && (
              <span className={`text-[10px] font-black px-1.5 py-0.5 rounded-full ${tab === t.id ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-600"}`}>
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="card p-12 flex items-center justify-center gap-3 text-slate-400">
          <Spinner /> Loading patients...
        </div>
      ) : (
        <div>
          {/* ACTIVE IPD */}
          {tab === "active" && (
            <div className="space-y-3">
              {(filterSearch(data?.active_admissions || [], ["patient_name","diagnosis","bed_label"])).length === 0 ? (
                <EmptyState icon={Bed} label="No active IPD patients" sub="Your current inpatients will appear here" />
              ) : (
                filterSearch(data?.active_admissions || [], ["patient_name","diagnosis","bed_label"]).map(a => (
                  <div key={a.admission_id} className="card p-5 border-l-4 border-l-blue-500 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => setSelectedPatient({ id: a.patient_id, name: a.patient_name })}>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-center gap-4">
                        <div className="w-11 h-11 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
                          <Bed className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="font-bold text-slate-900">{a.patient_name}</h3>
                            <span className="badge badge-blue">{a.bed_label || "IPD"}</span>
                            {a.is_mlc && <span className="badge badge-red">MLC</span>}
                            {a.scheme_applied && <span className="badge badge-blue">{a.scheme_applied}</span>}
                          </div>
                          <p className="text-sm text-slate-600 mt-1">{a.diagnosis}</p>
                          <p className="text-xs text-slate-400 mt-0.5">Admitted {timeAgo(a.admission_time)}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="badge badge-blue capitalize">{a.status}</span>
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* OPD QUEUE */}
          {tab === "opd" && (
            <div className="space-y-2">
              {(filterSearch(data?.todays_appointments || [], ["patient_name","reason_for_visit","department_name"])).length === 0 ? (
                <EmptyState icon={Calendar} label="No appointments" sub="Scheduled appointments will appear here" />
              ) : (
                <div className="card divide-y divide-slate-100">
                  {filterSearch(data?.todays_appointments || [], ["patient_name","reason_for_visit","department_name"]).map(a => (
                    <div key={a.appointment_id} className="p-4 hover:bg-slate-50 flex items-center gap-4 cursor-pointer transition-colors"
                      onClick={() => setSelectedPatient({ id: a.patient_id, name: a.patient_name })}>
                      <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center shrink-0">
                        <Stethoscope className="w-5 h-5 text-amber-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-bold text-slate-900 text-sm">{a.patient_name}</p>
                          <span className={`badge ${STATUS_BADGE[a.status] || "badge-gray"}`}>{a.status}</span>
                        </div>
                        <p className="text-xs text-slate-500 truncate">{a.reason_for_visit}</p>
                        <p className="text-xs text-slate-400">{a.department_name}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <p className="text-sm font-bold text-slate-900">
                          {a.scheduled_time ? new Date(a.scheduled_time).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }) : "—"}
                        </p>
                        <p className="text-xs text-slate-400">{fmtDate(a.scheduled_time)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* REGISTERED PATIENTS */}
          {tab === "registered" && (
            <div className="space-y-2">
              {(filterSearch(data?.registered_patients || [], ["full_name","email","phone"])).length === 0 ? (
                <EmptyState icon={Users} label="No registered patients" sub="Patients who've had appointments with you will appear here" />
              ) : (
                <div className="card divide-y divide-slate-100">
                  {filterSearch(data?.registered_patients || [], ["full_name","email","phone"]).map(p => (
                    <div key={p.user_id} className="p-4 hover:bg-slate-50 flex items-center gap-4 cursor-pointer transition-colors"
                      onClick={() => setSelectedPatient({ id: p.user_id, name: p.full_name })}>
                      <div className="w-10 h-10 rounded-full bg-emerald-600 flex items-center justify-center shrink-0 text-white text-xs font-black">
                        {(p.full_name || "P").split(" ").map(n => n[0]).join("").slice(0,2).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-bold text-slate-900 text-sm">{p.full_name}</p>
                        <p className="text-xs text-slate-500">{p.email}</p>
                        {p.abha_id && <p className="text-xs text-slate-400 font-mono">ABHA: {p.abha_id}</p>}
                      </div>
                      <div className="text-right shrink-0">
                        <p className="text-xs text-slate-400">Last visit</p>
                        <p className="text-sm font-semibold text-slate-700">{fmtDate(p.last_visit)}</p>
                        <ChevronRight className="w-4 h-4 text-slate-400 ml-auto mt-1" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* HISTORY */}
          {tab === "history" && (
            <div className="space-y-4">
              {/* Past Admissions */}
              {(data?.past_admissions || []).length > 0 && (
                <div>
                  <h3 className="section-title mb-3 flex items-center gap-2">
                    <Bed className="w-4 h-4 text-slate-400" /> Past Admissions
                  </h3>
                  <div className="card divide-y divide-slate-100">
                    {filterSearch(data.past_admissions, ["patient_name","diagnosis"]).map(a => (
                      <div key={a.admission_id} className="p-4 hover:bg-slate-50 flex items-center gap-4 cursor-pointer"
                        onClick={() => setSelectedPatient({ id: a.patient_id, name: a.patient_name })}>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="font-bold text-slate-900 text-sm">{a.patient_name}</p>
                            <span className="badge badge-gray capitalize">{a.status}</span>
                          </div>
                          <p className="text-xs text-slate-500">{a.diagnosis}</p>
                        </div>
                        <p className="text-xs text-slate-400 shrink-0">{fmtDate(a.admission_time)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Past Appointments */}
              {(data?.past_appointments || []).length > 0 && (
                <div>
                  <h3 className="section-title mb-3 flex items-center gap-2">
                    <ClipboardList className="w-4 h-4 text-slate-400" /> Past OPD Appointments
                  </h3>
                  <div className="card divide-y divide-slate-100">
                    {filterSearch(data.past_appointments, ["patient_name","reason_for_visit"]).map(a => (
                      <div key={a.appointment_id} className="p-4 hover:bg-slate-50 flex items-center gap-4 cursor-pointer"
                        onClick={() => setSelectedPatient({ id: a.patient_id, name: a.patient_name })}>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="font-bold text-slate-900 text-sm">{a.patient_name}</p>
                            <span className="badge badge-green">completed</span>
                          </div>
                          <p className="text-xs text-slate-500">{a.reason_for_visit}</p>
                          {a.notes && <p className="text-xs text-slate-400 italic truncate">{a.notes}</p>}
                        </div>
                        <p className="text-xs text-slate-400 shrink-0">{fmtDate(a.scheduled_time)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {(data?.past_admissions || []).length === 0 && (data?.past_appointments || []).length === 0 && (
                <EmptyState icon={ClipboardList} label="No history yet" sub="Completed cases will appear here" />
              )}
            </div>
          )}
        </div>
      )}

      {/* Patient Detail Drawer */}
      {selectedPatient && (
        <PatientDetailDrawer
          patientId={selectedPatient.id}
          patientName={selectedPatient.name}
          onClose={() => setSelectedPatient(null)}
        />
      )}
    </div>
  );
}

function EmptyState({ icon: Icon, label, sub }) {
  return (
    <div className="card p-12 text-center">
      <Icon className="w-10 h-10 text-slate-300 mx-auto mb-3" />
      <p className="text-slate-500 font-semibold">{label}</p>
      <p className="text-slate-400 text-sm mt-1">{sub}</p>
    </div>
  );
}
