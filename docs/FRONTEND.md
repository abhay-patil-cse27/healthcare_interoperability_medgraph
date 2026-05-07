# MedGraph AI — Frontend Architecture

---

## Overview

The frontend is a **React 19** single-page application built with **Vite**, styled with **TailwindCSS**, and using **Zustand** for state management. It provides role-based dashboards for 17 different user roles.

---

## Tech Stack

| Library | Version | Purpose |
|---------|---------|---------|
| React | 19.2.5 | UI framework |
| Vite | 8.0.10 | Build tool + dev server |
| react-router-dom | 6.30.3 | Client-side routing |
| Zustand | 5.0.12 | State management |
| Axios | 1.16.0 | HTTP client |
| TailwindCSS | 3.4.4 | Utility-first styling |
| @headlessui/react | 2.2.10 | Accessible UI primitives |
| lucide-react | 1.14.0 | Icons |
| Recharts | 3.8.1 | Charts & dashboards |
| react-markdown | 10.1.0 | Markdown rendering |
| react-hot-toast | 2.6.0 | Toast notifications |
| cobe | 2.0.1 | 3D globe (landing page) |

---

## Project Structure

```
frontend/src/
├── App.jsx                    # Root component, route definitions
├── main.jsx                   # Entry point, React DOM render
├── index.css                  # TailwindCSS imports + custom layers
├── store/
│   └── authStore.js           # Zustand auth state (user, token, login, logout)
├── components/
│   ├── layout/
│   │   ├── AppLayout.jsx      # Sidebar + header + content wrapper
│   │   ├── ProtectedRoute.jsx # Auth guard (redirects to /login)
│   │   └── GuestRoute.jsx     # Redirect authenticated users away
│   ├── ui/
│   │   ├── EmptyState.jsx     # Empty state placeholder
│   │   ├── Globe.jsx          # 3D globe (landing)
│   │   ├── MiniCharts.jsx     # Small inline charts
│   │   ├── NotificationBell.jsx # Header notification icon
│   │   ├── PatientChip.jsx    # Patient identity chip
│   │   ├── PatientSearchBar.jsx # Global patient search
│   │   ├── Spinner.jsx        # Loading spinner
│   │   ├── StatusDot.jsx      # Status indicator
│   │   └── VaidyaBot.jsx      # Floating Vaidya chatbot widget
│   ├── ConsentManager/        # Consent request/grant UI
│   ├── DoctorDashboard/       # Doctor-specific components
│   └── PatientPortal/         # Patient-specific components
├── pages/
│   ├── Landing.jsx            # Public landing page
│   ├── Login.jsx              # Login selector (patient vs staff)
│   ├── LoginPatient.jsx       # Patient login form
│   ├── LoginStaff.jsx         # Staff login form
│   ├── Register.jsx           # Patient registration
│   ├── ProfilePage.jsx        # Self-service profile edit
│   ├── admin/
│   │   └── SuperAdminDashboard.jsx
│   ├── doctor/
│   │   ├── PatientLookup.jsx      # Search patients by MRN/name/ABHA
│   │   ├── ClinicalQuery.jsx      # RAG chat interface
│   │   ├── DoctorConsents.jsx     # Manage consent requests
│   │   ├── FHIRExchange.jsx       # Generate FHIR bundles
│   │   ├── ScreeningInbox.jsx     # View forwarded screenings
│   │   └── PatientDetailDrawer.jsx # Patient detail side panel
│   ├── patient/
│   │   ├── HealthRecords.jsx      # View own health records
│   │   ├── PatientChat.jsx        # Chat about own records
│   │   ├── PatientConsents.jsx    # Grant/revoke consents
│   │   └── DocumentUpload.jsx     # Upload PDF lab reports
│   ├── nurse/
│   │   └── NurseStation.jsx       # Vitals, notes, patient list
│   ├── pharmacist/
│   │   └── PharmacistConsole.jsx  # Prescription queue, dispense
│   ├── opd/
│   │   └── OPDDashboard.jsx       # Appointments, queue
│   ├── ipd/
│   │   └── IPDDashboard.jsx       # Admissions, beds, discharge
│   ├── hospital/
│   │   └── HospitalAdminDashboard.jsx # Departments, staff
│   ├── finance/
│   │   ├── InsuranceDashboard.jsx # Claims management
│   │   └── SchemeDashboard.jsx    # Govt scheme eligibility
│   ├── hitl/
│   │   └── HITLDashboard.jsx      # AI screening validation
│   └── mlc/
│       └── MLCDashboard.jsx       # Medico-Legal Cases
└── hooks/                         # Custom React hooks
```

---

## Routing

Role-based routing with automatic redirect on login:

| Role | Default Route | Dashboard |
|------|--------------|-----------|
| patient | `/patient` | Health records, chat, consents, documents |
| doctor, surgeon | `/doctor` | Patient lookup, clinical query, FHIR, screening |
| nurse, ward_incharge, ward_bot | `/nurse` | Nurse station |
| pharmacist | `/pharmacist` | Prescription queue |
| opd_staff, receptionist | `/opd` | Appointments |
| ipd_staff | `/ipd` | Admissions, beds |
| hospital_admin | `/hospital` | Departments, staff |
| super_admin, govt_admin | `/admin` | System management |
| insurance_officer | `/finance` | Claims |
| scheme_officer | `/scheme` | Govt schemes |
| police_interface | `/mlc` | MLC records |
| hitl_validator | `/hitl` | AI screening queue |

---

## State Management

### Auth Store (Zustand)

```javascript
{
  user: { user_id, email, full_name, role, permissions },
  token: "jwt-string",
  isAuthenticated: true/false,
  login(token, user),
  logout()
}
```

Persisted to `localStorage` as `mg_token` and `mg_user`.

### Axios Interceptor

- Auto-attaches `Authorization: Bearer <token>` to all requests
- On 401 response: clears auth store, redirects to `/login`

---

## Styling

- **TailwindCSS** with custom design tokens
- Custom `@layer components` for reusable classes: `btn-primary`, `card`, `input`, `badge`
- Color palette: brand colors + surface/neutral system
- Responsive design with mobile-first approach

---

## Key Components

### VaidyaBot
Floating chatbot widget available on all authenticated pages. Connects to `/vaidya/chat` endpoint. Maintains sliding-window conversation history.

### PatientSearchBar
Global search component used by doctors/nurses. Searches by name, MRN, ABHA ID, phone number.

### NotificationBell
Real-time notification indicator in the header. Polls `/notifications/count` for unread count.

### ProtectedRoute
Route guard that checks `isAuthenticated` from Zustand store. Redirects to `/login` if not authenticated.

---

## Environment

```env
VITE_API_URL=http://localhost:8000
```

All API calls use this base URL via Axios instance.

---

## Build & Development

```bash
# Development (HMR)
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```
