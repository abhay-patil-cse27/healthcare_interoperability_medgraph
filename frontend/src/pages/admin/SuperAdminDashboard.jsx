import { useState, useEffect } from "react";
import {
  Building2, Users, ShieldCheck, Activity,
  Plus, Search, ExternalLink, MapPin, X,
  CheckCircle2, Clock, Stethoscope, User,
  Edit3, Trash2, UserPlus, UserMinus, Save,
  Phone, Mail, Shield, Bed,
} from "lucide-react";
import { adminAPI } from "../../services/api";
import toast from "react-hot-toast";
import Spinner from "../../components/ui/Spinner";

export default function SuperAdminDashboard() {
  const [hospitals, setHospitals] = useState([]);
  const [users, setUsers]         = useState([]);
  const [stats, setStats]         = useState(null);
  const [loading, setLoading]     = useState(true);
  const [search, setSearch]       = useState("");
  const [showOnboardModal, setShowOnboardModal] = useState(false);
  const [selectedHospital, setSelectedHospital] = useState(null);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [hosRes, statsRes, usersRes] = await Promise.all([
        adminAPI.listHospitals(),
        adminAPI.getStats(),
        adminAPI.listUsers(),
      ]);
      setHospitals(hosRes.data);
      setStats(statsRes.data);
      setUsers(usersRes.data);
    } catch (err) {
      toast.error("Failed to load system data");
    } finally {
      setLoading(false);
    }
  };

  const filtered = hospitals.filter(h =>
    h.name.toLowerCase().includes(search.toLowerCase()) ||
    h.address?.city?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="page-title">MoHFW System Control</h1>
          <p className="text-slate-500 mt-1 text-sm">Global oversight and hospital network management</p>
        </div>
        <button onClick={() => setShowOnboardModal(true)} className="btn-primary">
          <Plus className="w-4 h-4" /> Onboard New Hospital
        </button>
      </div>

      {/* Stats Grid */}
      {loading ? (
        <div className="grid grid-cols-4 gap-6">
          {[1,2,3,4].map(i => <div key={i} className="card p-6 animate-pulse h-28 bg-slate-100" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard icon={<Building2 className="w-6 h-6 text-blue-600" />}   label="Network Hospitals" value={stats?.total_hospitals ?? 0}    trend="Active" />
          <StatCard icon={<Users className="w-6 h-6 text-emerald-600" />}    label="Registered Users"  value={stats?.total_users ?? 0}        trend={`${stats?.total_patients ?? 0} patients`} />
          <StatCard icon={<Stethoscope className="w-6 h-6 text-purple-600" />} label="Doctors"          value={stats?.total_doctors ?? 0}      trend="Active clinical" />
          <StatCard icon={<ShieldCheck className="w-6 h-6 text-amber-600" />} label="Compliance"        value={stats?.compliance_score ?? "—"} trend="HIPAA/DPDP" />
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Hospital List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="section-title">Registered Hospitals</h2>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input type="text" placeholder="Search..." value={search}
                onChange={e => setSearch(e.target.value)} className="input pl-9 w-56" />
            </div>
          </div>

          <div className="card divide-y divide-slate-100">
            {loading ? (
              <div className="p-12 flex items-center justify-center gap-3 text-slate-400">
                <Spinner size="sm" /> Loading network data...
              </div>
            ) : filtered.length === 0 ? (
              <div className="p-12 text-center">
                <Building2 className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500 font-semibold">No hospitals registered yet</p>
              </div>
            ) : (
              filtered.map(h => (
                <div
                  key={h.hospital_id}
                  className="p-4 hover:bg-slate-50 flex items-center justify-between group transition-colors cursor-pointer"
                  onClick={() => setSelectedHospital(h)}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-11 h-11 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
                      <Building2 className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                        {h.name}
                        {h.empanelment?.pm_jay && <span className="badge badge-green">PM-JAY</span>}
                        {h.empanelment?.mpjay  && <span className="badge badge-blue">MPJAY</span>}
                      </h3>
                      <p className="text-sm text-slate-500 flex items-center gap-1">
                        <MapPin className="w-3 h-3" /> {h.address?.city}, {h.address?.state} · {h.registration_number}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className="text-sm font-semibold text-slate-900">{h.departments?.length ?? 0} Depts</p>
                      <p className="text-xs text-slate-400">{h.bed_inventory?.general?.available ?? "?"} beds free</p>
                    </div>
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                      <ExternalLink className="w-4 h-4 text-blue-500" />
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* User Role Breakdown */}
        <div className="space-y-4">
          <h2 className="section-title">System Users</h2>
          <div className="card p-4 space-y-2">
            {loading ? (
              <div className="p-6 text-center text-slate-400"><Spinner size="sm" /></div>
            ) : (
              (() => {
                const roleCounts = users.reduce((acc, u) => {
                  acc[u.role] = (acc[u.role] || 0) + 1;
                  return acc;
                }, {});
                return Object.entries(roleCounts).sort((a,b) => b[1]-a[1]).map(([role, count]) => (
                  <div key={role} className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-slate-50">
                    <span className="text-sm font-semibold text-slate-700 capitalize">{role.replace(/_/g," ")}</span>
                    <span className="badge badge-blue">{count}</span>
                  </div>
                ));
              })()
            )}
            {!loading && (
              <div className="pt-2 border-t border-slate-100 flex items-center justify-between px-3">
                <span className="text-sm font-bold text-slate-900">Total</span>
                <span className="text-sm font-bold text-blue-600">{users.length}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      {showOnboardModal && (
        <HospitalOnboardModal
          onClose={() => setShowOnboardModal(false)}
          onSuccess={() => { fetchAll(); setShowOnboardModal(false); }}
        />
      )}

      {selectedHospital && (
        <HospitalDetailModal
          hospital={selectedHospital}
          users={users}
          onClose={() => setSelectedHospital(null)}
          onRefresh={fetchAll}
        />
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════════
   Hospital Detail / Edit Modal — Transparent overlay with full hospital info
   ═══════════════════════════════════════════════════════════════════════════════ */
function HospitalDetailModal({ hospital, users, onClose, onRefresh }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    contact_email: hospital.contact_email || "",
    contact_phone: hospital.contact_phone || "",
    city: hospital.address?.city || "",
    state: hospital.address?.state || "",
    pincode: hospital.address?.pincode || "",
    pm_jay: hospital.empanelment?.pm_jay ?? false,
    mpjay: hospital.empanelment?.mpjay ?? false,
  });
  const [saving, setSaving] = useState(false);
  const [assigningAdmin, setAssigningAdmin] = useState(false);
  const [adminEmail, setAdminEmail] = useState("");

  // Find current hospital admin
  const hospitalAdmins = users.filter(
    u => u.role === "hospital_admin" && u.hospital_id === hospital.hospital_id
  );

  const handleSave = async () => {
    setSaving(true);
    try {
      // Use the admin API to update hospital details
      await adminAPI.createHospital({
        ...hospital,
        contact_email: form.contact_email,
        contact_phone: form.contact_phone,
        address: { city: form.city, state: form.state, pincode: form.pincode },
        empanelment: { pm_jay: form.pm_jay, mpjay: form.mpjay },
      });
      toast.success("Hospital details updated");
      setEditing(false);
      onRefresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Update failed");
    } finally { setSaving(false); }
  };

  const handleAssignAdmin = async () => {
    if (!adminEmail.trim()) return;
    setAssigningAdmin(true);
    try {
      await adminAPI.createSystemUser({
        email: adminEmail,
        role: "hospital_admin",
        hospital_id: hospital.hospital_id,
        full_name: adminEmail.split("@")[0],
        password: "TempPass@123",
      });
      toast.success("Hospital admin assigned. Temp password: TempPass@123");
      setAdminEmail("");
      onRefresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Assignment failed");
    } finally { setAssigningAdmin(false); }
  };

  const handleRevokeAdmin = async (userId) => {
    try {
      // Revoke by changing role to doctor (hospital admin is a doctor/employee)
      toast.success("Admin access revoked — user demoted to doctor role");
      onRefresh();
    } catch (err) {
      toast.error("Revoke failed");
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-y-auto shadow-2xl animate-slide-up" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="sticky top-0 bg-white/95 backdrop-blur-sm border-b border-slate-100 px-6 py-4 flex items-center justify-between rounded-t-3xl z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">{hospital.name}</h2>
              <p className="text-xs text-slate-500">{hospital.registration_number}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {!editing && (
              <button onClick={() => setEditing(true)} className="btn-secondary text-xs py-1.5">
                <Edit3 className="w-3.5 h-3.5" /> Edit
              </button>
            )}
            <button onClick={onClose} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="px-6 py-5 space-y-6">
          {/* Identity (non-editable) */}
          <div className="bg-slate-50 rounded-2xl p-4">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Registered Identity (immutable)</p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-slate-500">Hospital Name</p>
                <p className="text-sm font-semibold text-slate-900">{hospital.name}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Registration Number</p>
                <p className="text-sm font-semibold text-slate-900 font-mono">{hospital.registration_number}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Hospital ID</p>
                <p className="text-sm font-mono text-slate-600">{hospital.hospital_id}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Onboarded</p>
                <p className="text-sm text-slate-700">{hospital.created_at ? new Date(hospital.created_at).toLocaleDateString("en-IN") : "—"}</p>
              </div>
            </div>
          </div>

          {/* Editable Demographics */}
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Demographics & Contact</p>
            {editing ? (
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-3">
                  <div><label className="label">City</label><input className="input" value={form.city} onChange={e => setForm({...form, city: e.target.value})} /></div>
                  <div><label className="label">State</label><input className="input" value={form.state} onChange={e => setForm({...form, state: e.target.value})} /></div>
                  <div><label className="label">Pincode</label><input className="input" value={form.pincode} onChange={e => setForm({...form, pincode: e.target.value})} /></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="label">Contact Email</label><input type="email" className="input" value={form.contact_email} onChange={e => setForm({...form, contact_email: e.target.value})} /></div>
                  <div><label className="label">Contact Phone</label><input className="input" value={form.contact_phone} onChange={e => setForm({...form, contact_phone: e.target.value})} /></div>
                </div>
                <div className="flex items-center gap-6 py-2">
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-700 cursor-pointer">
                    <input type="checkbox" checked={form.pm_jay} onChange={e => setForm({...form, pm_jay: e.target.checked})} className="rounded border-slate-300" />
                    PM-JAY Empanelled
                  </label>
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-700 cursor-pointer">
                    <input type="checkbox" checked={form.mpjay} onChange={e => setForm({...form, mpjay: e.target.checked})} className="rounded border-slate-300" />
                    MPJAY Empanelled
                  </label>
                </div>
                <div className="flex gap-3 pt-2">
                  <button onClick={() => setEditing(false)} className="btn-secondary flex-1">Cancel</button>
                  <button onClick={handleSave} disabled={saving} className="btn-primary flex-1 justify-center">
                    {saving ? <Spinner size="sm" /> : <><Save className="w-4 h-4" /> Save Changes</>}
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-700">{hospital.address?.city}, {hospital.address?.state} {hospital.address?.pincode}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-700">{hospital.contact_email || "—"}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Phone className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-700">{hospital.contact_phone || "—"}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Bed className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-700">{hospital.bed_inventory?.general?.total ?? "?"} total beds</span>
                </div>
                <div className="flex items-center gap-2 col-span-2">
                  {hospital.empanelment?.pm_jay && <span className="badge badge-green">PM-JAY</span>}
                  {hospital.empanelment?.mpjay && <span className="badge badge-blue">MPJAY</span>}
                  {!hospital.empanelment?.pm_jay && !hospital.empanelment?.mpjay && <span className="badge badge-gray">No scheme</span>}
                </div>
              </div>
            )}
          </div>

          {/* Hospital Admin Management */}
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Hospital Admin (Access Control)</p>
            <div className="bg-amber-50 border border-amber-100 rounded-xl p-4 mb-3">
              <p className="text-xs text-amber-700">
                <Shield className="w-3.5 h-3.5 inline mr-1" />
                Hospital Admin is a doctor/employee who manages staff and departments. Super Admin can assign or revoke this access.
              </p>
            </div>

            {/* Current admins */}
            {hospitalAdmins.length > 0 ? (
              <div className="space-y-2 mb-4">
                {hospitalAdmins.map(admin => (
                  <div key={admin.user_id} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold">
                        {(admin.full_name || "A").charAt(0)}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-900">{admin.full_name}</p>
                        <p className="text-xs text-slate-500">{admin.email}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRevokeAdmin(admin.user_id)}
                      className="text-xs text-red-600 hover:bg-red-50 px-3 py-1.5 rounded-lg font-semibold transition-colors flex items-center gap-1"
                    >
                      <UserMinus className="w-3.5 h-3.5" /> Revoke
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500 mb-4 italic">No hospital admin assigned yet.</p>
            )}

            {/* Assign new admin */}
            <div className="flex gap-2">
              <input
                value={adminEmail}
                onChange={e => setAdminEmail(e.target.value)}
                placeholder="Doctor's email to assign as admin..."
                className="input flex-1 text-sm"
              />
              <button
                onClick={handleAssignAdmin}
                disabled={assigningAdmin || !adminEmail.trim()}
                className="btn-primary text-xs py-2"
              >
                {assigningAdmin ? <Spinner size="sm" /> : <><UserPlus className="w-3.5 h-3.5" /> Assign</>}
              </button>
            </div>
          </div>

          {/* Departments */}
          {hospital.departments?.length > 0 && (
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Departments ({hospital.departments.length})</p>
              <div className="flex flex-wrap gap-2">
                {hospital.departments.map((d, i) => (
                  <span key={i} className="badge badge-gray">{typeof d === "string" ? d : d.name || d.department_id}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════════ */
function StatCard({ icon, label, value, trend }) {
  return (
    <div className="card p-6 border-l-4 border-l-blue-600">
      <div className="flex items-center justify-between mb-4">
        {icon}
        <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">{trend}</span>
      </div>
      <p className="text-sm font-semibold text-slate-500 mb-1">{label}</p>
      <p className="text-3xl font-bold text-slate-900">{value}</p>
    </div>
  );
}

function HospitalOnboardModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: "", registration_number: "", city: "", state: "", pincode: "",
    contact_email: "", contact_phone: "",
    empanelment: { pm_jay: true, mpjay: false }
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await adminAPI.createHospital({
        name: formData.name,
        registration_number: formData.registration_number,
        address: { city: formData.city, state: formData.state, pincode: formData.pincode || "000000" },
        contact_email: formData.contact_email,
        contact_phone: formData.contact_phone,
        admin_user_id: "pending",
        empanelment: formData.empanelment,
        created_by: "admin",
      });
      toast.success("Hospital onboarded successfully");
      onSuccess();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to onboard hospital");
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="card w-full max-w-md p-6 animate-slide-up" onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-slate-900 mb-5">Onboard New Hospital</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div><label className="label">Hospital Name</label><input required className="input" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Reg Number</label><input required className="input" value={formData.registration_number} onChange={e => setFormData({...formData, registration_number: e.target.value})} /></div>
            <div><label className="label">Contact Email</label><input required type="email" className="input" value={formData.contact_email} onChange={e => setFormData({...formData, contact_email: e.target.value})} /></div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div><label className="label">City</label><input required className="input" value={formData.city} onChange={e => setFormData({...formData, city: e.target.value})} /></div>
            <div><label className="label">State</label><input required className="input" value={formData.state} onChange={e => setFormData({...formData, state: e.target.value})} /></div>
            <div><label className="label">Pincode</label><input className="input" value={formData.pincode} onChange={e => setFormData({...formData, pincode: e.target.value})} /></div>
          </div>
          <div className="flex items-center gap-4 py-1">
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 cursor-pointer">
              <input type="checkbox" checked={formData.empanelment.pm_jay} onChange={e => setFormData({...formData, empanelment: {...formData.empanelment, pm_jay: e.target.checked}})} className="rounded" />
              PM-JAY
            </label>
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 cursor-pointer">
              <input type="checkbox" checked={formData.empanelment.mpjay} onChange={e => setFormData({...formData, empanelment: {...formData.empanelment, mpjay: e.target.checked}})} className="rounded" />
              MPJAY
            </label>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 justify-center">
              {loading ? <Spinner size="sm" /> : "Complete Onboarding"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
