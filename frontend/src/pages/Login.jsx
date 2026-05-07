import { Link } from "react-router-dom";
import {
  Activity, HeartPulse, Building2, ArrowRight, ArrowLeft,
} from "lucide-react";

/**
 * Login Chooser — directs users to the appropriate login portal.
 * Patients → /login/patient
 * Staff    → /login/staff
 */
export default function Login() {
  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center p-6 relative">
      {/* Back to Home */}
      <div className="absolute top-6 left-6 z-50">
        <Link to="/landing" className="flex items-center gap-2 text-sm font-bold text-forest bg-white/80 backdrop-blur-md px-4 py-2 rounded-full border border-forest/10 hover:bg-forest hover:text-lime transition-all shadow-subtle">
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
      </div>

      <div className="max-w-2xl w-full animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-10">
          <Link to="/landing" className="inline-flex items-center gap-3 group">
            <div className="w-12 h-12 rounded-xl bg-forest text-lime flex items-center justify-center group-hover:bg-lime group-hover:text-forest transition-colors shadow-subtle">
              <Activity className="w-7 h-7" />
            </div>
            <span className="text-2xl font-black text-ink tracking-tight">MedGraph</span>
          </Link>
        </div>

        <h1 className="text-3xl font-black text-forest text-center mb-3 uppercase tracking-tighter">Choose your portal</h1>
        <p className="text-center text-slate-text font-medium mb-10">Select how you'd like to sign in.</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Patient Card */}
          <Link
            to="/login/patient"
            className="group relative p-8 rounded-3xl border-2 border-emerald-100 bg-white hover:border-emerald-400 hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
          >
            <div className="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center mb-5 group-hover:bg-emerald-100 transition-colors">
              <HeartPulse className="w-7 h-7 text-emerald-600" />
            </div>
            <h3 className="text-xl font-black text-slate-900 mb-2">Patient Login</h3>
            <p className="text-sm text-slate-500 leading-relaxed mb-4">
              Access your health records, manage consents, upload documents, and chat with your care team.
            </p>
            <div className="flex items-center gap-2 text-sm font-bold text-emerald-600 group-hover:text-emerald-700">
              Sign in as Patient
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          {/* Staff Card */}
          <Link
            to="/login/staff"
            className="group relative p-8 rounded-3xl border-2 border-blue-100 bg-white hover:border-blue-400 hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
          >
            <div className="w-14 h-14 rounded-2xl bg-blue-50 flex items-center justify-center mb-5 group-hover:bg-blue-100 transition-colors">
              <Building2 className="w-7 h-7 text-blue-600" />
            </div>
            <h3 className="text-xl font-black text-slate-900 mb-2">Staff Login</h3>
            <p className="text-sm text-slate-500 leading-relaxed mb-4">
              Doctors, nurses, admins, pharmacists, and all hospital staff. Sign in with your institutional credentials.
            </p>
            <div className="flex items-center gap-2 text-sm font-bold text-blue-600 group-hover:text-blue-700">
              Sign in as Staff
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
        </div>

        <p className="text-center text-sm text-slate-400 mt-8 font-medium">
          New patient?{" "}
          <Link to="/register" className="text-forest hover:text-lime font-black transition-colors underline decoration-2 underline-offset-4">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
