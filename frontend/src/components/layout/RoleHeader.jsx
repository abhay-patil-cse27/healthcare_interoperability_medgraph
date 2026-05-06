/**
 * RoleHeader — contextual top header bar for each of the 16 roles.
 *
 * Design philosophy:
 *  - Each role has its own accent color and theme so a doctor's UI
 *    looks clinically distinct from an insurance officer's or a nurse's.
 *  - The bar shows quick-context chips (e.g. hospital name, shift, pending count)
 *    relevant to that specific role — purely cosmetic / static context.
 *  - NotificationBell is embedded for roles that get alerts.
 *  - Patient role gets a completely different minimal look with their MRN.
 */
import { useEffect, useState } from "react";
import {
  Stethoscope, Bed, Package, ClipboardList, Building2,
  Scale, Shield, BadgeAlert, BarChart3, BriefcaseMedical,
  HeartPulse, Users, Bell, Zap, Moon, Sun, Activity,
  CalendarCheck, AlertTriangle, FileSearch, IndianRupee,
} from "lucide-react";
import NotificationBell from "../ui/NotificationBell";
import useAuthStore from "../../store/authStore";
import { nurseAPI, opdAPI, notifAPI } from "../../services/api";

// ── Role theme map ─────────────────────────────────────────────────────────
const ROLE_THEME = {
  super_admin:       { accent: "from-forest to-emerald", badge: "bg-lime/20 text-lime border-lime/30" },
  govt_admin:        { accent: "from-forest to-emerald", badge: "bg-lime/20 text-lime border-lime/30" },
  hospital_admin:    { accent: "from-forest to-[#054d28]", badge: "bg-lime/20 text-lime border-lime/30" },
  doctor:            { accent: "from-forest to-emerald", badge: "bg-lime/20 text-lime border-lime/30" },
  surgeon:           { accent: "from-forest to-emerald", badge: "bg-lime/20 text-lime border-lime/30" },
  nurse:             { accent: "from-[#0b4c72] to-cyan", badge: "bg-white/20 text-white border-white/30" },
  ward_incharge:     { accent: "from-[#0b4c72] to-cyan", badge: "bg-white/20 text-white border-white/30" },
  pharmacist:        { accent: "from-emerald to-forest", badge: "bg-lime/20 text-lime border-lime/30" },
  opd_staff:         { accent: "from-[#0b4c72] to-cyan", badge: "bg-white/20 text-white border-white/30" },
  ipd_staff:         { accent: "from-forest to-emerald", badge: "bg-lime/20 text-lime border-lime/30" },
  receptionist:      { accent: "from-[#0b4c72] to-cyan", badge: "bg-white/20 text-white border-white/30" },
  insurance_officer: { accent: "from-forest to-emerald", badge: "bg-lime/20 text-lime border-lime/30" },
  scheme_officer:    { accent: "from-forest to-emerald", badge: "bg-lime/20 text-lime border-lime/30" },
  police_interface:  { accent: "from-slate-700 to-slate-900", badge: "bg-slate-500/20 text-slate-300 border-slate-500/30" },
  patient:           { accent: "from-canvas to-white",    badge: "bg-lime/10 text-forest border-lime/20" },
};

