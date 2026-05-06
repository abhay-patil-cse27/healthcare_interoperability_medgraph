import { useState, useEffect } from "react";
import {
  X, Bed, FileText, HeartPulse, Stethoscope,
  ClipboardList, Package, AlertTriangle, Thermometer,
  Wind, Heart, Droplet, ChevronDown, ChevronRight, TrendingUp
} from "lucide-react";
import { nurseAPI } from "../../services/api";
import toast from "react-hot-toast";
import Spinner from "../../components/ui/Spinner";
import { VitalsTrendChart, MultiLineChart } from "../../components/ui/MiniCharts";

function fmtDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function VitalBadge({ icon: Icon, label, value, alert }) {
  return (
    <div className={`p-3 rounded-xl border flex items-center gap-2 ${alert ? "bg-red-50 border-red-200" : "bg-slate-50 border-slate-200"}`}>
      <Icon className={`w-4 h-4 shrink-0 ${alert ? "text-red-500" : "text-slate-500"}`} />
      <div>
        <p className="text-[10px] text-slate-400 font-bold uppercase">{label}</p>
        <p className={`text-sm font-bold ${alert ? "text-red-700" : "text-slate-900"}`}>{value ?? "—"}</p>
      </div>
    </div>
  );
}

export default function PatientDetailDrawer({ patientId, patientName, onClose }) {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [section, setSection] = useState("vitals");

  useEffect(() => {
    fetchHistory();
  }, [patientId]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await nurseAPI.getPatientHistory(patientId);
      setHistory(res.data);
    } catch {
      toast.error("Failed to load patient history");
    } finally { setLoading(false); }
  };

  const latestVitals = history?.vitals?.[0];

  const SECTIONS = [
    { id: "vitals",      label: "Vitals",       icon: HeartPulse,    count: history?.vitals?.length },
    { id: "admissions",  label: "Admissions",   icon: Bed,           count: history?.admissions?.length },
    { id: "notes",       label: "IPD Notes",    icon: FileText,      count: history?.notes?.length },
    { id: "rx",          label: "Prescriptions",icon: Package,       count: history?.prescriptions?.length },
    { id: "appts",       label: "Appointments", icon: ClipboardList, count: history?.appointments?.length },
  ];

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={onClose} />

      {/* Drawer */}
      <div className="relative w-full max-w-xl bg-white shadow-2xl flex flex-col h-full animate-slide-up overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-black">
              {(patientName || "P").split(" ").map(n => n[0]).join("").slice(0,2).toUpperCase()}
            </div>
            <div>
              <h2 className="font-bold text-slate-900 text-lg">{patientName}</h2>
              <p className="text-xs text-slate-400 font-mono">{patientId?.slice(0,16)}…</p>
            </div>
          </div>
          <button onClick={onClose} className="btn-ghost p-2">
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Spinner />
              <p className="text-slate-400 text-sm mt-3">Loading full history...</p>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            {/* Latest vitals summary bar */}
            {latestVitals && (
              <div className="px-6 py-4 bg-slate-50 border-b border-slate-100">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Latest Vitals</p>
                <div className="grid grid-cols-4 gap-2">
                  <VitalBadge icon={Wind}        label="SpO2"  value={latestVitals.sp02 != null ? `${latestVitals.sp02}%` : latestVitals.spo2 != null ? `${latestVitals.spo2}%` : "—"} alert={latestVitals.sp02 < 94 || latestVitals.spo2 < 94} />
                  <VitalBadge icon={Heart}       label="BPM"   value={latestVitals.heart_rate} alert={latestVitals.heart_rate > 110 || latestVitals.heart_rate < 50} />
                  <VitalBadge icon={Thermometer} label="Temp"  value={latestVitals.temperature_c ? `${latestVitals.temperature_c}°C` : "—"} alert={latestVitals.temperature_c > 38.5} />
                  <VitalBadge icon={Droplet}     label="BP"    value={latestVitals.blood_pressure_sys ? `${latestVitals.blood_pressure_sys}/${latestVitals.blood_pressure_dia}` : "—"} alert={latestVitals.blood_pressure_sys > 140} />
                </div>
                {latestVitals.is_alert && (
                  <div className="mt-3 flex items-center gap-2 p-2 bg-red-50 border border-red-200 rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                    <p className="text-xs text-red-700 font-bold">Alert — abnormal vitals detected. Immediate review required.</p>
                  </div>
                )}
              </div>
            )}

            {/* Vitals Trend Charts */}
            {history?.vitals?.length > 1 && (
              <div className="px-6 py-4 border-b border-slate-100">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" /> Vitals Trend
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white border border-slate-100 rounded-xl p-3">
                    <p className="text-[10px] font-bold text-slate-500 mb-1">Heart Rate (BPM)</p>
                    <VitalsTrendChart
                      data={[...history.vitals].reverse().map(v => ({ time: new Date(v.recorded_at).toLocaleDateString("en-IN", {day:"numeric", month:"short"}), value: v.heart_rate }))}
                      dataKey="value" name="BPM" color="red" unit=" bpm" height={80} refMin={60} refMax={100}
                    />
                  </div>
                  <div className="bg-white border border-slate-100 rounded-xl p-3">
                    <p className="text-[10px] font-bold text-slate-500 mb-1">SpO2 (%)</p>
                    <VitalsTrendChart
                      data={[...history.vitals].reverse().map(v => ({ time: new Date(v.recorded_at).toLocaleDateString("en-IN", {day:"numeric", month:"short"}), value: v.sp02 ?? v.spo2 }))}
                      dataKey="value" name="SpO2" color="blue" unit="%" height={80} refMin={90} refMax={100}
                    />
                  </div>
                  <div className="bg-white border border-slate-100 rounded-xl p-3 col-span-2">
                    <p className="text-[10px] font-bold text-slate-500 mb-1">Blood Pressure (mmHg)</p>
                    <MultiLineChart
                      data={[...history.vitals].reverse().map(v => ({ time: new Date(v.recorded_at).toLocaleDateString("en-IN", {day:"numeric", month:"short"}), systolic: v.blood_pressure_sys, diastolic: v.blood_pressure_dia }))}
                      lines={[
                        { dataKey: "systolic", name: "Systolic", color: "red" },
                        { dataKey: "diastolic", name: "Diastolic", color: "blue" },
                      ]}
                      height={80}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Section tabs */}
            <div className="flex gap-0.5 px-6 pt-4 overflow-x-auto">
              {SECTIONS.map(s => (
                <button key={s.id} onClick={() => setSection(s.id)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold whitespace-nowrap transition-all ${
                    section === s.id ? "bg-blue-600 text-white" : "text-slate-500 hover:bg-slate-100"
                  }`}>
                  <s.icon className="w-3.5 h-3.5" />
                  {s.label}
                  {s.count > 0 && <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-black ${section === s.id ? "bg-blue-500 text-white" : "bg-slate-100 text-slate-600"}`}>{s.count}</span>}
                </button>
              ))}
            </div>

            {/* Section content */}
            <div className="p-6 space-y-3">
              {/* Vitals */}
              {section === "vitals" && (
                <>
                  {(history?.vitals || []).length === 0 ? <EmptySection label="No vitals recorded yet" /> : (
                    (history.vitals).map(v => (
                      <div key={v.vital_id} className={`p-4 rounded-xl border ${v.is_alert ? "bg-red-50 border-red-200" : "bg-white border-slate-200"}`}>
                        <div className="flex justify-between items-center mb-3">
                          <p className="text-xs font-bold text-slate-500">{fmtDate(v.recorded_at)}</p>
                          <div className="flex items-center gap-1.5">
                            {v.is_alert && <span className="badge badge-red">⚠ Alert</span>}
                            <span className="text-xs text-slate-400">by {v.recorder_name || v.recorded_by}</span>
                          </div>
                        </div>
                        <div className="grid grid-cols-4 gap-2">
                          <VitalBadge icon={Wind}        label="SpO2"  value={v.sp02 ?? v.spo2 ? `${v.sp02 ?? v.spo2}%` : "—"} alert={(v.sp02 ?? v.spo2) < 94} />
                          <VitalBadge icon={Heart}       label="BPM"   value={v.heart_rate} alert={v.heart_rate > 110 || v.heart_rate < 50} />
                          <VitalBadge icon={Thermometer} label="Temp"  value={v.temperature_c ? `${v.temperature_c}°C` : "—"} alert={v.temperature_c > 38.5} />
                          <VitalBadge icon={Droplet}     label="BP"    value={v.blood_pressure_sys ? `${v.blood_pressure_sys}/${v.blood_pressure_dia}` : "—"} alert={v.blood_pressure_sys > 140} />
                        </div>
                      </div>
                    ))
                  )}
                </>
              )}

              {/* Admissions */}
              {section === "admissions" && (
                <>
                  {(history?.admissions || []).length === 0 ? <EmptySection label="No admissions on record" /> : (
                    (history.admissions).map(a => (
                      <div key={a.admission_id} className="card p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className={`badge ${a.status === "admitted" ? "badge-blue" : "badge-green"}`}>{a.status}</span>
                            {a.is_mlc && <span className="badge badge-red">MLC</span>}
                            {a.scheme_applied && <span className="badge badge-blue">{a.scheme_applied}</span>}
                          </div>
                          <p className="text-xs text-slate-400">{fmtDate(a.admission_time)}</p>
                        </div>
                        <p className="text-sm font-bold text-slate-900">{a.diagnosis}</p>
                        <p className="text-xs text-slate-500 mt-1">{a.ward_id} · {a.bed_id}</p>
                      </div>
                    ))
                  )}
                </>
              )}

              {/* IPD Notes */}
              {section === "notes" && (
                <>
                  {(history?.notes || []).length === 0 ? <EmptySection label="No clinical notes yet" /> : (
                    (history.notes).map(n => (
                      <div key={n.note_id} className={`card p-4 ${n.is_flagged ? "border-red-200 bg-red-50" : ""}`}>
                        <div className="flex justify-between items-center mb-2">
                          <div className="flex items-center gap-2">
                            {n.is_flagged && <span className="badge badge-red">⚑ Flagged</span>}
                            <span className="text-xs font-bold text-slate-700 capitalize">{n.note_type?.replace(/_/g," ")}</span>
                          </div>
                          <p className="text-xs text-slate-400">{fmtDate(n.timestamp)}</p>
                        </div>
                        <p className="text-sm text-slate-700 leading-relaxed">{n.content}</p>
                        <p className="text-xs text-slate-400 mt-2">— {n.author_name || n.author_id} · {n.author_role}</p>
                      </div>
                    ))
                  )}
                </>
              )}

              {/* Prescriptions */}
              {section === "rx" && (
                <>
                  {(history?.prescriptions || []).length === 0 ? <EmptySection label="No prescriptions on record" /> : (
                    (history.prescriptions).map(rx => (
                      <div key={rx.prescription_id} className="card p-4">
                        <div className="flex justify-between items-center mb-3">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs text-slate-500">{rx.prescription_id}</span>
                            <span className={`badge ${rx.status === "dispensed" ? "badge-green" : "badge-yellow"}`}>{rx.status}</span>
                          </div>
                          <p className="text-xs text-slate-400">{fmtDate(rx.created_at)}</p>
                        </div>
                        {rx.diagnosis && <p className="text-xs text-slate-500 italic mb-2">{rx.diagnosis}</p>}
                        <ul className="space-y-1">
                          {(rx.medications || []).map((m, i) => (
                            <li key={i} className="flex items-center gap-2 text-sm">
                              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0" />
                              <span className="font-semibold text-slate-900">{m.name}</span>
                              <span className="text-slate-400">{m.dosage} · {m.frequency}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))
                  )}
                </>
              )}

              {/* Appointments */}
              {section === "appts" && (
                <>
                  {(history?.appointments || []).length === 0 ? <EmptySection label="No appointments on record" /> : (
                    (history.appointments).map(a => (
                      <div key={a.appointment_id} className="card p-4">
                        <div className="flex justify-between items-center mb-1">
                          <span className={`badge ${a.status === "completed" ? "badge-green" : a.status === "scheduled" ? "badge-yellow" : "badge-gray"}`}>{a.status}</span>
                          <p className="text-xs text-slate-400">{fmtDate(a.scheduled_time)}</p>
                        </div>
                        <p className="text-sm font-semibold text-slate-900 mt-2">{a.reason_for_visit}</p>
                        {a.notes && <p className="text-xs text-slate-500 mt-1 italic">{a.notes}</p>}
                        <p className="text-xs text-slate-400 mt-1">{a.department_name}</p>
                      </div>
                    ))
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function EmptySection({ label }) {
  return (
    <div className="py-8 text-center text-slate-400">
      <p className="font-medium">{label}</p>
    </div>
  );
}
