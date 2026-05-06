import { useState } from "react";
import { FileText, Download, Shield, CheckCircle2, AlertCircle, ChevronDown, ChevronRight, Layers } from "lucide-react";
import toast from "react-hot-toast";
import { fhirAPI, consentAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";
import Spinner from "../../components/ui/Spinner";
import PatientSearchBar from "../../components/ui/PatientSearchBar";

function ResourceBadge({ type }) {
  const colors = {
    Patient:              "bg-brand-100 text-brand-700",
    Condition:            "bg-red-100 text-red-700",
    MedicationStatement:  "bg-blue-100 text-blue-700",
    DocumentReference:    "bg-purple-100 text-purple-700",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[type] || "bg-surface-100 text-surface-600"}`}>
      {type}
    </span>
  );
}

function BundleEntry({ entry, index }) {
  const [open, setOpen] = useState(false);
  const type = entry.resource?.resourceType || "Unknown";
  return (
    <div className="border border-surface-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-4 py-3 bg-surface-50 hover:bg-surface-100 transition-colors text-left"
      >
        <span className="text-xs text-surface-400 font-mono w-5">{index + 1}</span>
        <ResourceBadge type={type} />
        <span className="text-xs text-surface-600 flex-1 truncate font-mono">{entry.fullUrl}</span>
        {open ? <ChevronDown className="w-4 h-4 text-surface-400" /> : <ChevronRight className="w-4 h-4 text-surface-400" />}
      </button>
      {open && (
        <pre className="px-4 py-3 text-xs text-surface-700 bg-white overflow-x-auto font-mono leading-relaxed">
          {JSON.stringify(entry.resource, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default function FHIRExchange() {
  const { user } = useAuthStore();
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [consentId, setConsentId]   = useState("");
  const [loading, setLoading]       = useState(false);
  const [verifying, setVerifying]   = useState(false);
  const [consent, setConsent]       = useState(null);
  const [bundle, setBundle]         = useState(null);
  const [summary, setSummary]       = useState("");

  const verifyConsent = async () => {
    if (!selectedPatient) return;
    setVerifying(true);
    try {
      const { data } = await consentAPI.active(selectedPatient.user_id);
      const active = data.find((c) => c.status === "approved" && c.doctor_id === user.user_id);
      if (active) {
        setConsent(active);
        setConsentId(active.consent_id);
        toast.success("Consent verified!");
      } else {
        toast.error("No active consent found for this patient.");
      }
    } catch {
      toast.error("Consent verification failed");
    } finally {
      setVerifying(false);
    }
  };

  const generateBundle = async () => {
    if (!selectedPatient || !consentId.trim()) return;
    setLoading(true);
    setBundle(null);
    setSummary("");
    try {
      const { data } = await fhirAPI.exchange({
        patient_id:      selectedPatient.user_id,
        doctor_id:       user.user_id,
        consent_id:      consentId.trim(),
        include_summary: true,
      });
      setBundle(data.fhir_bundle);
      setSummary(data.clinical_summary);
      toast.success(`FHIR bundle generated — ${data.resource_count} resources`);
    } catch (err) {
      const detail = err.response?.data?.detail;
      toast.error(typeof detail === "object" ? detail.reason : detail || "Exchange failed");
    } finally {
      setLoading(false);
    }
  };

  const downloadBundle = () => {
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `fhir-bundle-${selectedPatient?.user_id?.slice(0, 8)}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-title">FHIR Exchange</h1>
        <p className="text-sm text-surface-500 mt-1">Generate FHIR R4 bundles for interoperable health record sharing.</p>
      </div>

      {/* Setup */}
      <div className="card p-6">
        <h2 className="section-title mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-brand-600" />
          Patient & Consent
        </h2>
        <div className="space-y-4">
          <div>
            <label className="label">Find Patient</label>
            <PatientSearchBar
              selected={selectedPatient}
              onSelect={(patient) => {
                 setSelectedPatient(patient);
                 setConsent(null);
                 setBundle(null);
              }}
              onClear={() => {
                 setSelectedPatient(null);
                 setConsent(null);
                 setBundle(null);
              }}
              placeholder="Search by name, MRN (AIIMS-2026-00001), phone or ABHA…"
            />
            {selectedPatient && (
              <div className="mt-3 flex justify-start">
                <button onClick={verifyConsent} disabled={verifying} className="btn-secondary text-xs">
                  {verifying ? <Spinner size="sm" /> : "Verify Consent"}
                </button>
              </div>
            )}
          </div>

          {consent && (
            <div className="flex items-center gap-3 p-3 bg-emerald-50 border border-emerald-200 rounded-lg animate-slide-up">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-emerald-700">Consent verified</p>
                <p className="text-xs text-emerald-600">Scope: {consent.requested_scope} · Expires: {new Date(consent.valid_until).toLocaleString()}</p>
              </div>
            </div>
          )}

          {!consent && (
            <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
              <p className="text-xs text-amber-700">Verify consent before generating a FHIR bundle.</p>
            </div>
          )}

          <button
            onClick={generateBundle}
            disabled={loading || !consent}
            className="btn-primary w-full justify-center py-2.5"
          >
            {loading
              ? <><Spinner size="sm" /> Generating Bundle...</>
              : <><FileText className="w-4 h-4" /> Generate FHIR R4 Bundle</>}
          </button>
        </div>
      </div>

      {/* Clinical Summary */}
      {summary && (
        <div className="card p-6 animate-slide-up">
          <h2 className="section-title mb-3 flex items-center gap-2">
            <FileText className="w-5 h-5 text-purple-600" />
            AI Clinical Summary
          </h2>
          <div className="bg-surface-50 rounded-xl p-4 border border-surface-200">
            <pre className="text-sm text-surface-700 whitespace-pre-wrap font-sans leading-relaxed">{summary}</pre>
          </div>
        </div>
      )}

      {/* Bundle viewer */}
      {bundle && (
        <div className="card p-6 animate-slide-up">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title flex items-center gap-2">
              <Layers className="w-5 h-5 text-brand-600" />
              FHIR R4 Bundle
              <span className="badge badge-blue">{bundle.entry?.length || 0} resources</span>
            </h2>
            <button onClick={downloadBundle} className="btn-secondary text-xs">
              <Download className="w-4 h-4" />
              Download JSON
            </button>
          </div>

          {/* Bundle meta */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            {[
              { label: "Type",      value: bundle.type },
              { label: "Bundle ID", value: bundle.id?.slice(0, 12) + "…" },
              { label: "Timestamp", value: bundle.timestamp ? new Date(bundle.timestamp).toLocaleString() : "—" },
            ].map((m) => (
              <div key={m.label} className="bg-surface-50 rounded-lg p-3">
                <p className="text-xs text-surface-400">{m.label}</p>
                <p className="text-sm font-medium text-surface-800 font-mono truncate">{m.value}</p>
              </div>
            ))}
          </div>

          {/* Entries */}
          <div className="space-y-2">
            {bundle.entry?.map((entry, i) => (
              <BundleEntry key={i} entry={entry} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
