import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Activity, Menu, X, ChevronRight } from "lucide-react";

const NAV_LINKS = [
  { label: "Features",   href: "#features" },
  { label: "Pathways",   href: "#pathways" },
  { label: "Compliance", href: "#compliance" },
  { label: "Roles",      href: "#roles" },
];

export default function LandingHeader() {
  const [scrolled, setScrolled]   = useState(false);
  const [mobileOpen, setMobile]   = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-white/95 backdrop-blur-xl shadow-sm"
          : "bg-transparent"
      }`}
      style={scrolled ? {borderBottom: '1px solid rgba(22,51,0,0.08)'} : {}}
    >
      <div className="max-w-7xl mx-auto px-6">
        <div className="h-16 flex items-center justify-between">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group relative z-50">
            <div className="relative">
              <div className="absolute inset-0 blur opacity-40 group-hover:opacity-70 transition-opacity rounded-xl" style={{background: '#9FE870'}} />
              <div className="relative w-9 h-9 rounded-xl flex items-center justify-center" style={{background: '#163300', border: '1px solid rgba(159,232,112,0.35)', boxShadow: '0 0 12px rgba(159,232,112,0.25)'}}>
                <Activity className="w-5 h-5" style={{color: '#9FE870'}} />
              </div>
            </div>
            <span className="text-xl font-black tracking-tight" style={{color: scrolled ? '#0e0f0c' : '#ffffff'}}>MedGraph</span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map(l => (
              <a
                key={l.label}
                href={l.href}
                className="px-4 py-2 rounded-lg text-sm font-bold transition-all"
                style={{color: scrolled ? '#163300' : 'rgba(255,255,255,0.85)'}}
                onMouseEnter={e => { e.currentTarget.style.color = '#9FE870'; e.currentTarget.style.background = 'rgba(159,232,112,0.1)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = scrolled ? '#163300' : 'rgba(255,255,255,0.85)'; e.currentTarget.style.background = 'transparent'; }}
              >
                {l.label}
              </a>
            ))}
          </nav>

          {/* CTA — single Login button */}
          <div className="hidden md:flex items-center">
            <Link
              to="/login"
              className="flex items-center gap-2 px-5 py-2 text-sm font-bold rounded-full transition-all"
              style={{background: '#9FE870', color: '#163300', boxShadow: '0 0 16px rgba(159,232,112,0.3)'}}
            >
              Login
            </Link>
          </div>

          {/* Mobile toggle */}
          <button
            onClick={() => setMobile(!mobileOpen)}
            className="md:hidden p-2 rounded-xl hover:bg-slate-100 transition-colors"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden bg-white border-t border-slate-100 py-4 space-y-1 animate-slide-up">
            {NAV_LINKS.map(l => (
              <a
                key={l.label}
                href={l.href}
                onClick={() => setMobile(false)}
                className="flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-semibold transition-all"
                style={{color: '#163300'}}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(159,232,112,0.1)'; e.currentTarget.style.color = '#163300'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}
              >
                <ChevronRight className="w-4 h-4 text-slate-400" />
                {l.label}
              </a>
            ))}
            <div className="pt-3 px-4 flex flex-col gap-2 border-t border-slate-100 mt-3">
              <Link to="/login" onClick={() => setMobile(false)} className="btn-primary justify-center text-sm py-2.5">
                Login
              </Link>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
