import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  Activity, Eye, EyeOff, AlertCircle, ArrowLeft,
  HeartPulse, FileText, Shield, Lock,
} from "lucide-react";
import toast from "react-hot-toast";
import useAuthStore from "../store/authStore";
import Spinner from "../components/ui/Spinner";

export default function LoginPatient() {
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw]     = useState(false);
  const { login, loading, error, clearError } = useAuthStore();
  const navigate  = useNavigate();
  const location  = useLocation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    try {
      const user = await login(email, password);
      if (user.role !== "patient") {
        toast.error("This portal is for patients only. Please use Staff Login.");
        useAuthStore.getState().logout();
        return;
      }
      toast.success(`Welcome, ${user.full_name.split(" ")[0]}!`);
      const from = location.state?.from?.pathname;
      navigate(from || "/patient", { replace: true });
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

          <h2 className="text-[32px] font-black text-forest mb-2 leading-tight uppercase tracking-tighter">Patient Portal</h2>
          <p className="text-slate-text font-medium mb-8">Sign in to access your health records.</p>

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
                placeholder="your.email@gmail.com"
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
              {loading ? <><Spinner size="sm" /> Signing in...</> : "Sign in to Patient Portal"}
            </button>
          </form>

          <div className="mt-8 space-y-3 text-center">
            <p className="text-sm text-slate-text font-medium">
              New patient?{" "}
              <Link to="/register" className="text-forest hover:text-lime font-black transition-colors underline decoration-2 underline-offset-4">
                Create an account
              </Link>
            </p>
            <p className="text-sm text-slate-text font-medium">
              Hospital staff?{" "}
              <Link to="/login/staff" className="text-forest hover:text-lime font-black transition-colors underline decoration-2 underline-offset-4">
                Staff Login →
              </Link>
            </p>
          </div>
        </div>
      </div>

      {/* Right Visual Column */}
      <div className="hidden lg:flex w-1/2 bg-gradient-to-br from-emerald-600 to-teal-700 relative overflow-hidden items-center justify-center p-12">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.08)_0%,transparent_70%)] pointer-events-none" />
        
        <div className="relative text-center text-white max-w-md">
          <div className="w-20 h-20 rounded-3xl bg-white/10 backdrop-blur-sm flex items-center justify-center mx-auto mb-8 border border-white/20">
            <HeartPulse className="w-10 h-10 text-white" />
          </div>
          <h3 className="text-3xl font-black mb-4 uppercase tracking-tight">Your Health,<br/>Your Control</h3>
          <p className="text-white/80 text-lg mb-10 leading-relaxed">Access your records, manage consents, and communicate with your care team securely.</p>
          
          <div className="grid grid-cols-1 gap-4 text-left">
            {[
              { icon: FileText, text: "View lab reports & prescriptions" },
              { icon: Shield, text: "Control who sees your data" },
              { icon: Lock, text: "ABHA-linked health records" },
            ].map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-xl px-4 py-3 border border-white/10">
                <Icon className="w-5 h-5 text-emerald-200 shrink-0" />
                <span className="text-sm font-medium text-white/90">{text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
