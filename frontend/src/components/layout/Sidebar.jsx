import { NavLink, useNavigate } from "react-router-dom";
import {
  Activity, MessageSquare, Shield, FileText, LogOut,
  User, Stethoscope, ChevronRight, Building2, Package,
  Bed, BarChart3, Scale, ClipboardList, Users, HeartPulse,
  Banknote, BadgeAlert, BriefcaseMedical, Upload, Eye,
} from "lucide-react";
import useAuthStore from "../../store/authStore";

// ── Nav definitions ────────────────────────────────────────────────────────
const patientNav = [
  { to: "/patient",            icon: Activity,         label: "Health Records" },
  { to: "/patient/documents",  icon: Upload,           label: "Lab Reports" },
  { to: "/patient/chat",       icon: MessageSquare,    label: "Ask My Records" },
  { to: "/patient/consents",   icon: Shield,           label: "Consent Manager" },
];

const doctorNav = [
  { to: "/doctor",            icon: Stethoscope,      label: "Patient Lookup" },
  { to: "/doctor/screening",  icon: Eye,              label: "AI Screenings" },
  { to: "/doctor/chat",       icon: MessageSquare,    label: "Clinical Query" },
  { to: "/doctor/consents",   icon: Shield,           label: "Consent Requests" },
  { to: "/doctor/fhir",       icon: FileText,         label: "FHIR Exchange" },
  { to: "/doctor/mlc",        icon: Scale,            label: "MLC Records" },
];

const adminNav = [
  { to: "/admin",            icon: BarChart3,        label: "System Overview" },
];

const hospitalNav = [
  { to: "/hospital",         icon: Building2,        label: "Hospital Ops" },
];

const nurseNav = [
  { to: "/nurse",            icon: Bed,              label: "Nurse Station" },
];

const pharmacistNav = [
  { to: "/pharmacist",       icon: Package,          label: "Pharmacy Queue" },
];

const opdNav = [
  { to: "/opd",              icon: ClipboardList,    label: "OPD Queue" },
];

const ipdNav = [
  { to: "/ipd",              icon: BriefcaseMedical, label: "IPD Admissions" },
];

const financeNav = [
  { to: "/finance",          icon: Banknote,         label: "Insurance Claims" },
];

const schemeNav = [
  { to: "/scheme",           icon: BadgeAlert,       label: "Scheme Eligibility" },
];

const mlcNav = [
  { to: "/mlc",              icon: Scale,            label: "MLC Interface" },
];

const hitlNav = [
  { to: "/hitl",             icon: Eye,              label: "Validation Queue" },
];

const ROLE_LABELS = {
  super_admin:      "Super Admin",
  govt_admin:       "Govt Admin",
  hospital_admin:   "Hospital Admin",
  doctor:           "Doctor",
  surgeon:          "Surgeon",
  nurse:            "Nurse",
  ward_incharge:    "Ward Incharge",
  pharmacist:       "Pharmacist",
  opd_staff:        "OPD Staff",
  ipd_staff:        "IPD Staff",
  receptionist:     "Receptionist",
  insurance_officer:"Insurance Officer",
  scheme_officer:   "Scheme Officer",
  police_interface: "Police Interface",
  hitl_validator:   "HITL Validator",
  patient:          "Patient",
};

export default function Sidebar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const getNav = () => {
    switch (user?.role) {
      case "super_admin":
      case "govt_admin":       return adminNav;
      case "hospital_admin":   return hospitalNav;
      case "doctor":
      case "surgeon":          return doctorNav;
      case "nurse":
      case "ward_incharge":    return nurseNav;
      case "pharmacist":       return pharmacistNav;
      case "opd_staff":
      case "receptionist":     return opdNav;
      case "ipd_staff":        return ipdNav;
      case "insurance_officer":return financeNav;
      case "scheme_officer":   return schemeNav;
      case "police_interface": return mlcNav;
      case "hitl_validator":   return hitlNav;
      default:                 return patientNav;
    }
  };

  const nav = getNav();
  const initials = (user?.full_name || "U").split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <aside className="w-64 min-h-screen bg-canvas border-r border-ash flex flex-col shrink-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-ash">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl gradient-forest flex items-center justify-center shadow-subtle">
            <HeartPulse className="w-5 h-5 text-lime" />
          </div>
          <div>
            <p className="text-body-sm font-bold text-ink tracking-tight">MedGraph</p>
            <p className="text-caption text-muted font-semibold uppercase tracking-widest">AI Platform</p>
          </div>
        </div>
      </div>

      {/* User Card */}
      <div className="px-4 py-3 mx-3 mt-5 rounded-2xl bg-ash/50 border border-ash">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full gradient-forest flex items-center justify-center shrink-0 text-lime text-caption font-bold">
            {initials}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-caption font-bold text-ink truncate">{user?.full_name || "User"}</p>
            <p className="text-caption text-forest font-semibold truncate">
              {ROLE_LABELS[user?.role] || user?.role}
            </p>
          </div>
          <span className="w-2 h-2 rounded-full bg-lime animate-pulse-slow shrink-0" />
        </div>
      </div>

      {/* Nav Links */}
      <nav className="flex-1 px-3 mt-6 space-y-1">
        <p className="px-3 mb-3 text-caption font-bold text-muted uppercase tracking-widest">
          Navigation
        </p>
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to.split("/").length === 2}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-body-sm font-semibold transition-all duration-200 ${
                isActive
                  ? "bg-forest text-lime shadow-subtle"
                  : "text-slate-text hover:text-ink hover:bg-ash/60"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? "text-lime" : "text-muted"}`} />
                <span className="flex-1 truncate">{label}</span>
                {isActive && <ChevronRight className="w-3 h-3 opacity-70" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom actions */}
      <div className="px-3 pb-5 mt-auto border-t border-ash pt-4 space-y-1">
        <NavLink
          to="/profile"
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-xl text-body-sm font-semibold transition-all duration-200 ${
              isActive
                ? "bg-forest text-lime"
                : "text-slate-text hover:text-ink hover:bg-ash/60"
            }`
          }
        >
          {({ isActive }) => (
            <>
              <User className={`w-4 h-4 shrink-0 ${isActive ? "text-lime" : "text-muted"}`} />
              <span className="flex-1">My Profile</span>
              {isActive && <ChevronRight className="w-3 h-3 opacity-70" />}
            </>
          )}
        </NavLink>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-body-sm font-semibold text-muted hover:text-alert hover:bg-alert/5 transition-all duration-200"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
