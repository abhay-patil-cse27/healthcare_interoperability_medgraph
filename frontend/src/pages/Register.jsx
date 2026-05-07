import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Activity, AlertCircle, User, Stethoscope,
  Eye, EyeOff, Info, ArrowLeft
} from "lucide-react";
import toast from "react-hot-toast";
import useAuthStore from "../store/authStore";
import Spinner from "../components/ui/Spinner";
import Globe from "../components/ui/Globe";

// Per RBAC design: only patient can self-register.
// Doctors, nurses, etc. are invited by hospital_admin.
// This page explains the system clearly.

const STAFF_ROLES = [
  { value: "doctor",            label: "Doctor",              desc: "Licensed physician" },
  { value: "surgeon",           label: "Surgeon",             desc: "OT & surgical procedures" },
  { value: "nurse",             label: "Nurse",               desc: "Ward bedside care" },
  { value: "ward_incharge",     label: "Ward Incharge",       desc: "Senior nurse / shift lead" },
  { value: "pharmacist",        label: "Pharmacist",          desc: "Drug dispensing & checks" },
  { value: "hospital_admin",    label: "Hospital Admin",      desc: "Manage staff & departments" },
  { value: "opd_staff",         label: "OPD Staff",           desc: "Appointments & registration" },
  { value: "ipd_staff",         label: "IPD Staff",           desc: "Admissions & bed management" },
  { value: "insurance_officer", label: "Insurance Officer",   desc: "Claims & TPA management" },
  { value: "scheme_officer",    label: "Scheme Officer",      desc: "PM-JAY / MPJAY eligibility" },
];

export default function Register() {
  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    phone: "",
    role: "patient",
    specialization: "",
    license_number: "",
  });
  const [showPw, setShowPw] = useState(false);
  const { register, loading, error, clearError } = useAuthStore();
  const navigate = useNavigate();

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    try {
      await register(form);
      toast.success("Account created! Please sign in.");
      navigate("/login/patient");
    } catch (err) {
      toast.error(err.message || "Registration failed");
    }
  };

  return (
    <div className="min-h-screen bg-canvas flex flex-col lg:flex-row-reverse relative">
      {/* Back to Home Header */}
      <div className="absolute top-6 left-6 z-50">
        <Link to="/" className="flex items-center gap-2 text-sm font-bold text-forest bg-white/80 backdrop-blur-md px-4 py-2 rounded-full border border-forest/10 hover:bg-forest hover:text-lime transition-all shadow-subtle">
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
      </div>

      {/* Right Form Column (mirrored layout compared to Login) */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-6 py-12 lg:px-16 animate-fade-in relative z-10 overflow-y-auto">
        <div className="max-w-md w-full mx-auto">
          {/* Logo */}
          <Link to="/" className="inline-flex items-center gap-3 mb-10 group">
            <div className="w-10 h-10 rounded-xl bg-forest text-lime flex items-center justify-center group-hover:bg-lime group-hover:text-forest transition-colors shadow-subtle">
              <Activity className="w-6 h-6" />
            </div>
            <span className="text-xl font-black text-ink tracking-tight">MedGraph</span>
          </Link>

          <h2 className="text-[32px] font-black text-forest mb-2 leading-tight uppercase tracking-tighter">Create Account</h2>
          <p className="text-slate-text font-medium mb-8">Join the national healthcare network.</p>

          <div className="flex gap-4 p-4 bg-lime/10 border border-lime/20 rounded-2xl mb-8">
            <Info className="w-5 h-5 text-forest shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-black text-forest uppercase tracking-wider mb-1">Patient Portal</p>
              <p className="text-sm text-forest/80 leading-relaxed font-medium">
                Only patients can self-register. Staff accounts are provisioned via Admin invite.
              </p>
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 p-4 mb-6 bg-alert/10 border border-alert/20 rounded-xl text-alert text-sm font-bold">
              <AlertCircle className="w-5 h-5 shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label">Full Name</label>
              <input
                value={form.full_name}
                onChange={(e) => set("full_name", e.target.value)}
                placeholder="John Doe"
                required
                className="input py-3.5 text-base"
              />
            </div>

            <div>
              <label className="label">Email Address</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => set("email", e.target.value)}
                placeholder="john@example.com"
                required
                className="input py-3.5 text-base"
              />
            </div>

            <div>
              <label className="label">Phone Number</label>
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => set("phone", e.target.value)}
                placeholder="+91 98765 43210"
                className="input py-3.5 text-base"
              />
            </div>

            <div>
              <label className="label">Password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  value={form.password}
                  onChange={(e) => set("password", e.target.value)}
                  placeholder="Min 8 characters"
                  minLength={8}
                  required
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
              {loading ? <><Spinner size="sm" /> Creating Account...</> : "Create Patient Account"}
            </button>
          </form>

          <p className="text-center text-sm text-slate-text mt-8 font-medium">
            Already have an account?{" "}
            <Link to="/login/patient" className="text-forest hover:text-lime font-black transition-colors underline decoration-2 underline-offset-4">
              Sign in
            </Link>
          </p>
        </div>
      </div>

      {/* Left Visual Column */}
      <div className="hidden lg:flex w-1/2 bg-lime relative overflow-hidden items-center justify-center p-12">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(22,51,0,0.05)_0%,transparent_70%)] pointer-events-none" />
        
        <div className="relative w-full max-w-lg aspect-square">
          {/* Decorative text */}
          <div className="absolute -top-12 -right-12 z-10 max-w-[200px] text-right">
            <h3 className="text-3xl font-black text-forest leading-tight uppercase tracking-tighter">Your Health<br/>In One Place</h3>
          </div>
          
          <Globe className="w-full h-full drop-shadow-xl" />
          
          <div className="absolute -bottom-8 -left-8 z-10 bg-forest p-6 rounded-card shadow-card-hover max-w-[250px] animate-slide-up" style={{ animationDelay: '0.2s' }}>
             <p className="text-xs font-black text-lime uppercase tracking-widest mb-1">Privacy</p>
             <p className="text-sm font-medium text-white leading-relaxed">Full consent control over your clinical records.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