// ── Role-specific context chips (static + dynamic) ────────────────────────
function ContextChips({ role, user, stats }) {
  const badge = (ROLE_THEME[role] || ROLE_THEME.doctor).badge;

  const Chip = ({ icon: Icon, label, pulse }) => (
    <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-bold ${badge}`}>
      <Icon className={`w-3.5 h-3.5 shrink-0 ${pulse ? "animate-pulse" : ""}`} />
      {label}
    </span>
  );

  const hospitalName = "AIIMS New Delhi"; // derived from hospital_id in future

  switch (role) {
    case "super_admin":
    case "govt_admin":
      return (
        <>
          <Chip icon={Building2}   label="National Registry" />
          <Chip icon={BarChart3}   label="MoHFW System Admin" />
          <Chip icon={Activity}    label={`${stats?.hospitals ?? "—"} Hospitals`} />
        </>
      );
    case "hospital_admin":
      return (
        <>
          <Chip icon={Building2}   label={hospitalName} />
          <Chip icon={Users}       label={`${stats?.staff ?? "—"} Staff`} />
          <Chip icon={Activity}    label={`${stats?.departments ?? "—"} Departments`} />
        </>
      );
    case "doctor":
    case "surgeon":
      return (
        <>
          <Chip icon={Stethoscope} label={user?.specialization || (role === "surgeon" ? "General Surgery" : "Medicine")} />
          <Chip icon={Bed}         label={`${stats?.active ?? "—"} Active IPD`} />
          <Chip icon={CalendarCheck} label={`${stats?.opd ?? "—"} OPD Today`} />
          {role === "surgeon" && <Chip icon={Zap} label="OT Eligible" />}
        </>
      );
    case "nurse":
    case "ward_incharge":
      return (
        <>
          <Chip icon={HeartPulse}  label="Ward C-4" />
          <Chip icon={Moon}        label="Night Shift" />
          <Chip icon={AlertTriangle} label={`${stats?.alerts ?? "—"} Alerts`} pulse={stats?.alerts > 0} />
          {role === "ward_incharge" && <Chip icon={Users} label="Incharge" />}
        </>
      );
    case "pharmacist":
      return (
        <>
          <Chip icon={Package}     label={hospitalName} />
          <Chip icon={ClipboardList} label={`${stats?.pending ?? "—"} Pending`} pulse={stats?.pending > 0} />
          <Chip icon={Zap}         label="Drug Interaction Enabled" />
        </>
      );
    case "opd_staff":
    case "receptionist":
      return (
        <>
          <Chip icon={Building2}   label={hospitalName} />
          <Chip icon={CalendarCheck} label={`${stats?.scheduled ?? "—"} Scheduled`} />
          <Chip icon={ClipboardList} label="Registration Desk" />
        </>
      );
    case "ipd_staff":
      return (
        <>
          <Chip icon={BriefcaseMedical} label={hospitalName} />
          <Chip icon={Bed}         label={`${stats?.admitted ?? "—"} Admitted`} />
          <Chip icon={AlertTriangle} label={`${stats?.mlc ?? "—"} MLC Cases`} pulse={stats?.mlc > 0} />
        </>
      );
    case "insurance_officer":
      return (
        <>
          <Chip icon={IndianRupee} label="TPA Portal" />
          <Chip icon={FileSearch}  label={`${stats?.pending ?? "—"} Pending Claims`} pulse={stats?.pending > 0} />
          <Chip icon={Shield}      label="NHCX v2" />
        </>
      );
    case "scheme_officer":
      return (
        <>
          <Chip icon={BadgeAlert}  label="PM-JAY Desk" />
          <Chip icon={FileSearch}  label="Eligibility Checks" />
          <Chip icon={Users}       label="MPJAY Portal" />
        </>
      );
    case "police_interface":
      return (
        <>
          <Chip icon={Scale}       label="MLC Read-Only" />
          <Chip icon={AlertTriangle} label="72h Access TTL" />
        </>
      );
    case "patient":
      return (
        <>
          {user?.mrn && <Chip icon={HeartPulse} label={`MRN: ${user.mrn}`} />}
          {user?.blood_group && <Chip icon={Activity} label={`${user.blood_group}`} />}
        </>
      );
    default:
      return null;
  }
}

// ── Patient header (light) ─────────────────────────────────────────────────
function PatientHeader({ user }) {
  const initials = (user?.full_name || "P").split(" ").map(n => n[0]).join("").slice(0,2).toUpperCase();
  return (
    <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 shrink-0 sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-forest flex items-center justify-center text-lime text-xs font-black shadow-glow">{initials}</div>
        <div>
          <p className="text-sm font-bold text-slate-900">{user?.full_name}</p>
          <p className="text-[10px] text-slate-400">
            {user?.mrn ? `MRN: ${user.mrn}` : "Patient Portal"}{user?.blood_group ? ` · ${user.blood_group}` : ""}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-slate-400 font-medium hidden md:block">
          {new Date().toLocaleDateString("en-IN", { weekday:"long", day:"numeric", month:"short" })}
        </span>
        <NotificationBell />
      </div>
    </header>
  );
}

// ── Main export ────────────────────────────────────────────────────────────
export default function RoleHeader() {
  const { user } = useAuthStore();
  const role     = user?.role;
  const theme    = ROLE_THEME[role] || ROLE_THEME.doctor;
  const [stats, setStats] = useState({});

  // Fetch quick stats for relevant roles
  useEffect(() => {
    if (!role) return;
    fetchStats();
  }, [role]);

  const fetchStats = async () => {
    try {
      if (role === "doctor" || role === "surgeon") {
        const res = await nurseAPI.getMyPatients();
        setStats({ active: res.data?.summary?.active_inpatients, opd: res.data?.summary?.todays_opd });
      }
    } catch { /* silent fail — stats are cosmetic */ }
  };

  if (role === "patient") return <PatientHeader user={user} />;

  const initials    = (user?.full_name || "U").split(" ").map(n => n[0]).join("").slice(0,2).toUpperCase();
  const displayRole = role?.replace(/_/g," ").replace(/\b\w/g, c => c.toUpperCase());
  const now         = new Date().toLocaleTimeString("en-IN", { hour:"2-digit", minute:"2-digit" });
  const date        = new Date().toLocaleDateString("en-IN", { weekday:"short", day:"numeric", month:"short" });

  return (
    <header className={`h-16 bg-gradient-to-r ${theme.accent} flex items-center justify-between px-6 shrink-0 sticky top-0 z-30 shadow-md`}>
      {/* Left — identity */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-white/20 border border-white/30 flex items-center justify-center text-white text-xs font-black backdrop-blur-sm">
            {initials}
          </div>
          <div>
            <p className="text-sm font-bold text-white leading-none">{user?.full_name}</p>
            <p className="text-[10px] text-white/60 font-semibold mt-0.5">{displayRole}</p>
          </div>
        </div>

        {/* Divider */}
        <div className="w-px h-8 bg-white/15 hidden md:block" />

        {/* Context chips */}
        <div className="hidden md:flex items-center gap-2">
          <ContextChips role={role} user={user} stats={stats} />
        </div>
      </div>

      {/* Right — time + bell */}
      <div className="flex items-center gap-4">
        <div className="hidden md:flex flex-col items-end">
          <p className="text-sm font-bold text-white leading-none">{now}</p>
          <p className="text-[10px] text-white/60 mt-0.5">{date}</p>
        </div>
        <div className="w-px h-8 bg-white/15" />
        {/* Notification bell — styled for dark header */}
        <div className="[&_button]:text-white [&_button]:hover:bg-white/10 [&_.badge]:bg-red-500">
          <NotificationBell />
        </div>
      </div>
    </header>
  );
}
