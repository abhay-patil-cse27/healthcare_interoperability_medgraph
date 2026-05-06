import { useState, useEffect } from "react";
import {
  Bed, Activity, Clipboard, AlertCircle,
  User, Thermometer, Heart, Droplet, Wind, RefreshCw
} from "lucide-react";
import toast from "react-hot-toast";
import { nurseAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";
import Spinner from "../../components/ui/Spinner";
import { ActivityBar } from "../../components/ui/MiniCharts";

export default function NurseStation() {
  const { user } = useAuthStore();
  const [vitalsHistory, setVitalsHistory] = useState([]);
  const [loading, setLoading]             = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [showVitalsModal, setShowVitalsModal] = useState(false);
  const [vitalsForm, setVitalsForm] = useState({
    patient_id: "", temperature_c: "", heart_rate: "",
    spo2: "", systolic_bp: "", diastolic_bp: "", notes: ""
  });
  const [submitting, setSubmitting] = useState(false);

  // Seeded patient reference list for nurse's ward
  const patients = [
    { id: "look-up-in-mongo", name: "Ramesh Yadav",   age: 47, bed: "IPD-401-A", condition: "Stable",              email: "patient.ramesh@gmail.com" },
    { id: "look-up-in-mongo", name: "Nisha Kulkarni", age: 38, bed: "IPD-402-B", condition: "Requires Monitoring", email: "patient.nisha@gmail.com" },
    { id: "look-up-in-mongo", name: "Sanjay Pawar",   age: 55, bed: "IPD-OT-03", condition: "Post-Op Recovery",    email: "patient.sanjay@gmail.com" },
  ];

  const handleOpenVitals = (p) => {
    setSelectedPatient(p);
    setVitalsForm({ ...vitalsForm, patient_id: p.id });
    setShowVitalsModal(true);
  };

  const handleLogVitals = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await nurseAPI.logVitals({
        patient_id:    vitalsForm.patient_id || "unknown",
        temperature_c: parseFloat(vitalsForm.temperature_c) || null,
        heart_rate:    parseInt(vitalsForm.heart_rate) || null,
        spo2:          parseFloat(vitalsForm.spo2) || null,
        systolic_bp:   parseInt(vitalsForm.systolic_bp) || null,
        diastolic_bp:  parseInt(vitalsForm.diastolic_bp) || null,
        notes:         vitalsForm.notes,
        recorded_at:   new Date().toISOString(),
      });
      toast.success(`Vitals saved for ${selectedPatient.name}`);
      setShowVitalsModal(false);
      setVitalsForm({ patient_id: "", temperature_c: "", heart_rate: "", spo2: "", systolic_bp: "", diastolic_bp: "", notes: "" });
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to log vitals");
    } finally {
      setSubmitting(false);
    }
  };

  const conditionBadge = (condition) => {
    if (condition.includes("Post-Op"))   return "badge-blue";
    if (condition.includes("Monitoring")) return "badge-yellow";
    return "badge-green";
  };

  const conditionBorder = (condition) => {
    if (condition.includes("Post-Op"))    return "border-t-blue-500";
    if (condition.includes("Monitoring")) return "border-t-amber-500";
    return "border-t-emerald-500";
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="page-title">Nurse Station</h1>
          <p className="text-slate-500 mt-1 text-sm">
            Ward IPD-General — {user?.full_name} · {new Date().toLocaleDateString("en-IN", { weekday:"long", day:"numeric", month:"short" })}
          </p>
        </div>
        <button onClick={() => toast("Shift handoff report generated", { icon: "📋" })} className="btn-secondary">
          <Clipboard className="w-4 h-4" /> Shift Handoff
        </button>
      </div>

      {/* Summary bar */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-4 border-l-4 border-l-emerald-500">
          <p className="text-2xl font-bold text-slate-900">{patients.filter(p => p.condition === "Stable").length}</p>
          <p className="text-sm text-slate-500 font-medium mt-1">Stable</p>
        </div>
        <div className="card p-4 border-l-4 border-l-amber-500">
          <p className="text-2xl font-bold text-slate-900">{patients.filter(p => p.condition.includes("Monitoring")).length}</p>
          <p className="text-sm text-slate-500 font-medium mt-1">Needs Monitoring</p>
        </div>
        <div className="card p-4 border-l-4 border-l-blue-500">
          <p className="text-2xl font-bold text-slate-900">{patients.filter(p => p.condition.includes("Post")).length}</p>
          <p className="text-sm text-slate-500 font-medium mt-1">Post-Op Recovery</p>
        </div>
      </div>

      {/* Vitals Activity — Last 7 days */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Vitals Logged (Last 7 Days)</p>
          <span className="text-xs text-slate-500">Ward IPD-General</span>
        </div>
        <ActivityBar
          data={[
            { name: "Mon", count: 8 },
            { name: "Tue", count: 12 },
            { name: "Wed", count: 6 },
            { name: "Thu", count: 14 },
            { name: "Fri", count: 10 },
            { name: "Sat", count: 7 },
            { name: "Sun", count: 4 },
          ]}
          color="blue"
          height={60}
        />
      </div>

      {/* Patient Grid */}
      <div>
        <h2 className="section-title mb-4">Assigned Patients — Ward IPD-General</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {patients.map(p => (
            <div key={p.name} className={`card p-5 border-t-4 ${conditionBorder(p.condition)}`}>
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center">
                    <User className="w-5 h-5 text-slate-500" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">{p.name}</h3>
                    <p className="text-xs text-slate-500">Bed {p.bed} · {p.age}y</p>
                  </div>
                </div>
                <span className={`badge ${conditionBadge(p.condition)}`}>{p.condition}</span>
              </div>

              <div className="grid grid-cols-2 gap-2 mb-4">
                <VitalChip icon={<Wind className="w-3.5 h-3.5 text-blue-500" />}    label="SpO2"  value="—" />
                <VitalChip icon={<Heart className="w-3.5 h-3.5 text-red-500" />}    label="BPM"   value="—" />
                <VitalChip icon={<Thermometer className="w-3.5 h-3.5 text-orange-500" />} label="Temp" value="—" />
                <VitalChip icon={<Droplet className="w-3.5 h-3.5 text-indigo-500" />} label="BP" value="—" />
              </div>

              <div className="flex gap-2">
                <button onClick={() => handleOpenVitals(p)} className="flex-1 btn-primary py-1.5 text-xs justify-center">
                  Log Vitals
                </button>
                <button onClick={() => toast("Clinical note for " + p.name, { icon: "📝" })} className="btn-secondary py-1.5 text-xs">
                  Add Note
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Ward Bot Monitor */}
      <div className="card p-5 bg-slate-900 text-white">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-4 h-4 text-blue-400" />
              <h2 className="font-bold text-sm">Ward Bot — Autonomous Monitor</h2>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-mono text-emerald-400 text-sm font-bold">ALL SYSTEMS NOMINAL</span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-slate-400 text-xs mb-1">IoT data stream</p>
            <p className="font-mono text-slate-300">Active · 3 devices</p>
          </div>
        </div>
      </div>

      {showVitalsModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="card w-full max-w-md p-6 animate-slide-up">
            <h2 className="text-lg font-bold text-slate-900 mb-1">Record Vitals</h2>
            <p className="text-sm text-slate-500 mb-5">Patient: <strong>{selectedPatient?.name}</strong> · Bed {selectedPatient?.bed}</p>
            <form onSubmit={handleLogVitals} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div><label className="label">SpO2 (%)</label><input type="number" step="0.1" className="input" placeholder="98" value={vitalsForm.spo2} onChange={e => setVitalsForm({...vitalsForm, spo2: e.target.value})} /></div>
                <div><label className="label">Heart Rate (BPM)</label><input type="number" className="input" placeholder="72" value={vitalsForm.heart_rate} onChange={e => setVitalsForm({...vitalsForm, heart_rate: e.target.value})} /></div>
                <div><label className="label">Temp (°C)</label><input type="number" step="0.1" className="input" placeholder="37.0" value={vitalsForm.temperature_c} onChange={e => setVitalsForm({...vitalsForm, temperature_c: e.target.value})} /></div>
                <div><label className="label">Systolic BP</label><input type="number" className="input" placeholder="120" value={vitalsForm.systolic_bp} onChange={e => setVitalsForm({...vitalsForm, systolic_bp: e.target.value})} /></div>
              </div>
              <div><label className="label">Notes</label><textarea className="input resize-none" rows={2} placeholder="Any observations..." value={vitalsForm.notes} onChange={e => setVitalsForm({...vitalsForm, notes: e.target.value})} /></div>
              <div className="flex gap-3 pt-1">
                <button type="button" onClick={() => setShowVitalsModal(false)} className="btn-secondary flex-1">Cancel</button>
                <button type="submit" disabled={submitting} className="btn-primary flex-1 justify-center">
                  {submitting ? <Spinner size="sm" /> : "Save Vitals"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function VitalChip({ icon, label, value }) {
  return (
    <div className="bg-slate-50 p-2.5 rounded-lg flex items-center gap-2">
      {icon}
      <div>
        <p className="text-[10px] text-slate-400 font-bold uppercase">{label}</p>
        <p className="text-sm font-bold text-slate-700">{value}</p>
      </div>
    </div>
  );
}
