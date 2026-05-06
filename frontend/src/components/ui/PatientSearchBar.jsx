/**
 * PatientSearchBar
 * ─────────────────
 * Replaces UUID text input everywhere in the app.
 * Supports: name, MRN (AIIMS-2026-00001), phone, ABHA ID.
 * Renders a dropdown of patient cards. On select, calls onSelect(patient).
 */
import { useState, useEffect, useRef } from "react";
import { Search, X, User, Loader2 } from "lucide-react";
import { patientSearchAPI } from "../../services/api";
import PatientChip from "./PatientChip";

export default function PatientSearchBar({
  onSelect,
  placeholder = "Search by name, MRN, phone or ABHA…",
  selected = null,
  onClear = null,
  className = "",
}) {
  const [query, setQuery]     = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen]       = useState(false);
  const debounceRef = useRef(null);
  const containerRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    const h = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  const handleChange = (e) => {
    const v = e.target.value;
    setQuery(v);
    if (v.length < 2) { setResults([]); setOpen(false); return; }
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(v), 300);
  };

  const doSearch = async (q) => {
    setLoading(true);
    try {
      const res = await patientSearchAPI.search(q);
      setResults(res.data || []);
      setOpen(true);
    } catch { setResults([]); }
    finally { setLoading(false); }
  };

  const handleSelect = (patient) => {
    setQuery("");
    setResults([]);
    setOpen(false);
    onSelect(patient);
  };

  const handleClear = () => {
    setQuery("");
    setResults([]);
    setOpen(false);
    if (onClear) onClear();
  };

  // If a patient is already selected, show their chip
  if (selected) {
    return (
      <div className={`flex items-center gap-3 ${className}`}>
        <PatientChip patient={selected} />
        <button
          type="button"
          onClick={handleClear}
          className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-600 transition-colors"
          title="Clear patient"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* Input */}
      <div className="relative">
        {loading
          ? <Loader2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-blue-500 animate-spin" />
          : <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        }
        <input
          value={query}
          onChange={handleChange}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder={placeholder}
          className="input pl-9 pr-4"
          autoComplete="off"
        />
      </div>

      {/* Dropdown */}
      {open && (
        <div className="absolute top-full left-0 right-0 mt-1.5 bg-white border border-slate-200 rounded-xl shadow-xl z-50 overflow-hidden animate-slide-up">
          {results.length === 0 ? (
            <div className="px-4 py-6 text-center text-slate-400 text-sm">
              <User className="w-6 h-6 mx-auto mb-2 text-slate-300" />
              No patients found for "<span className="font-semibold">{query}</span>"
            </div>
          ) : (
            <div className="max-h-72 overflow-y-auto divide-y divide-slate-50">
              {results.map(p => (
                <button
                  key={p.user_id}
                  type="button"
                  onClick={() => handleSelect(p)}
                  className="w-full px-4 py-3 hover:bg-blue-50 transition-colors text-left flex items-center gap-3"
                >
                  <PatientAvatar name={p.full_name} gender={p.gender} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-bold text-slate-900 text-sm">{p.full_name}</p>
                      {p.mrn && (
                        <span className="text-[10px] font-black px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-100 rounded-full font-mono">
                          {p.mrn}
                        </span>
                      )}
                      {p.blood_group && (
                        <span className="text-[10px] font-bold px-1.5 py-0.5 bg-red-50 text-red-600 rounded-full border border-red-100">
                          {p.blood_group}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-0.5">
                      {p.phone && <p className="text-xs text-slate-500">{p.phone}</p>}
                      {p.abha_id && <p className="text-xs text-slate-400 font-mono">ABHA: {p.abha_id}</p>}
                    </div>
                  </div>
                  {p.gender && (
                    <span className="text-xs text-slate-400 shrink-0 capitalize">{p.gender}</span>
                  )}
                </button>
              ))}
            </div>
          )}
          <div className="px-4 py-2 bg-slate-50 border-t border-slate-100">
            <p className="text-[10px] text-slate-400 font-medium">
              Search by full name · MRN · phone · ABHA ID · email
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// Small avatar inside dropdown
function PatientAvatar({ name, gender }) {
  const initials = (name || "P").split(" ").map(n => n[0]).join("").slice(0,2).toUpperCase();
  const color = gender === "female" ? "bg-pink-500" : gender === "male" ? "bg-blue-600" : "bg-slate-500";
  return (
    <div className={`w-9 h-9 rounded-full ${color} flex items-center justify-center text-white text-xs font-black shrink-0`}>
      {initials}
    </div>
  );
}
