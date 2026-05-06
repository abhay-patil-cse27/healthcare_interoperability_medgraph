import { useState } from "react";
import { Upload, Pill, Heart, Thermometer, AlertTriangle, Activity, CheckCircle2, Clock } from "lucide-react";
import toast from "react-hot-toast";
import { memoryAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";
import Spinner from "../../components/ui/Spinner";
import EmptyState from "../../components/ui/EmptyState";

const SOURCES = [
  { value: "patient_input",  label: "Self Report" },
  { value: "lab_result",     label: "Lab Result" },
  { value: "prescription",   label: "Prescription" },
  { value: "discharge_note", label: "Discharge Note" },
];

function EntitySection({ icon: Icon, label, items, color, renderItem }) {
  if (!items?.length) return null;
  return (
    <div>
      <div className={`flex items-center gap-2 mb-2 text-xs font-semibold uppercase tracking-wider ${color}`}>
        <Icon className="w-3.5 h-3.5" />
        {label} ({items.length})
      </div>
      <div className="flex flex-wrap gap-2">
        {items.map((item, i) => (
          <span key={i} className="px-2.5 py-1 bg-surface-50 border border-surface-200 rounded-lg text-xs text-surface-700">
            {renderItem(item)}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function HealthRecords() {
  const { user } = useAuthStore();
  const [text, setText]         = useState("");
  const [source, setSource]     = useState("patient_input");
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState(null);
  const [history, setHistory]   = useState([]);
  const [histLoading, setHistLoading] = useState(false);

  const handleIngest = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const { data } = await memoryAPI.ingest({
        patient_id: user.user_id,
        text: text.trim(),
        source,
      });
      setResult(data);
      setText("");
      toast.success(`Ingested! ${data.graph_nodes_created} entities extracted.`);
      loadHistory();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Ingestion failed");
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    setHistLoading(true);
    try {
      const { data } = await memoryAPI.history(user.user_id);
      setHistory(data.history || []);
    } catch {
      // silent
    } finally {
      setHistLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="page-title">Health Records</h1>
        <p className="text-sm text-surface-500 mt-1">
          Submit your health information to build your personal knowledge graph.
        </p>
      </div>

      {/* Ingest form */}
      <div className="card p-6">
        <h2 className="section-title mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5 text-brand-600" />
          Add Health Information
        </h2>
        <form onSubmit={handleIngest} className="space-y-4">
          <div>
            <label className="label">Source Type</label>
            <div className="flex flex-wrap gap-2">
              {SOURCES.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => setSource(s.value)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                    source === s.value
                      ? "bg-brand-600 text-white border-brand-600"
                      : "bg-white text-surface-600 border-surface-200 hover:border-brand-300"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="label">Health Text</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={5}
              placeholder="Describe your health information in natural language...&#10;&#10;Example: I have Type 2 Diabetes (E11.9). Taking Metformin 500mg twice daily. Blood pressure 145/92 mmHg. Reports fatigue and frequent urination. Allergic to penicillin."
              className="input resize-none font-mono text-xs leading-relaxed"
              required
            />
            <p className="text-xs text-surface-400 mt-1">{text.length} characters</p>
          </div>

          <button type="submit" disabled={loading || !text.trim()} className="btn-primary">
            {loading ? <><Spinner size="sm" /> Processing...</> : <><Upload className="w-4 h-4" /> Ingest Health Data</>}
          </button>
        </form>
      </div>

      {/* Result */}
      {result && (
        <div className="card p-6 border-l-4 border-l-emerald-500 animate-slide-up">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <h3 className="font-semibold text-surface-900">Extraction Complete</h3>
            <span className="ml-auto text-xs text-surface-400">{result.processing_time_ms}ms</span>
          </div>

          <div className="grid grid-cols-3 gap-3 mb-5">
            {[
              { label: "Graph Nodes", value: result.graph_nodes_created, color: "text-brand-600" },
              { label: "Status",      value: result.status,              color: "text-emerald-600" },
              { label: "Vector ID",   value: result.vector_entry_id?.slice(0, 8) + "...", color: "text-purple-600" },
            ].map((m) => (
              <div key={m.label} className="bg-surface-50 rounded-lg p-3 text-center">
                <p className={`text-lg font-bold ${m.color}`}>{m.value}</p>
                <p className="text-xs text-surface-500">{m.label}</p>
              </div>
            ))}
          </div>

          <div className="space-y-3">
            <EntitySection icon={Heart}         label="Conditions"  color="text-red-600"     items={result.entities?.conditions}  renderItem={(c) => `${c.name}${c.icd10_code ? ` (${c.icd10_code})` : ""}`} />
            <EntitySection icon={Pill}          label="Medications" color="text-blue-600"    items={result.entities?.medications} renderItem={(m) => `${m.name} ${m.dosage || ""} ${m.frequency || ""}`.trim()} />
            <EntitySection icon={Thermometer}   label="Symptoms"    color="text-orange-600"  items={result.entities?.symptoms}    renderItem={(s) => `${s.name} (${s.severity || "?"})`} />
            <EntitySection icon={Activity}      label="Vitals"      color="text-teal-600"    items={result.entities?.vitals}      renderItem={(v) => `${v.type}: ${v.value} ${v.unit || ""}`} />
            <EntitySection icon={AlertTriangle} label="Allergies"   color="text-amber-600"   items={result.entities?.allergies}   renderItem={(a) => `${a.substance} → ${a.reaction || "reaction"}`} />
          </div>
        </div>
      )}

      {/* History */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title flex items-center gap-2">
            <Clock className="w-5 h-5 text-surface-400" />
            Ingestion History
          </h2>
          <button onClick={loadHistory} className="btn-ghost text-xs">
            {histLoading ? <Spinner size="sm" /> : "Refresh"}
          </button>
        </div>

        {history.length === 0 ? (
          <EmptyState icon={Clock} title="No history yet" description="Your ingestion events will appear here." />
        ) : (
          <div className="space-y-2">
            {history.map((h, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-surface-50 border border-surface-100">
                <div className="w-2 h-2 rounded-full bg-emerald-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-surface-700 truncate">{h.action || "INGEST"}</p>
                  <p className="text-xs text-surface-400">{new Date(h.timestamp).toLocaleString()}</p>
                </div>
                <span className="badge badge-gray">{h.metadata?.source || "—"}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
