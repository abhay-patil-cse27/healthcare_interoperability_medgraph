import { create } from "zustand";
import { authAPI } from "../services/api";

// Helper: check if a user has a specific permission
export const hasPermission = (user, permission) => {
  if (!user?.permissions) return false;
  return user.permissions.includes(permission);
};

// Helper: check role
export const hasRole = (user, ...roles) => {
  if (!user?.role) return false;
  return roles.includes(user.role);
};

const useAuthStore = create((set, get) => ({
  user:            JSON.parse(localStorage.getItem("mg_user") || "null"),
  token:           localStorage.getItem("mg_token") || null,
  isAuthenticated: !!localStorage.getItem("mg_token"),
  loading:         false,
  error:           null,

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const { data } = await authAPI.login(email, password);
      localStorage.setItem("mg_token", data.access_token);

      // Fetch full user profile with all RBAC fields (permissions, hospital_id, etc.)
      const { data: profile } = await authAPI.me();
      localStorage.setItem("mg_user", JSON.stringify(profile));

      set({ token: data.access_token, user: profile, isAuthenticated: true, loading: false });
      return profile;
    } catch (err) {
      const msg = err.response?.data?.detail || "Login failed";
      set({ error: msg, loading: false });
      throw new Error(msg);
    }
  },

  register: async (userData) => {
    set({ loading: true, error: null });
    try {
      // Backend only allows role=patient for self-registration
      const payload = { ...userData, role: "patient" };
      const { data } = await authAPI.register(payload);
      set({ loading: false });
      return data;
    } catch (err) {
      const msg = err.response?.data?.detail || "Registration failed";
      set({ error: msg, loading: false });
      throw new Error(msg);
    }
  },

  // Refresh profile (e.g. after hospital assignment changes)
  refreshProfile: async () => {
    try {
      const { data: profile } = await authAPI.me();
      localStorage.setItem("mg_user", JSON.stringify(profile));
      set({ user: profile });
      return profile;
    } catch {
      // Token expired or invalid
      get().logout();
    }
  },

  logout: () => {
    localStorage.removeItem("mg_token");
    localStorage.removeItem("mg_user");
    set({ user: null, token: null, isAuthenticated: false, error: null });
  },

  clearError: () => set({ error: null }),
}));

export default useAuthStore;
