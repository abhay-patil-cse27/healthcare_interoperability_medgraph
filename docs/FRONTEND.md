# Frontend Architecture

> React 19 · Vite 8 · Tailwind CSS 3 · Zustand · Recharts · Lucide Icons

---

## Directory Structure

```
frontend/
├── src/
│   ├── main.jsx                          # React entry point
│   ├── App.jsx                           # Router configuration (role-based)
│   ├── index.css                         # Tailwind + component classes
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppLayout.jsx             # Authenticated layout (sidebar + content)
│   │   │   ├── Sidebar.jsx               # Role-aware navigation sidebar
│   │   │   ├── RoleHeader.jsx            # Top bar with context chips
│   │   │   ├── ProtectedRoute.jsx        # Role-based route guard
│   │   │   ├── GuestRoute.jsx            # Redirect if already authenticated
│   │   │   ├── LandingHeader.jsx         # Public landing nav
│   │   │   └── LandingFooter.jsx         # Public landing footer
│   │   │
│   │   └── ui/
│   │       ├── Spinner.jsx               # Loading indicator (sm/md/lg/xl)
│   │       ├── EmptyState.jsx            # Empty content placeholder
│   │       ├── StatusDot.jsx             # Color-coded status indicator
│   │       ├── PatientSearchBar.jsx      # Multi-field patient search
│   │       ├── PatientChip.jsx           # Compact patient display
│   │       ├── NotificationBell.jsx      # Notification dropdown
│   │       └── MiniCharts.jsx            # Recharts-based visualizations
│   │
│   ├── pages/
│   │   ├── Landing.jsx                   # Public landing page
│   │   ├── Login.jsx                     # Authentication (all 17 roles)
│   │   ├── Register.jsx                  # Patient self-registration
│   │   ├── ProfilePage.jsx               # Self-service profile editor
│   │   │
│   │   ├── patient/
│   │   │   ├── HealthRecords.jsx         # Text ingestion + entity display
│   │   │   ├── DocumentUpload.jsx        # PDF upload with PHI redaction
│   │   │   ├── PatientChat.jsx           # ChatGPT-style health Q&A
│   │   │   └── PatientConsents.jsx       # Consent grant/revoke manager
│   │   │
│   │   ├── doctor/
│   │   │   ├── PatientLookup.jsx         # Patient list + sparkline stats
│   │   │   ├── ClinicalQuery.jsx         # ChatGPT-style clinical RAG
│   │   │   ├── ScreeningInbox.jsx        # AI screening review (time-bound)
│   │   │   ├── DoctorConsents.jsx        # Consent request form
│   │   │   ├── FHIRExchange.jsx          # FHIR bundle generation
│   │   │   └── PatientDetailDrawer.jsx   # Patient history + vitals charts
│   │   │
│   │   ├── hitl/
│   │   │   └── HITLDashboard.jsx         # HITL validation queue + review panel
│   │   │
│   │   ├── admin/
│   │   │   └── SuperAdminDashboard.jsx   # Hospital network + user management
│   │   │
│   │   ├── hospital/
│   │   │   └── HospitalAdminDashboard.jsx# Departments + staff management
│   │   │
│   │   ├── nurse/
│   │   │   └── NurseStation.jsx          # Ward patients + vitals + activity chart
│   │   │
│   │   ├── pharmacist/
│   │   │   └── PharmacistConsole.jsx     # Prescription queue + dispensing
│   │   │
│   │   ├── opd/
│   │   │   └── OPDDashboard.jsx          # Appointments + queue management
│   │   │
│   │   ├── ipd/
│   │   │   └── IPDDashboard.jsx          # Admissions + discharge
│   │   │
│   │   ├── finance/
│   │   │   ├── InsuranceDashboard.jsx    # Claims lifecycle management
│   │   │   └── SchemeDashboard.jsx       # PM-JAY/MPJAY eligibility
│   │   │
│   │   ├── mlc/
│   │   │   └── MLCDashboard.jsx          # Medico-legal case records
│   │   │
│   │   └── legal/                        # (placeholder)
│   │
│   ├── services/
│   │   └── api.js                        # Axios instance + all API modules
│   │
│   └── store/
│       └── authStore.js                  # Zustand auth state (login/logout/refresh)
│
├── public/
│   ├── favicon.svg
│   └── icons.svg
│
├── UI_Design/                            # Design system reference
│   ├── DESIGN.md
│   ├── theme.css
│   ├── tokens.json
│   └── variables.css
│
├── tailwind.config.js
├── postcss.config.js
├── vite.config.js
├── package.json
└── Dockerfile
```

---

## Routing Architecture

Role-based routing with automatic redirect:

| Role | Root Path | Pages |
|------|-----------|-------|
| `patient` | `/patient` | HealthRecords, DocumentUpload, PatientChat, PatientConsents |
| `doctor`, `surgeon` | `/doctor` | PatientLookup, ScreeningInbox, ClinicalQuery, DoctorConsents, FHIRExchange, MLC |
| `hitl_validator` | `/hitl` | HITLDashboard |
| `super_admin`, `govt_admin` | `/admin` | SuperAdminDashboard |
| `hospital_admin` | `/hospital` | HospitalAdminDashboard |
| `nurse`, `ward_incharge` | `/nurse` | NurseStation |
| `pharmacist` | `/pharmacist` | PharmacistConsole |
| `opd_staff`, `receptionist` | `/opd` | OPDDashboard |
| `ipd_staff` | `/ipd` | IPDDashboard |
| `insurance_officer` | `/finance` | InsuranceDashboard |
| `scheme_officer` | `/scheme` | SchemeDashboard |
| `police_interface` | `/mlc` | MLCDashboard |

