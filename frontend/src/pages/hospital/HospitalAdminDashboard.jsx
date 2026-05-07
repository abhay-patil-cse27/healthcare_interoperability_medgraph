import { useState, useEffect } from "react";
import {
  Building2, UserPlus, Stethoscope, Settings,
  Users, BedDouble, Activity, RefreshCw
} from "lucide-react";
import { hospitalAPI } from "../../services/api";
import toast from "react-hot-toast";
import Spinner from "../../components/ui/Spinner";

export default function HospitalAdminDashboard() {
  const [departments, setDepartments] = useState([]);
  const [staff, setStaff]             = useState([]);
  const [stats, setStats]             = useState(null);
  const [loading, setLoading]         = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showDeptModal, setShowDeptModal]     = useState(false);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [deptRes, staffRes, statsRes] = await Promise.all([
        hospitalAPI.listDepartments(),
        hospitalAPI.listStaff(),
        hospitalAPI.getStats(),
      ]);
      setDepartments(deptRes.data);
      setStaff(staffRes.data);
      setStats(statsRes.data);
    } catch (err) {
      toast.error("Failed to load hospital data");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (staffMember) => {
    try {
      if (staffMember.is_active) {
        await hospitalAPI.deactivateStaff(staffMember.user_id);
        toast.success(`${staffMember.full_name} deactivated`);
      } else {
        await hospitalAPI.activateStaff(staffMember.user_id);
        toast.success(`${staffMember.full_name} activated`);
      }
      fetchAll();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to update staff status");
    }
  };

  const DEPT_TYPE_COLOR = {
    opd:      "bg-blue-50 text-blue-600",
    ipd:      "bg-emerald-50 text-emerald-600",
    icu:      "bg-red-50 text-red-600",
    pharmacy: "bg-amber-50 text-amber-600",
    ot:       "bg-purple-50 text-purple-600",
    emergency:"bg-orange-50 text-orange-600",
    lab:      "bg-teal-50 text-teal-600",
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="page-title">Hospital Administration</h1>
          <p className="text-slate-500 mt-1 text-sm">
            {stats?.hospital_name || "Your Hospital"} — Staff, departments & capacity
          </p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setShowDeptModal(true)} className="btn-secondary">
            <Building2 className="w-4 h-4" /> Add Department
          </button>
          <button onClick={() => setShowInviteModal(true)} className="btn-primary">
            <UserPlus className="w-4 h-4" /> Invite Staff
          </button>
        </div>
      </div>

      {/* Stats */}
      {loading ? (
        <div className="grid grid-cols-4 gap-6">
          {[1,2,3,4].map(i => <div key={i} className="card p-6 animate-pulse h-24 bg-slate-100" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: "Total Staff",    value: stats?.total_staff       ?? 0, icon: Users,     color: "border-l-blue-600" },
            { label: "Departments",    value: stats?.total_departments ?? 0, icon: Building2,  color: "border-l-emerald-600" },
            { label: "Doctors",        value: stats?.total_doctors     ?? 0, icon: Stethoscope,color: "border-l-purple-600" },
            { label: "Nurses",         value: stats?.total_nurses      ?? 0, icon: Activity,   color: "border-l-amber-600" },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className={`card p-5 border-l-4 ${color}`}>
              <div className="flex items-center justify-between mb-3">
                <Icon className="w-5 h-5 text-slate-400" />
              </div>
              <p className="text-2xl font-bold text-slate-900">{value}</p>
              <p className="text-sm text-slate-500 font-medium mt-1">{label}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Departments */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="section-title">Departments</h2>
            <button onClick={fetchAll} className="btn-ghost text-xs">
              <RefreshCw className="w-3 h-3" /> Refresh
            </button>
          </div>
          {loading ? (
            <div className="card p-8 flex justify-center"><Spinner /></div>
          ) : departments.length === 0 ? (
            <div className="card p-8 text-center">
              <Building2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-slate-500 font-medium">No departments yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {departments.map(d => (
                <div key={d.department_id} className="card p-4 flex items-center justify-between hover:border-blue-200 transition-colors">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded-lg text-xs font-bold uppercase ${DEPT_TYPE_COLOR[d.type] || "bg-slate-50 text-slate-600"}`}>
                      {d.type}
                    </span>
                    <div>
                      <p className="font-semibold text-slate-900 text-sm">{d.name}</p>
                      {d.sub_type && <p className="text-xs text-slate-400 capitalize">{d.sub_type}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {d.bed_count > 0 && (
                      <div className="text-right">
                        <p className="text-sm font-semibold text-slate-900">{d.bed_count}</p>
                        <p className="text-xs text-slate-400">Beds</p>
                      </div>
                    )}
                    <button onClick={() => toast("Department settings", { icon: "⚙️" })} className="btn-ghost p-1.5">
                      <Settings className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Staff List */}
        <div className="space-y-4">
          <h2 className="section-title">Staff Roster</h2>
          {loading ? (
            <div className="card p-8 flex justify-center"><Spinner /></div>
          ) : staff.length === 0 ? (
            <div className="card p-8 text-center">
              <Users className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-slate-500 font-medium">No staff found</p>
            </div>
          ) : (
            <div className="card divide-y divide-slate-100 max-h-[480px] overflow-auto">
              {staff.map(s => (
                <div key={s.user_id} className="p-3 flex items-center gap-3 hover:bg-slate-50 group">
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
                    {s.full_name.split(" ").map(n => n[0]).join("").slice(0,2)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-900 truncate">{s.full_name}</p>
                    <p className="text-xs text-slate-500 capitalize">{s.role.replace(/_/g," ")}{s.specialization ? ` · ${s.specialization}` : ""}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${s.is_active ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-600"}`}>
                      {s.is_active ? "Active" : "Inactive"}
                    </span>
                    <button
                      onClick={() => handleToggleActive(s)}
                      className="opacity-0 group-hover:opacity-100 text-xs px-2 py-1 rounded border border-slate-200 hover:bg-slate-100 text-slate-600 transition-all"
                    >
                      {s.is_active ? "Deactivate" : "Activate"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {showInviteModal && <InviteStaffModal onClose={() => setShowInviteModal(false)} onSuccess={fetchAll} />}
      {showDeptModal   && <AddDeptModal    onClose={() => setShowDeptModal(false)}   onSuccess={fetchAll} />}
    </div>
  );
}

function InviteStaffModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({ email: "", full_name: "", password: "Medgraph@2026", role: "doctor", specialization: "", license_number: "", phone: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await hospitalAPI.inviteStaff(form);
      toast.success(`Staff member ${form.full_name} added`);
      onSuccess();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to add staff");
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="card w-full max-w-md p-6 animate-slide-up">
        <h2 className="text-lg font-bold text-slate-900 mb-5 flex items-center gap-2">
          <UserPlus className="w-5 h-5 text-blue-600" /> Invite Staff Member
        </h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div><label className="label">Full Name</label><input required className="input" value={form.full_name} onChange={e => setForm({...form, full_name: e.target.value})} /></div>
          <div><label className="label">Work Email</label><input required type="email" className="input" value={form.email} onChange={e => setForm({...form, email: e.target.value})} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Role</label>
              <select className="input" value={form.role} onChange={e => setForm({...form, role: e.target.value})}>
                {["doctor","surgeon","nurse","ward_incharge","pharmacist","opd_staff","ipd_staff","receptionist"].map(r => (
                  <option key={r} value={r}>{r.replace(/_/g," ")}</option>
                ))}
              </select>
            </div>
            <div><label className="label">Phone</label><input className="input" value={form.phone} onChange={e => setForm({...form, phone: e.target.value})} /></div>
          </div>
          {["doctor","surgeon","pharmacist"].includes(form.role) && (
            <div className="grid grid-cols-2 gap-3">
              <div><label className="label">Specialization</label><input className="input" value={form.specialization} onChange={e => setForm({...form, specialization: e.target.value})} /></div>
              <div><label className="label">License No.</label><input className="input" value={form.license_number} onChange={e => setForm({...form, license_number: e.target.value})} /></div>
            </div>
          )}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 justify-center">
              {loading ? <Spinner size="sm" /> : "Send Credentials"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function AddDeptModal({ onClose, onSuccess }) {
  const [form, setForm]   = useState({ name: "", type: "opd", sub_type: "", bed_count: 0, hospital_id: "hosp-aiims-delhi-001" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await hospitalAPI.createDepartment(form);
      toast.success(`Department "${form.name}" created`);
      onSuccess();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create department");
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="card w-full max-w-md p-6 animate-slide-up">
        <h2 className="text-lg font-bold text-slate-900 mb-5">Create New Department</h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div><label className="label">Department Name</label><input required className="input" placeholder="e.g. Oncology OPD" value={form.name} onChange={e => setForm({...form, name: e.target.value})} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Type</label>
              <select className="input" value={form.type} onChange={e => setForm({...form, type: e.target.value})}>
                {["opd","ipd","icu","ot","pharmacy","emergency","lab"].map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}
              </select>
            </div>
            <div><label className="label">Bed Count</label><input type="number" min="0" className="input" value={form.bed_count} onChange={e => setForm({...form, bed_count: parseInt(e.target.value)||0})} /></div>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 justify-center">
              {loading ? <Spinner size="sm" /> : "Create Department"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
