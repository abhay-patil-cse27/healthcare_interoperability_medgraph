import { Link } from "react-router-dom";
import {
  Activity, Mail, Globe, Shield, FileText,
  Phone, MapPin, HeartPulse, ArrowUpRight
} from "lucide-react";

const FOOTER_LINKS = {
  Platform: [
    { label: "Patient Portal",    to: "/register" },
    { label: "Staff Login",       to: "/login" },
    { label: "FHIR R4 Docs",     href: "https://www.hl7.org/fhir/R4/" },
    { label: "ABDM Integration",  href: "https://abdm.gov.in" },
    { label: "API Reference",     href: "http://localhost:8000/docs" },
  ],
  Roles: [
    { label: "Doctors & Surgeons", to: "/login" },
    { label: "Nurses & Ward",      to: "/login" },
    { label: "Pharmacists",        to: "/login" },
    { label: "Insurance Officers", to: "/login" },
    { label: "Police Interface",   to: "/login" },
  ],
  Compliance: [
    { label: "DPDP Act 2023",     href: "#" },
    { label: "HIPAA Framework",   href: "#" },
    { label: "NHA Guidelines",    href: "https://nha.gov.in" },
    { label: "NHCX v2 Protocol",  href: "#" },
    { label: "IT Act Section 43A",href: "#" },
  ],
};

const STATS = [
  { value: "16",     label: "User Roles" },
  { value: "FHIR R4",label: "Standard" },
  { value: "PM-JAY", label: "Integrated" },
  { value: "AES-256",label: "Encryption" },
];

export default function LandingFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="bg-slate-950 text-white">
      {/* Stats bar */}
      <div className="border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {STATS.map(s => (
              <div key={s.label} className="text-center">
                <p className="text-2xl font-black text-white">{s.value}</p>
                <p className="text-xs text-slate-500 font-semibold mt-1 uppercase tracking-widest">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main footer body */}
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-12">
          {/* Brand column */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-forest border border-lime/30 shadow-glow flex items-center justify-center">
                <HeartPulse className="w-5 h-5 text-lime" />
              </div>
              <div>
                <p className="font-black text-lg text-white tracking-tight">MedGraph</p>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">AI Healthcare Platform</p>
              </div>
            </div>
            <p className="text-slate-400 text-sm leading-relaxed max-w-xs mb-6">
              A unified government-scale healthcare interoperability platform connecting
              hospitals, patients, insurance TPAs, and legal interfaces across India.
            </p>
            {/* Contact */}
            <div className="space-y-2">
              {[
                { icon: Mail,    text: "platform@mohfw.gov.in" },
                { icon: Phone,   text: "+91-11-2306-3928" },
                { icon: MapPin,  text: "Nirman Bhawan, New Delhi 110 011" },
              ].map(({ icon: Icon, text }) => (
                <div key={text} className="flex items-center gap-2 text-xs text-slate-500">
                  <Icon className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                  {text}
                </div>
              ))}
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(FOOTER_LINKS).map(([group, links]) => (
            <div key={group}>
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4">{group}</p>
              <ul className="space-y-3">
                {links.map(l => (
                  <li key={l.label}>
                    {l.to ? (
                      <Link
                        to={l.to}
                        className="text-sm text-slate-400 hover:text-white transition-colors flex items-center gap-1 group"
                      >
                        {l.label}
                        <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </Link>
                    ) : (
                      <a
                        href={l.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-slate-400 hover:text-white transition-colors flex items-center gap-1 group"
                      >
                        {l.label}
                        <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3 text-xs text-slate-600">
            <Shield className="w-3.5 h-3.5" />
            <span>© {year} Ministry of Health &amp; Family Welfare, Government of India</span>
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            <span>DPDP Compliant</span>
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            <span>FHIR R4</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-600">
            <span className="font-bold text-slate-500 uppercase tracking-widest text-[10px]">Built by TLE_Eliminators · KIT Kolhapur · Cognizant Technoverse 2026</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
