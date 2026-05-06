import { useState, useEffect, useRef } from "react";
import { Bell, BellRing, CheckCheck, AlertTriangle, Info, HeartPulse, X } from "lucide-react";
import { notifAPI } from "../../services/api";
import useAuthStore from "../../store/authStore";
import toast from "react-hot-toast";

const TYPE_META = {
  vitals_alert:      { icon: HeartPulse, color: "text-red-600 bg-red-50",     border: "border-red-200" },
  new_admission:     { icon: Info,       color: "text-blue-600 bg-blue-50",   border: "border-blue-200" },
  prescription_due:  { icon: AlertTriangle, color: "text-amber-600 bg-amber-50", border: "border-amber-200" },
  default:           { icon: Bell,       color: "text-slate-600 bg-slate-50", border: "border-slate-200" },
};

function timeAgo(d) {
  if (!d) return "";
  const diff = (Date.now() - new Date(d).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function NotificationBell() {
  const { isAuthenticated } = useAuthStore();
  const [notifications, setNotifications] = useState([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    fetchCount();
    const iv = setInterval(fetchCount, 30000); // poll every 30s
    return () => clearInterval(iv);
  }, [isAuthenticated]);

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const fetchCount = async () => {
    try {
      const res = await notifAPI.getCount();
      setUnread(res.data.unread || 0);
    } catch { /* silent */ }
  };

  const fetchAll = async () => {
    setLoading(true);
    try {
      const res = await notifAPI.getAll(false);
      setNotifications(res.data || []);
    } catch { /* silent */ } finally { setLoading(false); }
  };

  const handleOpen = () => {
    setOpen(prev => !prev);
    if (!open) fetchAll();
  };

  const markRead = async (id) => {
    try {
      await notifAPI.markRead(id);
      setNotifications(prev => prev.map(n => n.notification_id === id ? { ...n, is_read: true } : n));
      setUnread(prev => Math.max(0, prev - 1));
    } catch { /* silent */ }
  };

  const markAllRead = async () => {
    try {
      await notifAPI.markAllRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnread(0);
      toast.success("All notifications marked as read");
    } catch { /* silent */ }
  };

  return (
    <div className="relative" ref={panelRef}>
      {/* Bell button */}
      <button
        onClick={handleOpen}
        className="relative p-2.5 rounded-xl hover:bg-slate-100 transition-colors text-slate-600"
      >
        {unread > 0
          ? <BellRing className="w-5 h-5 text-blue-600 animate-[wiggle_1s_ease-in-out_infinite]" />
          : <Bell className="w-5 h-5" />
        }
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-red-500 text-white text-[10px] font-black rounded-full flex items-center justify-center px-1">
            {unread > 99 ? "99+" : unread}
          </span>
        )}
      </button>

      {/* Dropdown panel */}
      {open && (
        <div className="absolute right-0 top-12 w-96 bg-white border border-slate-200 rounded-2xl shadow-2xl z-50 flex flex-col max-h-[500px] animate-slide-up">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-slate-600" />
              <span className="font-bold text-slate-900 text-sm">Notifications</span>
              {unread > 0 && (
                <span className="text-[10px] font-black px-1.5 py-0.5 bg-red-100 text-red-600 rounded-full">{unread} unread</span>
              )}
            </div>
            <div className="flex gap-2">
              {unread > 0 && (
                <button onClick={markAllRead} className="text-xs text-blue-600 font-bold hover:text-blue-700 flex items-center gap-1">
                  <CheckCheck className="w-3.5 h-3.5" /> Mark all read
                </button>
              )}
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* List */}
          <div className="overflow-y-auto flex-1">
            {loading ? (
              <div className="p-8 text-center text-slate-400 text-sm">Loading...</div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center">
                <Bell className="w-8 h-8 text-slate-200 mx-auto mb-2" />
                <p className="text-slate-400 text-sm font-medium">No notifications yet</p>
              </div>
            ) : (
              notifications.map(n => {
                const meta = TYPE_META[n.type] || TYPE_META.default;
                const Icon = meta.icon;
                return (
                  <div
                    key={n.notification_id}
                    onClick={() => !n.is_read && markRead(n.notification_id)}
                    className={`px-5 py-4 border-b border-slate-50 flex items-start gap-3 cursor-pointer hover:bg-slate-50 transition-colors ${n.is_read ? "opacity-60" : ""}`}
                  >
                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${meta.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-bold text-slate-900 leading-tight">{n.title}</p>
                      <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{n.message}</p>
                      <p className="text-[10px] text-slate-400 mt-1">{timeAgo(n.created_at)}</p>
                    </div>
                    {!n.is_read && (
                      <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0 mt-1.5" />
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
