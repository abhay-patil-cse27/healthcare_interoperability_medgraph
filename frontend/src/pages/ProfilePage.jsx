import { useState, useEffect } from "react";
import {
  User, Phone, MapPin, Heart, Shield, Mail, Calendar,
  Edit3, Save, X, CheckCircle2, AlertCircle, Stethoscope,
  BadgeCheck, Fingerprint, Users, Lock,
} from "lucide-react";
import toast from "react-hot-toast";
import { profileAPI } from "../services/api";
import useAuthStore from "../store/authStore";
import Spinner from "../components/ui/Spinner";

const BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"];
const GENDERS      = ["male", "female", "other", "prefer_not_to_say"];

function Field({ icon: Icon, label, value, children }) {
  return (
    <div className="flex gap-3">
      <div className="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center shrink-0 mt-0.5">
        <Icon className="w-4 h-4 text-slate-500" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">{label}</p>
        {children || <p className="text-sm text-slate-700 font-medium">{value || <span className="text-slate-300 italic">Not set</span>}</p>}
      </div>
    </div>
  );
}

function SectionCard({ title, icon: Icon, children }) {
  return (
    <div className="card p-6">
      <div className="flex items-center gap-2 mb-5">
        <Icon className="w-4 h-4 text-slate-500" />
        <h2 className="text-sm font-black text-slate-700 uppercase tracking-widest">{title}</h2>
      </div>
      <div className="space-y-5">{children}</div>
    </div>
  );
}

