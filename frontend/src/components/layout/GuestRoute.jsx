import { Navigate } from "react-router-dom";
import useAuthStore from "../../store/authStore";

/**
 * GuestRoute — wraps Login/Register pages.
 * If already authenticated, redirects to the role's home dashboard.
 * This prevents the browser back/forward button from showing login
 * when already signed in, or re-logging in after logout.
 */
export default function GuestRoute({ children }) {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) return children;

  // Already logged in — send to role home
  const roleMap = {
    super_admin:      "/admin",
    govt_admin:       "/admin",
    hospital_admin:   "/hospital",
    doctor:           "/doctor",
    surgeon:          "/doctor",
    nurse:            "/nurse",
    ward_incharge:    "/nurse",
    pharmacist:       "/pharmacist",
    opd_staff:        "/opd",
    ipd_staff:        "/ipd",
    receptionist:     "/opd",
    insurance_officer:"/finance",
    scheme_officer:   "/scheme",
    police_interface: "/mlc",
    patient:          "/patient",
  };
  return <Navigate to={roleMap[user?.role] || "/patient"} replace />;
}
