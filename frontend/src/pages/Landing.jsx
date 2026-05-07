import { Link } from "react-router-dom";
import {
  Activity, Shield, Lock, Building2, Zap, ArrowRight,
  Globe, Database, Cpu, Users, Stethoscope, Package,
  BarChart3, Scale, CheckCircle2, HeartPulse, Brain,
  FileText, GitBranch,
} from "lucide-react";
import LandingHeader from "../components/layout/LandingHeader";
import LandingFooter from "../components/layout/LandingFooter";
import Globe3D from "../components/ui/Globe";

const PATHWAYS = [
  {
    icon: Stethoscope,
    title: "OPD Pathway",
    color: "bg-[#163300]",
    iconColor: "text-[#9FE870]",
    bg: "bg-[#9FE870]",
    text: "text-[#163300]",
    steps: [
      "Registration / ABHA ID check",
      "Scheme eligibility (PM-JAY/MPJAY)",
      "Doctor consultation + ICD-10 diagnosis",
      "Prescription → Pharmacy dispensing",
      "Follow-up scheduling",
    ],
  },
  {
    icon: Building2,
    title: "IPD Non-Surgical",
    color: "bg-[#163300]",
    iconColor: "text-[#9FE870]",
    bg: "bg-[#9FE870]",
    text: "text-[#163300]",
    steps: [
      "OPD → Admission order",
      "Bed/ward assignment",
      "Daily doctor rounds + nurse vitals",
      "Ward Bot automated monitoring",
      "Discharge + insurance claim",
    ],
  },
  {
    icon: Shield,
    title: "Surgical / Emergency",
    color: "bg-[#163300]",
    iconColor: "text-[#9FE870]",
    bg: "bg-[#9FE870]",
    text: "text-[#163300]",
    steps: [
      "Emergency triage + MLC check",
      "Pre-op assessment + OT scheduling",
      "Intraoperative recording",
      "Post-op recovery (ward cycle)",
      "Surgical claim up to ₹5L (PM-JAY)",
    ],
  },
];

const ROLE_CARDS = [
  { icon: BarChart3,   label: "Govt Admin",        desc: "MoHFW system oversight, national audit" },
  { icon: Building2,   label: "Hospital Admin",    desc: "Staff management, departments, onboarding" },
  { icon: Stethoscope, label: "Doctor / Surgeon",  desc: "Clinical query, RAG, prescriptions, FHIR" },
  { icon: Users,       label: "Nurse / Incharge",  desc: "Ward vitals, IPD shift notes, alerts" },
  { icon: Package,     label: "Pharmacist",        desc: "Dispensing queue, drug interactions" },
  { icon: FileText,    label: "OPD / Receptionist",desc: "Appointments, patient registration" },
  { icon: Building2,   label: "IPD Staff",         desc: "Admissions, bed management, discharge" },
  { icon: Shield,      label: "Insurance Officer", desc: "Claims, TPA, pre-authorization, NHCX" },
  { icon: Globe,       label: "Scheme Officer",    desc: "PM-JAY / MPJAY disbursement checks" },
  { icon: Scale,       label: "Police Interface",  desc: "MLC records (read-only, 72h TTL)" },
  { icon: Lock,        label: "Patient",           desc: "Own records, consent, ABHA linking" },
];

