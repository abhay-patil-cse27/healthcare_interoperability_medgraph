import { Navigate, useNavigate, useLocation } from "react-router-dom";
import { ShieldAlert, ArrowLeft, Home } from "lucide-react";
import useAuthStore from "../../store/authStore";

// Role → home path mapping
const ROLE_HOME = {
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

/**
 * ProtectedRoute — gate for authenticated routes.
 *
 * Behaviour:
 * - Not authenticated → redirect to /login (preserving intended URL)
 * - Wrong role → show Access Denied screen with navigation to user's home
 * - Correct role → render children
 */
export default function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, user } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  // Not authenticated — go to login, remember where they were going
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Wrong role — show inline access denied with proper navigation
  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    const homePath = ROLE_HOME[user?.role] || "/";

    const handleGoBack = () => {
      // If there's browser history, go back; otherwise navigate to role home
      if (window.history.length > 1) {
        navigate(-1);
      } else {
        navigate(homePath, { replace: true });
      }
    };

    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="text-center max-w-sm animate-slide-up">
          <div className="w-16 h-16 rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center mx-auto mb-5">
            <ShieldAlert className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Access Denied</h2>
          <p className="text-sm text-slate-500 leading-relaxed mb-2">
            Your role <span className="font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md">{user?.role}</span> cannot access this area.
          </p>
          <p className="text-xs text-slate-400 mb-6">
            Required: {allowedRoles.join(", ")}
          </p>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={handleGoBack}
              className="btn-secondary"
            >
              <ArrowLeft className="w-4 h-4" />
              Go Back
            </button>
            <button
              onClick={() => navigate(homePath, { replace: true })}
              className="btn-primary"
            >
              <Home className="w-4 h-4" />
              My Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return children;
}
