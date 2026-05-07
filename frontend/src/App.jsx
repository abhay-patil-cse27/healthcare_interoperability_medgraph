import { Routes, Route, Navigate } from "react-router-dom";
import useAuthStore from "./store/authStore";

// Layout
import AppLayout      from "./components/layout/AppLayout";
import ProtectedRoute from "./components/layout/ProtectedRoute";
import GuestRoute     from "./components/layout/GuestRoute";

// Public pages
import Landing  from "./pages/Landing";
import Login    from "./pages/Login";
import LoginPatient from "./pages/LoginPatient";
import LoginStaff   from "./pages/LoginStaff";
import Register from "./pages/Register";

// Patient
import HealthRecords   from "./pages/patient/HealthRecords";
import PatientChat     from "./pages/patient/PatientChat";
import PatientConsents from "./pages/patient/PatientConsents";
import DocumentUpload  from "./pages/patient/DocumentUpload";

// Doctor / Surgeon
import PatientLookup  from "./pages/doctor/PatientLookup";
import ClinicalQuery  from "./pages/doctor/ClinicalQuery";
import DoctorConsents from "./pages/doctor/DoctorConsents";
import FHIRExchange   from "./pages/doctor/FHIRExchange";
import ScreeningInbox from "./pages/doctor/ScreeningInbox";

// Admin
import SuperAdminDashboard    from "./pages/admin/SuperAdminDashboard";
import HospitalAdminDashboard from "./pages/hospital/HospitalAdminDashboard";

// Clinical
import NurseStation      from "./pages/nurse/NurseStation";
import PharmacistConsole from "./pages/pharmacist/PharmacistConsole";

// Operations
import OPDDashboard from "./pages/opd/OPDDashboard";
import IPDDashboard from "./pages/ipd/IPDDashboard";

// Finance & Legal
import InsuranceDashboard from "./pages/finance/InsuranceDashboard";
import SchemeDashboard    from "./pages/finance/SchemeDashboard";
import MLCDashboard       from "./pages/mlc/MLCDashboard";

// Shared
import ProfilePage from "./pages/ProfilePage";

// HITL Validator
import HITLDashboard from "./pages/hitl/HITLDashboard";

// ── Role-based root redirect ────────────────────────────────────────────────
function RootRedirect() {
  const { isAuthenticated, user } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/landing" replace />;

  const roleMap = {
    super_admin:      "/admin",
    govt_admin:       "/admin",
    hospital_admin:   "/hospital",
    doctor:           "/doctor",
    surgeon:          "/doctor",
    nurse:            "/nurse",
    ward_incharge:    "/nurse",
    ward_bot:         "/nurse",
    pharmacist:       "/pharmacist",
    opd_staff:        "/opd",
    ipd_staff:        "/ipd",
    receptionist:     "/opd",
    insurance_officer:"/finance",
    scheme_officer:   "/scheme",
    police_interface: "/mlc",
    hitl_validator:   "/hitl",
    patient:          "/patient",
  };
  return <Navigate to={roleMap[user?.role] || "/patient"} replace />;
}

export default function App() {
  return (
    <Routes>
      {/* ── Root ─────────────────────────────────────────────────────── */}
      <Route path="/"         element={<RootRedirect />} />
      <Route path="/landing"  element={<Landing />} />

      {/* ── Auth pages — GuestRoute prevents back-button re-login ─────── */}
      <Route path="/login"         element={<GuestRoute><Login /></GuestRoute>} />
      <Route path="/login/patient" element={<GuestRoute><LoginPatient /></GuestRoute>} />
      <Route path="/login/staff"   element={<GuestRoute><LoginStaff /></GuestRoute>} />
      <Route path="/register"      element={<GuestRoute><Register /></GuestRoute>} />

      {/* ── Patient ──────────────────────────────────────────────────── */}
      <Route path="/patient" element={
        <ProtectedRoute allowedRoles={["patient"]}>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index           element={<HealthRecords />} />
        <Route path="chat"     element={<PatientChat />} />
        <Route path="consents" element={<PatientConsents />} />
        <Route path="documents" element={<DocumentUpload />} />
      </Route>

      {/* ── Doctor / Surgeon ─────────────────────────────────────────── */}
      <Route path="/doctor" element={
        <ProtectedRoute allowedRoles={["doctor", "surgeon"]}>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index            element={<PatientLookup />} />
        <Route path="chat"      element={<ClinicalQuery />} />
        <Route path="consents"  element={<DoctorConsents />} />
        <Route path="fhir"      element={<FHIRExchange />} />
        <Route path="screening" element={<ScreeningInbox />} />
        <Route path="mlc"       element={<MLCDashboard />} />
      </Route>

      {/* ── Super Admin / Govt Admin ──────────────────────────────────── */}
      <Route path="/admin" element={
        <ProtectedRoute allowedRoles={["super_admin", "govt_admin"]}>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index element={<SuperAdminDashboard />} />
      </Route>

      {/* ── Hospital Admin ────────────────────────────────────────────── */}
      <Route path="/hospital" element={
        <ProtectedRoute allowedRoles={["hospital_admin"]}>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index element={<HospitalAdminDashboard />} />
      </Route>

      {/* ── Nurse / Ward Incharge ─────────────────────────────────────── */}
      <Route path="/nurse" element={
        <ProtectedRoute allowedRoles={["nurse", "ward_incharge", "ward_bot"]}>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index element={<NurseStation />} />
      </Route>

      {/* ── Pharmacist ────────────────────────────────────────────────── */}
      <Route path="/pharmacist" element={
        <ProtectedRoute allowedRoles={["pharmacist"]}>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index element={<PharmacistConsole />} />
      </Route>

      {/* ── OPD Staff / Receptionist ──────────────────────────────────── */}
      <Route path="/opd" element={
        <ProtectedRoute allowedRoles={["opd_staff", "receptionist"]}>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index element={<OPDDashboard />} />
      </Route>

      {/* ── IPD Staff ─────────────────────────────────────────────────── */}
      <Route path="/ipd" element={
        <ProtectedRoute allowedRoles={["ipd_staff"]}>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index element={<IPDDashboard />} />
      </Route>

      {/* ── Insurance Officer ─────────────────────────────────────────── */}
      <Route path="/finance" element={
        <ProtectedRoute allowedRoles={["insurance_officer"]}>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index element={<InsuranceDashboard />} />
      </Route>

      {/* ── Scheme Officer ────────────────────────────────────────────── */}
      <Route path="/scheme" element={
        <ProtectedRoute allowedRoles={["scheme_officer"]}>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index element={<SchemeDashboard />} />
      </Route>

      {/* ── Police / MLC ──────────────────────────────────────────────── */}
      <Route path="/mlc" element={
        <ProtectedRoute allowedRoles={["police_interface", "doctor", "surgeon", "ward_incharge"]}>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index element={<MLCDashboard />} />
      </Route>

      {/* ── HITL Validator (Responsible AI) ────────────────────────────── */}
      <Route path="/hitl" element={
        <ProtectedRoute allowedRoles={["hitl_validator", "super_admin", "hospital_admin"]}>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index element={<HITLDashboard />} />
      </Route>

      {/* ── Universal: Profile (all authenticated roles) ─────────────── */}
      <Route path="/profile" element={
        <ProtectedRoute allowedRoles={[
          "super_admin","govt_admin","hospital_admin",
          "doctor","surgeon","nurse","ward_incharge","ward_bot",
          "pharmacist","opd_staff","ipd_staff","receptionist",
          "insurance_officer","scheme_officer","police_interface","hitl_validator","patient"
        ]}>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index element={<ProfilePage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
