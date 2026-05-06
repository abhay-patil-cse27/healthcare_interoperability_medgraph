import { Navigate, useLocation } from "react-router-dom";
import { ShieldAlert, ArrowLeft } from "lucide-react";
import useAuthStore from "../../store/authStore";

/**
 * ProtectedRoute — gate for authenticated routes.
 *
 * Behaviour:
 * - Not authenticated → redirect to /login (preserving intended URL)
 * - Wrong role → show Access Denied screen (NOT a redirect, so back button works)
 * - Correct role → render children
 *
 * NOTE: Does NOT clear auth state. Back button pressing when logged out
 *       simply redirects to /login since isAuthenticated=false (token gone).
 *       Session is preserved in localStorage until explicit logout.
 */
export default function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, user } = useAuthStore();
  const location = useLocation();

  // Not authenticated — go to login, remember where they were going
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Wrong role — show inline access denied (back button still works)
  if (allowedRoles && !allowedRoles.includes(user?.role)) {
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
          <button
            onClick={() => window.history.back()}
            className="btn-secondary mx-auto"
          >
            <ArrowLeft className="w-4 h-4" />
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return children;
}
