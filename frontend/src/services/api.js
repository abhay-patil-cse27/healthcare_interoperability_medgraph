import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("mg_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401 → clear auth and redirect
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("mg_token");
      localStorage.removeItem("mg_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post("/auth/register", data),
  login:    (email, password) => api.post("/auth/login", { email, password }),
  me:       () => api.get("/auth/me"),
};

// ── Profile (self-service) ────────────────────────────────────────────────
export const profileAPI = {
  get:    ()     => api.get("/profile/me"),
  update: (data) => api.patch("/profile/me", data),
};

// ── Memory ────────────────────────────────────────────────────────────────
export const memoryAPI = {
  ingest:  (data) => api.post("/memory/ingest", data),
  history: (patientId) => api.get(`/memory/history/${patientId}`),
};

// ── Chat ──────────────────────────────────────────────────────────────────
export const chatAPI = {
  query:          (data)       => api.post("/chat/", data),
  listSessions:   (patientId) => api.get("/chat/sessions", { params: patientId ? { patient_id: patientId } : {} }),
  createSession:  (patientId) => api.post(`/chat/sessions?patient_id=${patientId}`),
  getSession:     (sessionId) => api.get(`/chat/sessions/${sessionId}`),
  deleteSession:  (sessionId) => api.delete(`/chat/sessions/${sessionId}`),
};

// ── Consent ───────────────────────────────────────────────────────────────
export const consentAPI = {
  request: (data)              => api.post("/consent/request", data),
  grant:   (data)              => api.post("/consent/grant", data),
  active:  (patientId)         => api.get(`/consent/active/${patientId}`),
  revoke:  (consentId)         => api.delete(`/consent/${consentId}`),
};

// ── FHIR ──────────────────────────────────────────────────────────────────
export const fhirAPI = {
  exchange:  (data)     => api.post("/fhir/exchange", data),
  getBundle: (bundleId) => api.get(`/fhir/bundle/${bundleId}`),
};

// ── Admin ─────────────────────────────────────────────────────────────────
export const adminAPI = {
  createHospital:  (data) => api.post("/admin/hospitals", data),
  listHospitals:   ()     => api.get("/admin/hospitals"),
  createSystemUser:(data) => api.post("/admin/users", data),
  listUsers:       (role) => api.get("/admin/users", { params: role ? { role } : {} }),
  getStats:        ()     => api.get("/admin/stats"),
};

// ── Hospital ──────────────────────────────────────────────────────────────
export const hospitalAPI = {
  createDepartment:(data) => api.post("/hospital/departments", data),
  listDepartments: ()     => api.get("/hospital/departments"),
  inviteStaff:     (data) => api.post("/hospital/staff", data),
  listStaff:       ()     => api.get("/hospital/staff"),
  getStats:        ()     => api.get("/hospital/stats"),
};

// ── Patient Search (name / MRN / phone / ABHA) ────────────────────────────
export const patientSearchAPI = {
  search: (q)         => api.get("/patient/search", { params: { q } }),
  getCard: (patientId)=> api.get(`/patient/${patientId}/card`),
};

export const opdAPI = {
  bookAppointment:    (data)       => api.post("/opd/appointments", data),
  listAppointments:   (status)     => api.get("/opd/appointments", { params: status ? { status } : {} }),
  getQueue:           (deptId)     => api.get("/opd/appointments/queue", { params: deptId ? { department_id: deptId } : {} }),
  updateStatus:       (id, status) => api.patch(`/opd/appointments/${id}/status?status=${status}`),
  getStats:           ()           => api.get("/opd/stats"),
};

// ── IPD ───────────────────────────────────────────────────────────────────
export const ipdAPI = {
  admit:     (data)   => api.post("/ipd/admissions", data),
  discharge: (id)     => api.post(`/ipd/admissions/${id}/discharge`),
  getBeds:   (wardId) => api.get(`/ipd/wards/${wardId}/beds`),
};

// ── Nurse / Doctor clinical ───────────────────────────────────────────────
export const nurseAPI = {
  addNote:         (data)      => api.post("/nurse/notes", data),
  logVitals:       (data)      => api.post("/nurse/vitals", data),
  getVitals:       (patientId) => api.get(`/nurse/patients/${patientId}/vitals`),
  getMyPatients:   ()          => api.get("/nurse/my-patients"),
  getPatientHistory:(patientId)=> api.get(`/nurse/patient/${patientId}/full-history`),
};

// ── Notifications ──────────────────────────────────────────────────────────
export const notifAPI = {
  getAll:      (unreadOnly) => api.get("/notifications/", { params: unreadOnly ? { unread_only: true } : {} }),
  markRead:    (id)         => api.post(`/notifications/${id}/read`),
  markAllRead: ()           => api.post("/notifications/mark-all-read"),
  getCount:    ()           => api.get("/notifications/count"),
};

// ── Activity Logs ──────────────────────────────────────────────────────────
export const logsAPI = {
  getAll: (params) => api.get("/logs/", { params }),
  getMy:  ()       => api.get("/logs/my"),
};

// ── Pharmacy ──────────────────────────────────────────────────────────────
export const pharmacyAPI = {
  createPrescription: (data)   => api.post("/prescription/", data),
  getPrescriptions:   (patientId) => api.get(`/prescription/patient/${patientId}`),
  getQueue:           (status) => api.get("/prescription/queue", { params: { status } }),
  getStats:           ()       => api.get("/prescription/stats"),
  dispense:           (id)     => api.post(`/prescription/${id}/dispense`),
};

// ── Finance/Scheme ────────────────────────────────────────────────────────
export const financeAPI = {
  checkEligibility: (data)           => api.post("/scheme/eligibility/check", data),
  disburse:         (claimId, amount) => api.post(`/scheme/disburse/${claimId}?amount=${amount}`),
  createClaim:      (data)           => api.post("/insurance/claims", data),
  listClaims:       (status)         => api.get("/insurance/claims", { params: status ? { status } : {} }),
  getClaimStats:    ()               => api.get("/insurance/claims/stats"),
  updateClaim:      (id, status)     => api.patch(`/insurance/claims/${id}/status?status=${status}`),
};

// ── MLC ───────────────────────────────────────────────────────────────────
export const mlcAPI = {
  createRecord: (data) => api.post("/mlc/records", data),
  listRecords:  ()     => api.get("/mlc/records"),
  getRecord:    (id)   => api.get(`/mlc/records/${id}`),
  getStats:     ()     => api.get("/mlc/stats"),
};

// ── Legal ─────────────────────────────────────────────────────────────────
export const legalAPI = {
  getPrivacyPolicy: () => api.get("/legal/privacy-policy"),
  getCompliance:    () => api.get("/legal/compliance"),
};

export const healthAPI = {
  check: () => api.get("/health"),
};

// ── Documents (Patient PDF Upload) ────────────────────────────────────────
export const documentsAPI = {
  upload: (formData) => api.post("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 120000,
  }),
  myDocuments:    ()   => api.get("/documents/my-documents"),
  getMetadata:    (id) => api.get(`/documents/${id}`),
  getPdfUrl:      (id) => `${BASE_URL}/documents/${id}/pdf`,
  getFhir:        (id) => api.get(`/documents/${id}/fhir`),
  triggerScreening:(id) => api.post(`/documents/${id}/trigger-screening`),
};

// ── Screening (Responsible AI Pipeline) ───────────────────────────────────
export const screeningAPI = {
  // HITL Validator
  summarise:      (data) => api.post("/screening/summarise", data),
  getHitlQueue:   ()     => api.get("/screening/hitl/queue"),
  getHitlDetail:  (id)   => api.get(`/screening/hitl/${id}`),
  editForward:    (data) => api.post("/screening/hitl/edit-forward", data),
  acceptForward:  (data) => api.post("/screening/hitl/accept-forward", data),
  reject:         (data) => api.post("/screening/hitl/reject", data),
  escalate:       (data) => api.post("/screening/hitl/escalate", data),
  // Doctor
  doctorInbox:    ()     => api.get("/screening/doctor/inbox"),
  doctorView:     (id)   => api.get(`/screening/doctor/${id}`),
  doctorReviewed: (id)   => api.post(`/screening/doctor/${id}/reviewed`),
};

export default api;
