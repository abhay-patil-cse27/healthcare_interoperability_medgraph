/**
 * PatientChip — compact selected-patient display.
 * Shows: avatar, name, MRN, blood group badge.
 * Used after PatientSearchBar selects a patient.
 */
export default function PatientChip({ patient }) {
  if (!patient) return null;
  const initials = (patient.full_name || "P").split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase();
  const avatarColor = patient.gender === "female" ? "bg-pink-500" : patient.gender === "male" ? "bg-blue-600" : "bg-slate-500";

  return (
    <div className="flex items-center gap-3 px-3 py-2.5 bg-blue-50 border border-blue-200 rounded-xl">
      {/* Avatar */}
      <div className={`w-9 h-9 rounded-full ${avatarColor} flex items-center justify-center text-white text-xs font-black shrink-0`}>
        {initials}
      </div>

      {/* Info */}
      <div className="min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="font-bold text-slate-900 text-sm leading-none">{patient.full_name}</p>
          {patient.mrn && (
            <span className="text-[10px] font-black px-2 py-0.5 bg-white text-blue-700 border border-blue-200 rounded-full font-mono">
              {patient.mrn}
            </span>
          )}
          {patient.blood_group && (
            <span className="text-[10px] font-bold px-1.5 py-0.5 bg-red-50 text-red-600 border border-red-100 rounded-full">
              {patient.blood_group}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 mt-1">
          {patient.phone && (
            <p className="text-xs text-slate-500">{patient.phone}</p>
          )}
          {patient.abha_id && (
            <p className="text-xs text-slate-400 font-mono">ABHA: {patient.abha_id}</p>
          )}
          {patient.gender && !patient.phone && (
            <p className="text-xs text-slate-400 capitalize">{patient.gender}</p>
          )}
        </div>
      </div>
    </div>
  );
}
