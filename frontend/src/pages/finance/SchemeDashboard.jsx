import { useState, useEffect } from "react";
import {
  BadgeAlert, CheckCircle2, XCircle, Search,
  User, RefreshCw, FileSearch, IndianRupee
} from "lucide-react";
import { financeAPI } from "../../services/api";
import toast from "react-hot-toast";
import Spinner from "../../components/ui/Spinner";

function fmtDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export default function SchemeDashboard() {
  const [checks, setChecks]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState("");

  // Use seeded data from scheme_checks collection
  const staticChecks = [
    {
      check_id: "sc-001", patient_name: "Ramesh Yadav",
      scheme_name: "PM-JAY", identity_type: "ABHA", identity_value: "91-1234-5678-9012",
      is_eligible: true, coverage_cap: 500000, family_id: "PMJAY-FAM-MH-098234",
      timestamp: new Date(Date.now() - 3 * 86400000),
    },
    {
      check_id: "sc-002", patient_name: "Sanjay Pawar",
      scheme_name: "PM-JAY", identity_type: "Aadhaar", identity_value: "XXXX-XXXX-4821",
      is_eligible: true, coverage_cap: 500000, family_id: "PMJAY-FAM-MH-112984",
      timestamp: new Date(Date.now() - 4 * 86400000),
    },
    {
      check_id: "sc-003", patient_name: "Nisha Kulkarni",
      scheme_name: "MPJAY", identity_type: "Ration Card", identity_value: "MH/2021/RC/094821",
      is_eligible: false, coverage_cap: null, family_id: null,
      notes: "Above income threshold. Referred to private insurance.",
      timestamp: new Date(Date.now() - 5 * 86400000),
    },
  ];

  const filtered = staticChecks.filter(c =>
    !search || c.patient_name.toLowerCase().includes(search.toLowerCase()) ||
    c.scheme_name.toLowerCase().includes(search.toLowerCase())
  );

  const eligibleCount = staticChecks.filter(c => c.is_eligible).length;
  const totalCoverage = staticChecks.filter(c => c.is_eligible)
    .reduce((sum, c) => sum + (c.coverage_cap || 0), 0);

  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [verifyForm, setVerifyForm] = useState({ patient_name: "", scheme_name: "PM-JAY", identity_type: "ABHA", identity_value: "" });
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);

  const handleVerify = async (e) => {
    e.preventDefault();
    setVerifying(true);
    try {
      const res = await financeAPI.checkEligibility({
        patient_id: "manual-check",
        ...verifyForm,
      });
      setVerifyResult(res.data);
      toast.success("Eligibility check complete");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Eligibility check failed");
    } finally { setVerifying(false); }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="page-title">Scheme Eligibility</h1>
          <p className="text-slate-500 text-sm mt-1">PM-JAY / MPJAY beneficiary verification and enrollment</p>
        </div>
        <button onClick={() => setShowVerifyModal(true)} className="btn-primary">
          <FileSearch className="w-4 h-4" /> Verify Eligibility
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-4 border-l-4 border-l-emerald-500">
          <p className="text-2xl font-bold text-slate-900">{eligibleCount}</p>
          <p className="text-sm text-slate-500 font-medium mt-1">Eligible Beneficiaries</p>
        </div>
        <div className="card p-4 border-l-4 border-l-red-500">
          <p className="text-2xl font-bold text-slate-900">{staticChecks.length - eligibleCount}</p>
          <p className="text-sm text-slate-500 font-medium mt-1">Ineligible</p>
        </div>
        <div className="card p-4 border-l-4 border-l-blue-500">
          <p className="text-2xl font-bold text-slate-900">₹{(totalCoverage / 100000).toFixed(1)}L</p>
          <p className="text-sm text-slate-500 font-medium mt-1">Total Coverage Cap</p>
        </div>
      </div>

      {/* Search */}
      <div className="relative w-64">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Patient or scheme..." className="input pl-9" />
      </div>

      {/* Checks List */}
      <div className="space-y-3">
        {filtered.map(c => (
          <div key={c.check_id} className={`card p-5 border-l-4 ${c.is_eligible ? "border-l-emerald-500" : "border-l-red-500"}`}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${c.is_eligible ? "bg-emerald-50" : "bg-red-50"}`}>
                  {c.is_eligible
                    ? <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    : <XCircle className="w-5 h-5 text-red-600" />
                  }
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-bold text-slate-900">{c.patient_name}</h3>
                    <span className={`badge ${c.is_eligible ? "badge-green" : "badge-red"}`}>
                      {c.is_eligible ? "Eligible" : "Ineligible"}
                    </span>
                    <span className="badge badge-blue">{c.scheme_name}</span>
                  </div>
                  <p className="text-sm text-slate-500 mt-1">
                    {c.identity_type}: <span className="font-mono font-semibold">{c.identity_value}</span>
                  </p>
                  {c.family_id && <p className="text-xs text-slate-400 mt-0.5">Family ID: {c.family_id}</p>}
                  {c.notes && <p className="text-xs text-amber-700 mt-1 bg-amber-50 px-2 py-1 rounded-lg">{c.notes}</p>}
                </div>
              </div>
              <div className="text-right shrink-0">
                {c.coverage_cap && (
                  <p className="text-sm font-bold text-emerald-700">
                    ₹{c.coverage_cap.toLocaleString("en-IN")}
                  </p>
                )}
                <p className="text-xs text-slate-400 mt-1">{fmtDate(c.timestamp)}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Verify Modal */}
      {showVerifyModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="card w-full max-w-md p-6 animate-slide-up">
            <h2 className="text-lg font-bold text-slate-900 mb-5">Check Scheme Eligibility</h2>
            {verifyResult ? (
              <div className={`p-4 rounded-xl border ${verifyResult.is_eligible ? "bg-emerald-50 border-emerald-100" : "bg-red-50 border-red-100"} mb-4`}>
                <div className="flex items-center gap-2 mb-2">
                  {verifyResult.is_eligible ? <CheckCircle2 className="w-5 h-5 text-emerald-600" /> : <XCircle className="w-5 h-5 text-red-600" />}
                  <p className="font-bold">{verifyResult.is_eligible ? "Eligible" : "Not Eligible"}</p>
                </div>
                {verifyResult.coverage_cap && <p className="text-sm">Coverage Cap: ₹{verifyResult.coverage_cap.toLocaleString("en-IN")}</p>}
              </div>
            ) : (
              <form onSubmit={handleVerify} className="space-y-3">
                <div><label className="label">Patient Name</label><input required className="input" value={verifyForm.patient_name} onChange={e => setVerifyForm({...verifyForm, patient_name: e.target.value})} /></div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label">Scheme</label>
                    <select className="input" value={verifyForm.scheme_name} onChange={e => setVerifyForm({...verifyForm, scheme_name: e.target.value})}>
                      <option>PM-JAY</option><option>MPJAY</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">ID Type</label>
                    <select className="input" value={verifyForm.identity_type} onChange={e => setVerifyForm({...verifyForm, identity_type: e.target.value})}>
                      <option>ABHA</option><option>Aadhaar</option><option>Ration Card</option>
                    </select>
                  </div>
                </div>
                <div><label className="label">Identity Value</label><input required className="input" placeholder="ABHA number / Aadhaar..." value={verifyForm.identity_value} onChange={e => setVerifyForm({...verifyForm, identity_value: e.target.value})} /></div>
                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setShowVerifyModal(false)} className="btn-secondary flex-1">Cancel</button>
                  <button type="submit" disabled={verifying} className="btn-primary flex-1 justify-center">
                    {verifying ? <Spinner size="sm" /> : "Verify"}
                  </button>
                </div>
              </form>
            )}
            {verifyResult && (
              <button onClick={() => { setShowVerifyModal(false); setVerifyResult(null); }} className="btn-secondary w-full mt-2">Close</button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