const FEATURES = [
  { icon: Brain,     title: "AI Clinical RAG",      desc: "Consent-gated LLM queries over patient records using Qdrant vector store and Neo4j knowledge graph.", accent: "bg-[#163300] text-[#9FE870]" },
  { icon: GitBranch, title: "FHIR R4 Exchange",     desc: "Generate and push structured FHIR bundles to ABHA gateway. Full ICD-10 + SNOMED CT coding support.", accent: "bg-[#163300] text-[#9FE870]" },
  { icon: Shield,    title: "Consent Architecture", desc: "Patients own their data. Every clinical access requires a scoped, time-limited consent token.", accent: "bg-[#163300] text-[#9FE870]" },
  { icon: Zap,       title: "Real-time Vitals",     desc: "Ward Bot auto-monitoring with nurse dashboard. Critical alerts trigger notifications across roles.", accent: "bg-[#163300] text-[#9FE870]" },
  { icon: HeartPulse,title: "PM-JAY Integration",  desc: "Live scheme eligibility check, benefit disbursement, and TPA claim settlement up to ₹5L.", accent: "bg-[#163300] text-[#9FE870]" },
  { icon: Scale,     title: "MLC / Legal",          desc: "Police-facing MLC interface with field-level RBAC. Sensitive data auto-redacted based on role.", accent: "bg-[#163300] text-[#9FE870]" },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-white text-slate-900">
      <LandingHeader />

      {/* Hero — push below fixed header */}
      <section className="pt-32 pb-24 px-6 bg-[#163300] relative overflow-hidden min-h-[90vh] flex items-center">
        {/* Background decoration */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgba(159,232,112,0.15),transparent)] pointer-events-none" />
        <div className="absolute -top-40 -right-40 w-[800px] h-[800px] rounded-full bg-[#9FE870]/10 blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-2 gap-12 items-center relative z-10">
          
          {/* Left Text Content */}
          <div className="text-left">
            <h1 className="text-5xl md:text-[80px] font-black text-[#9FE870] tracking-tighter leading-[0.95] mb-6 uppercase">
              Healthcare <br />
              Without <br />
              Borders
            </h1>

            <p className="text-xl md:text-2xl text-white/90 max-w-xl mb-10 leading-relaxed font-medium">
              A unified platform connecting hospitals, patients, and insurance with AI-powered intelligence. Save time and lives.
            </p>

            <div className="flex flex-wrap items-center gap-4">
              <Link
                to="/login"
                className="flex items-center gap-2 px-8 py-4 bg-[#9FE870] text-[#163300] rounded-full font-bold text-lg shadow-xl transition-all hover:-translate-y-1 hover:brightness-110"
              >
                Login
              </Link>
            </div>

            {/* Trust badges */}
            <div className="flex flex-wrap items-center gap-6 mt-14">
              {[
                { label: "FHIR R4 Compliant" },
                { label: "ABDM 2.0 Integrated" },
                { label: "PM-JAY Enabled" },
              ].map(b => (
                <div key={b.label} className="flex items-center gap-2 text-sm text-[#9FE870] font-bold uppercase tracking-wider">
                  <CheckCircle2 className="w-5 h-5 text-[#9FE870]" />
                  {b.label}
                </div>
              ))}
            </div>
          </div>

          {/* Right Globe Content */}
          <div className="relative w-full aspect-square max-w-[600px] mx-auto">
            {/* Soft backdrop for globe */}
            <div className="absolute inset-4 bg-[#9FE870]/20 rounded-full blur-[100px]"></div>
            <Globe3D className="w-full h-full drop-shadow-2xl" />
          </div>

        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 px-6" style={{background: '#f7faf4'}}>
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-black uppercase tracking-[0.25em] mb-3" style={{color: '#163300'}}>Platform Capabilities</p>
            <h2 className="text-4xl md:text-5xl font-black mb-4" style={{color: '#0e0f0c', letterSpacing: '-0.03em'}}>Built for real clinical environments</h2>
            <p className="max-w-xl mx-auto text-base" style={{color: '#454745'}}>
              Not a demo app — every feature is backed by real backend APIs with permission enforcement.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map(({ icon: Icon, title, desc, accent }) => (
              <div
                key={title}
                className="p-7 rounded-3xl group transition-all duration-300 hover:-translate-y-1"
                style={{background: '#163300', border: '1px solid rgba(159,232,112,0.15)', boxShadow: '0 4px 24px rgba(22,51,0,0.12)'}}
              >
                <div className="w-12 h-12 rounded-2xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform" style={{background: 'rgba(159,232,112,0.15)'}}>
                  <Icon className="w-6 h-6" style={{color: '#9FE870'}} />
                </div>
                <h3 className="font-black text-lg mb-2" style={{color: '#9FE870'}}>{title}</h3>
                <p className="text-sm leading-relaxed" style={{color: 'rgba(255,255,255,0.7)'}}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Roles */}
      <section id="roles" className="py-24 px-6" style={{background: '#163300'}}>
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-black uppercase tracking-[0.25em] mb-3" style={{color: '#9FE870'}}>Access Control</p>
            <h2 className="text-4xl md:text-5xl font-black mb-4" style={{color: '#ffffff', letterSpacing: '-0.03em'}}>16-Role Permission Matrix</h2>
            <p className="max-w-xl mx-auto text-base" style={{color: 'rgba(255,255,255,0.65)'}}>
              Every user has a precisely defined role with JWT-embedded permissions.
              Staff are onboarded by Hospital Admins — never via self-registration.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {ROLE_CARDS.map(({ icon: Icon, label, desc }) => (
              <div
                key={label}
                className="flex items-center gap-4 p-5 rounded-2xl cursor-default group transition-all duration-200 hover:-translate-y-0.5"
                style={{background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(159,232,112,0.15)', boxShadow: '0 2px 12px rgba(0,0,0,0.15)'}}
              >
                <div className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform" style={{background: 'rgba(159,232,112,0.15)'}}>
                  <Icon className="w-5 h-5" style={{color: '#9FE870'}} />
                </div>
                <div>
                  <p className="font-bold text-sm" style={{color: '#ffffff'}}>{label}</p>
                  <p className="text-xs mt-0.5" style={{color: 'rgba(255,255,255,0.55)'}}>{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Care Pathways */}
      <section id="pathways" className="py-24 px-6" style={{background: '#f7faf4'}}>
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-black uppercase tracking-[0.25em] mb-3" style={{color: '#163300'}}>Clinical Workflows</p>
            <h2 className="text-4xl md:text-5xl font-black mb-4" style={{color: '#0e0f0c', letterSpacing: '-0.03em'}}>3 End-to-End Care Pathways</h2>
            <p style={{color: '#454745'}}>Complete workflows from triage to insurance settlement</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {PATHWAYS.map(({ icon: Icon, title, steps }, idx) => (
              <div key={title} className="rounded-3xl p-7 transition-all duration-300 hover:-translate-y-1" style={{background: '#163300', boxShadow: '0 8px 32px rgba(22,51,0,0.18)'}}>
                <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6" style={{background: 'rgba(159,232,112,0.18)'}}>
                  <Icon className="w-7 h-7" style={{color: '#9FE870'}} />
                </div>
                <h3 className="font-black text-xl mb-5" style={{color: '#9FE870'}}>{title}</h3>
                <ul className="space-y-3">
                  {steps.map((step, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm">
                      <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-black shrink-0 mt-0.5" style={{background: 'rgba(159,232,112,0.2)', color: '#9FE870', border: '1px solid rgba(159,232,112,0.3)'}}>
                        {i + 1}
                      </span>
                      <span style={{color: 'rgba(255,255,255,0.8)'}}>{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance */}
      <section id="compliance" className="py-24 px-6 relative overflow-hidden" style={{background: '#163300'}}>
        <div className="absolute inset-0 pointer-events-none" style={{background: 'radial-gradient(ellipse 80% 50% at 50% 100%, rgba(159,232,112,0.1), transparent)'}} />
        <div className="max-w-7xl mx-auto relative">
          <div className="text-center mb-16">
            <p className="text-xs font-black uppercase tracking-[0.25em] mb-3" style={{color: '#9FE870'}}>Standards &amp; Compliance</p>
            <h2 className="text-4xl md:text-5xl font-black mb-4" style={{color: '#ffffff', letterSpacing: '-0.03em'}}>Government-mandated protocols</h2>
            <p className="max-w-xl mx-auto text-base" style={{color: 'rgba(255,255,255,0.6)'}}>Every data exchange follows NHA-approved standards</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
            {[
              { icon: Cpu,      label: "ABDM 2.0",   desc: "ABHA-linked health records" },
              { icon: Database, label: "FHIR R4",    desc: "Interoperability standard" },
              { icon: Shield,   label: "HIPAA/DPDP", desc: "Data privacy compliance" },
              { icon: Globe,    label: "NHCX v2",    desc: "Claims exchange protocol" },
            ].map(({ icon: Icon, label, desc }) => (
              <div key={label} className="text-center p-8 rounded-3xl transition-all duration-200 hover:-translate-y-1" style={{background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(159,232,112,0.2)'}}>
                <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4" style={{background: 'rgba(159,232,112,0.15)'}}>
                  <Icon className="w-7 h-7" style={{color: '#9FE870'}} />
                </div>
                <p className="font-black text-lg" style={{color: '#9FE870'}}>{label}</p>
                <p className="text-xs mt-2" style={{color: 'rgba(255,255,255,0.55)'}}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 bg-[#163300] text-white text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_60%_at_50%_50%,rgba(159,232,112,0.1),transparent)] pointer-events-none" />
        <div className="max-w-3xl mx-auto relative">
          <h2 className="text-4xl font-black mb-4 uppercase tracking-tighter text-[#9FE870]">Ready to get started?</h2>
          <p className="text-white/80 mb-10 text-lg font-medium">
            Patients can self-register. Hospital staff are onboarded by their admin.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/login"
              className="flex items-center gap-2 px-8 py-4 bg-[#9FE870] text-[#163300] hover:brightness-105 rounded-full font-bold text-base shadow-[0_0_24px_rgba(159,232,112,0.35)] transition-all"
            >
              Login
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      <LandingFooter />
    </div>
  );
}