All routes wrapped in `ProtectedRoute` with `allowedRoles` enforcement.

---

## Key Pages — Feature Details

### Patient: Document Upload (`/patient/documents`)
- Drag-and-drop PDF upload zone
- File validation (PDF only, max 20MB)
- Upload progress with spinner
- Result card: pages, sections, PHI redactions, chunks indexed
- Document history list with "View PDF" button
- HIPAA/FHIR/PHI compliance badges

### Patient: Chat (`/patient/chat`)
- **ChatGPT-style interface** with persistent sessions
- Left sidebar: conversation history, "New Chat" button, delete per session
- Messages persist in MongoDB across page reloads
- Suggested prompts for empty state
- Typing indicator while AI responds
- Citations shown inline under assistant messages
- Timestamps on each message

### Doctor: Clinical Query (`/doctor/chat`)
- Same ChatGPT-style layout with session sidebar
- Patient search picker (PatientSearchBar) for new conversations
- Consent status bar showing active consent
- Performance metrics (retrieval time, LLM time, cache hit)
- Sessions scoped per patient
- Consent-denied errors handled gracefully

### Doctor: AI Screening Inbox (`/doctor/screening`)
- List of HITL-forwarded screenings with consent timer
- "HITL Edited" badge when summary was modified
- Detail view: transparency label, abnormalities table, clinical summary
- "Mark as Reviewed" button to complete pipeline
- Access denied when consent expires

### Doctor: Patient Detail Drawer
- Slide-in drawer with full patient history
- **Vitals trend charts** (Heart Rate, SpO2, Blood Pressure) — interactive recharts
- Tabbed sections: Vitals, Admissions, IPD Notes, Prescriptions, Appointments
- Alert indicators for abnormal vitals

### HITL Validator Dashboard (`/hitl`)
- Queue of pending AI screenings (priority indicators)
- Stats: pending count, critical findings, abnormalities
- Split-panel: queue list + review panel
- Review panel: flagged abnormalities, AI summary (markdown)
- 4 action buttons: Accept, Edit, Reject, Escalate
- Each action has its own form (target doctor, consent duration, reason)

### Super Admin Dashboard (`/admin`)
- Hospital network overview with stats
- **Hospital detail popup** (transparent overlay):
  - Immutable identity section (name, reg number)
  - Editable demographics (city, state, contact, empanelment)
  - Hospital admin assignment/revocation
  - Department listing
- User role breakdown with counts
- Hospital onboarding modal

### Nurse Station (`/nurse`)
- Ward patient grid with vitals badges
- **Activity bar chart** (vitals logged per day)
- Log Vitals modal with form
- Shift handoff button
- Ward Bot status monitor

---

## State Management

### Auth Store (Zustand)
```javascript
{
  user: { user_id, full_name, role, permissions, hospital_id, ... },
  token: "jwt_string",
  isAuthenticated: boolean,
  loading: boolean,
  error: string | null,
  login(email, password),
  register(userData),
  logout(),
  refreshProfile(),
}
```

Helpers: `hasPermission(user, permission)`, `hasRole(user, ...roles)`

### API Layer (`api.js`)
- Axios instance with JWT interceptor
- Auto-redirect to `/login` on 401
- 30s timeout (120s for document upload)
- Organized by domain: `authAPI`, `chatAPI`, `consentAPI`, `screeningAPI`, `documentsAPI`, etc.

---

## Visualization Components (`MiniCharts.jsx`)

| Component | Props | Use Case |
|-----------|-------|----------|
| `SparkLine` | data, dataKey, color, height | Inline trend in stat cards |
| `VitalsTrendChart` | data, dataKey, color, unit, refMin, refMax | Vitals over time with reference bands |
| `MultiLineChart` | data, lines[] | Multiple metrics (e.g., systolic + diastolic) |
| `ActivityBar` | data, dataKey, color, height | Daily activity counts |
| `StatWithSparkline` | label, value, unit, data, trend | KPI with inline sparkline |

---

## Design System

- **Colors**: Blue-600 primary, Slate grays, Emerald success, Amber warning, Red error
- **Typography**: Inter font, sizes from 10px to 7xl
- **Border Radius**: 2xl (16px) for cards, xl (12px) for buttons, lg (10px) for inputs
- **Shadows**: `card` (subtle), `card-hover` (elevated), `glow` (blue glow)
- **Animations**: `fade-in`, `slide-up`, `pulse-slow`

### Component Classes (index.css)
- `.btn-primary` — Blue-600, white text, rounded-xl, shadow
- `.btn-secondary` — White, slate border, rounded-xl
- `.btn-ghost` — Transparent, hover bg-slate-100
- `.card` — White, rounded-2xl, border, shadow-card
- `.input` — White, rounded-xl, slate border, blue focus ring
- `.badge` / `.badge-green` / `.badge-blue` / `.badge-red` / `.badge-yellow` / `.badge-gray`
