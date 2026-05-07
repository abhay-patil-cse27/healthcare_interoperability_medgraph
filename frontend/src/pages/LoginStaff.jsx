import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  Activity, Eye, EyeOff, AlertCircle, ArrowLeft,
  Stethoscope, Building2, Shield, Users, ChevronDown, ChevronUp,
} from "lucide-react";
import toast from "react-hot-toast";
import useAuthStore from "../store/authStore";
import Spinner from "../components/ui/Spinner";
import Globe from "../components/ui/Globe";

const STAFF_ROLE_GROUPS = [
  {
    label: "Government",
    color: "bg-purple-50 border-purple-100 text-purple-700",
    dot: "bg-purple-500",
    roles: [
      { role: "super_admin",   label: "Super Admin",    desc: "Full system control" },
      { role: "govt_admin",    label: "Govt Admin",     desc: "MoHFW oversight" },
    ],
  },
  {
    label: "Hospital",
    color: "bg-blue-50 border-blue-100 text-blue-700",
    dot: "bg-blue-500",
    roles: [
      { role: "hospital_admin", label: "Hospital Admin", desc: "Staff & dept management" },
    ],
  },
  {
    label: "Clinical",
    color: "bg-emerald-50 border-emerald-100 text-emerald-700",
    dot: "bg-emerald-500",
    roles: [
      { role: "doctor",       label: "Doctor",        desc: "OPD / IPD physician" },
      { role: "surgeon",      label: "Surgeon",       desc: "OT & surgical care" },
      { role: "nurse",        label: "Nurse",         desc: "Ward bedside care" },
      { role: "ward_incharge",label: "Ward Incharge", desc: "Shift supervisor" },
    ],
  },
  {
    label: "Operations",
    color: "bg-amber-50 border-amber-100 text-amber-700",
    dot: "bg-amber-500",
    roles: [
      { role: "pharmacist",   label: "Pharmacist",     desc: "Prescriptions & dispensing" },
      { role: "opd_staff",    label: "OPD Staff",      desc: "Appointments & queues" },
      { role: "ipd_staff",    label: "IPD Staff",      desc: "Admissions & beds" },
    ],
  },
  {
    label: "Finance & Legal",
    color: "bg-red-50 border-red-100 text-red-700",
    dot: "bg-red-500",
    roles: [
      { role: "insurance_officer", label: "Insurance Officer", desc: "Claims & TPA" },
      { role: "scheme_officer",    label: "Scheme Officer",    desc: "PM-JAY / MPJAY" },
      { role: "police_interface",  label: "Police Interface",  desc: "MLC records (read-only)" },
    ],
  },
  {
    label: "AI Oversight",
    color: "bg-indigo-50 border-indigo-100 text-indigo-700",
    dot: "bg-indigo-500",
    roles: [
      { role: "hitl_validator", label: "HITL Validator", desc: "AI screening review" },
    ],
  },
];

export default function LoginStaff() {
  const [email, setEmail]         = useState("");
  const [password, setPassword]   = useState("");
  const [showPw, setShowPw]       = useState(false);
  const [showRoles, setShowRoles] = useState(false);
  const { login, loading, error, clearError } = useAuthStore();
  const navigate  = useNavigate();
  const location  = useLocation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    try {
      const user = await login(email, password);
      if (user.role === "patient") {
        toast.error("Patients should use the Patient Login portal.");
        useAuthStore.getState().logout();
        return;
      }
      toast.success(`Welcome, ${user.full_name.split(" ")[0]}!`);
      const from = location.state?.from?.pathname;
      navigate(from || "/", { replace: true });
    } catch (err) {
      toast.error(err.message || "Login failed");
    }
  };

  return (
    <div className="min-h-screen bg-canvas flex flex-col lg:flex-row relative">
      {/* Back to Home */}
      <div className="absolute top-6 left-6 z-50">
        <Link to="/landing" className="flex items-center gap-2 text-sm font-bold text-forest bg-white/80 backdrop-blur-md px-4 py-2 rounded-full border border-forest/10 hover:bg-forest hover:text-lime transition-all shadow-subtle">
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
      </div>

      {/* Left Form Column */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-6 py-12 lg:px-16 animate-fade-in relative z-10">
        <div className="max-w-md w-full mx-auto">
          {/* Logo */}
          <Link to="/landing" className="inline-flex items-center gap-3 mb-10 group">
            <div className="w-10 h-10 rounded-xl bg-forest text-lime flex items-center justify-center group-hover:bg-lime group-hover:text-forest transition-colors shadow-subtle">
              <Activity className="w-6 h-6" />
            </div>
            <span className="text-xl font-black text-ink tracking-tight">MedGraph</span>
          </Link>

          <h2 className="text-[32px] font-black text-forest mb-2 leading-tight uppercase tracking-tighter">Staff Portal</h2>
          <p className="text-slate-text font-medium mb-8">Sign in with your hospital credentials.</p>

          {error && (
            <div className="flex items-center gap-2 p-4 mb-6 bg-alert/10 border border-alert/20 rounded-xl text-alert text-sm font-bold">
              <AlertCircle className="w-5 h-5 shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@hospital.gov.in"
                required
                autoComplete="email"
                className="input py-3.5 text-base"
              />
            </div>

            <div>
              <label className="label">Password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  autoComplete="current-password"
                  className="input py-3.5 text-base pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-muted hover:text-forest transition-colors"
                >
                  {showPw ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center py-4 text-base mt-2"
            >
              {loading ? <><Spinner size="sm" /> Signing in...</> : "Sign in to Staff Portal"}
            </button>
          </form>

          <p className="text-center text-sm text-slate-text mt-8 font-medium">
            Are you a patient?{" "}
            <Link to="/login/patient" className="text-forest hover:text-lime font-black transition-colors underline decoration-2 underline-offset-4">
              Patient Login →
            </Link>
          </p>

          {/* Role reference */}
          <div className="mt-6">
            <button
              onClick={() => setShowRoles(!showRoles)}
              className="flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-slate-600 transition-colors mx-auto"
            >
              {showRoles ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              {showRoles ? "Hide" : "View"} supported roles
            </button>
            {showRoles && (
              <div className="mt-4 space-y-3 max-h-64 overflow-y-auto pr-2">
                {STAFF_ROLE_GROUPS.map(g => (
                  <div key={g.label}>
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">{g.label}</p>
                    <div className="space-y-1">
                      {g.roles.map(r => (
                        <div key={r.role} className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs ${g.color}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${g.dot}`} />
                          <span className="font-bold">{r.label}</span>
                          <span className="text-[10px] opacity-70 ml-auto">{r.desc}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Visual Column */}
      <div className="hidden lg:flex w-1/2 bg-forest relative overflow-hidden items-center justify-center p-12">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(159,232,112,0.1)_0%,transparent_70%)] pointer-events-none" />
        
        <div className="relative w-full max-w-lg aspect-square">
          <div className="absolute -top-12 -left-12 z-10 max-w-[200px]">
            <h3 className="text-3xl font-black text-lime leading-tight uppercase tracking-tighter">Secure<br/>Staff Access</h3>
          </div>
          
          <Globe className="w-full h-full drop-shadow-2xl opacity-90" />
          
          <div className="absolute -bottom-8 -right-8 z-10 bg-white p-6 rounded-card shadow-card-hover max-w-[250px] animate-slide-up" style={{ animationDelay: '0.2s' }}>
             <p className="text-xs font-black text-forest uppercase tracking-widest mb-1">Access</p>
             <p className="text-sm font-medium text-slate-text leading-relaxed">16-role RBAC with JWT-embedded permissions.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