export default function ProfilePage() {
  const { user: storeUser, refreshProfile } = useAuthStore();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving,  setSaving]  = useState(false);
  const [editing, setEditing] = useState(false);
  const [form,    setForm]    = useState({});

  useEffect(() => { fetchProfile(); }, []);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const { data } = await profileAPI.get();
      setProfile(data);
      setForm(data);
    } catch { toast.error("Failed to load profile"); }
    finally { setLoading(false); }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        full_name:         form.full_name,
        phone:             form.phone,
        gender:            form.gender,
        date_of_birth:     form.date_of_birth,
        address:           form.address,
        emergency_contact: form.emergency_contact,
        blood_group:       form.blood_group,
        abha_id:           form.abha_id,
        specialization:    form.specialization,
      };
      const { data } = await profileAPI.update(payload);
      setProfile(data);
      setForm(data);
      // Refresh authStore so header chips reflect new name immediately
      await refreshProfile();
      setEditing(false);
      toast.success("Profile updated!");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Update failed");
    } finally { setSaving(false); }
  };

  const set = (key) => (e) => setForm(f => ({ ...f, [key]: e.target.value }));

  const isPatient = profile?.role === "patient";
  const isDoctor  = ["doctor","surgeon"].includes(profile?.role);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <Spinner /><span className="ml-3 text-slate-400">Loading profile…</span>
    </div>
  );

  const initials = (profile?.full_name || "U").split(" ").map(n => n[0]).join("").slice(0,2).toUpperCase();
  const avatarColor = profile?.gender === "female" ? "bg-pink-500" : profile?.gender === "male" ? "bg-blue-600" : "bg-slate-500";
  const roleDisplay = profile?.role?.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      {/* Header card */}
      <div className="card p-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex items-center gap-5">
            {/* Avatar */}
            <div className={`w-16 h-16 rounded-2xl ${avatarColor} flex items-center justify-center text-white text-xl font-black shadow-md`}>
              {initials}
            </div>
            <div>
              <h1 className="text-xl font-black text-slate-900">{profile?.full_name}</h1>
              <div className="flex items-center gap-2 mt-1 flex-wrap">
                <span className="badge badge-blue capitalize">{roleDisplay}</span>
                {profile?.mrn && (
                  <span className="badge badge-gray font-mono text-xs">{profile.mrn}</span>
                )}
                {profile?.blood_group && (
                  <span className="px-2 py-0.5 bg-red-50 text-red-600 border border-red-100 rounded-full text-xs font-bold">
                    {profile.blood_group}
                  </span>
                )}
                {profile?.is_active && (
                  <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> Active
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-1.5">{profile?.email}</p>
            </div>
          </div>

          {/* Edit / Save buttons */}
          <div className="flex gap-2">
            {editing ? (
              <>
                <button onClick={() => { setEditing(false); setForm(profile); }} className="btn-ghost text-sm gap-1.5">
                  <X className="w-4 h-4" /> Cancel
                </button>
                <button onClick={handleSave} disabled={saving} className="btn-primary text-sm gap-1.5">
                  {saving ? <Spinner size="sm" /> : <Save className="w-4 h-4" />}
                  Save changes
                </button>
              </>
            ) : (
              <button onClick={() => setEditing(true)} className="btn-secondary text-sm gap-1.5">
                <Edit3 className="w-4 h-4" /> Edit Profile
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Read-only info banner */}
      <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-100 rounded-xl text-xs text-amber-700">
        <AlertCircle className="w-4 h-4 shrink-0" />
        <span>Role, hospital assignment, and medical license number are managed by your Hospital Administrator and cannot be changed here.</span>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Personal Info */}
        <SectionCard title="Personal Information" icon={User}>
          <Field icon={User} label="Full Name">
            {editing
              ? <input value={form.full_name || ""} onChange={set("full_name")} className="input text-sm" placeholder="Full name" />
              : <p className="text-sm text-slate-700 font-medium">{profile?.full_name}</p>
            }
          </Field>

          <Field icon={Calendar} label="Date of Birth">
            {editing
              ? <input type="date" value={form.date_of_birth || ""} onChange={set("date_of_birth")} className="input text-sm" />
              : <p className="text-sm text-slate-700 font-medium">{profile?.date_of_birth || <span className="text-slate-300 italic">Not set</span>}</p>
            }
          </Field>

          <Field icon={Users} label="Gender">
            {editing
              ? (
                <select value={form.gender || ""} onChange={set("gender")} className="input text-sm capitalize">
                  <option value="">Select gender</option>
                  {GENDERS.map(g => <option key={g} value={g} className="capitalize">{g.replace(/_/g," ")}</option>)}
                </select>
              )
              : <p className="text-sm text-slate-700 font-medium capitalize">{profile?.gender?.replace(/_/g," ") || <span className="text-slate-300 italic">Not set</span>}</p>
            }
          </Field>

          {isPatient && (
            <Field icon={Heart} label="Blood Group">
              {editing
                ? (
                  <select value={form.blood_group || ""} onChange={set("blood_group")} className="input text-sm">
                    <option value="">Select blood group</option>
                    {BLOOD_GROUPS.map(b => <option key={b} value={b}>{b}</option>)}
                  </select>
                )
                : <p className="text-sm text-slate-700 font-bold">{profile?.blood_group || <span className="text-slate-300 italic font-normal">Not set</span>}</p>
              }
            </Field>
          )}
        </SectionCard>

        {/* Contact Info */}
        <SectionCard title="Contact" icon={Phone}>
          <Field icon={Phone} label="Phone">
            {editing
              ? <input value={form.phone || ""} onChange={set("phone")} className="input text-sm" placeholder="+91-98765-43210" />
              : <p className="text-sm text-slate-700 font-medium">{profile?.phone || <span className="text-slate-300 italic">Not set</span>}</p>
            }
          </Field>

          <Field icon={Mail} label="Email (cannot change)">
            <p className="text-sm text-slate-400 font-medium">{profile?.email}</p>
          </Field>

          <Field icon={MapPin} label="Address">
            {editing
              ? <textarea value={form.address || ""} onChange={set("address")} className="input text-sm resize-none" rows={2} placeholder="Full address" />
              : <p className="text-sm text-slate-700 font-medium">{profile?.address || <span className="text-slate-300 italic">Not set</span>}</p>
            }
          </Field>

          <Field icon={AlertCircle} label="Emergency Contact">
            {editing
              ? <input value={form.emergency_contact || ""} onChange={set("emergency_contact")} className="input text-sm" placeholder="Name + phone" />
              : <p className="text-sm text-slate-700 font-medium">{profile?.emergency_contact || <span className="text-slate-300 italic">Not set</span>}</p>
            }
          </Field>
        </SectionCard>

        {/* Health IDs — patients only */}
        {isPatient && (
          <SectionCard title="Health Identifiers" icon={Fingerprint}>
            <Field icon={BadgeCheck} label="MRN (Medical Record Number)">
              <p className="text-sm font-black text-blue-700 font-mono tracking-wide">{profile?.mrn || "—"}</p>
              <p className="text-[10px] text-slate-400 mt-1">Issued by hospital. Used on your wristband.</p>
            </Field>

            <Field icon={Shield} label="ABHA ID">
              {editing
                ? <input value={form.abha_id || ""} onChange={set("abha_id")} className="input text-sm font-mono" placeholder="91-XXXX-XXXX-XXXX" />
                : <p className="text-sm text-slate-700 font-mono">{profile?.abha_id || <span className="text-slate-300 italic font-sans">Not linked</span>}</p>
              }
              {editing && <p className="text-[10px] text-slate-400 mt-1">Format: 91-XXXX-XXXX-XXXX</p>}
            </Field>
          </SectionCard>
        )}

        {/* Staff info — doctors etc. */}
        {!isPatient && (
          <SectionCard title="Professional Details" icon={Stethoscope}>
            <Field icon={Stethoscope} label="Specialization">
              {editing && isDoctor
                ? <input value={form.specialization || ""} onChange={set("specialization")} className="input text-sm" placeholder="e.g. Cardiology" />
                : <p className="text-sm text-slate-700 font-medium">{profile?.specialization || <span className="text-slate-300 italic">Not set</span>}</p>
              }
            </Field>
            <Field icon={BadgeCheck} label="License / Registration">
              <p className="text-sm text-slate-400 font-mono">{profile?.license_number || "—"}</p>
              <p className="text-[10px] text-slate-400 mt-1">Managed by Hospital Admin</p>
            </Field>
            <Field icon={Lock} label="Role">
              <p className="text-sm text-slate-700 font-medium capitalize">{roleDisplay}</p>
              <p className="text-[10px] text-slate-400 mt-1">Cannot be changed by self</p>
            </Field>
          </SectionCard>
        )}
      </div>

      {/* Security notice */}
      <div className="card p-5 flex items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
        </div>
        <div>
          <p className="text-sm font-bold text-slate-900">Data is encrypted at rest</p>
          <p className="text-xs text-slate-400 mt-0.5">All updates are audit-logged. Password changes require current password verification (contact admin to reset).</p>
        </div>
      </div>
    </div>
  );
}
