import { Link, useLocation } from "react-router-dom";
import { useTheme } from "../context/ThemeContext";
import {
  LayoutDashboard,
  DollarSign,
  TrendingUp,
  Database,
  ChevronLeft,
  ChevronRight,
  Zap,
  Sun,
  Moon,
} from "lucide-react";

const navItems = [
  {
    path: "/",
    label: "Dashboard",
    icon: LayoutDashboard,
  },
  {
    path: "/prices",
    label: "Prices",
    icon: DollarSign,
  },
  {
    path: "/forecasts",
    label: "Forecasts",
    icon: TrendingUp,
  },
  {
    path: "/historical",
    label: "Historical",
    icon: Database,
  },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();

  return (
    <aside
      className={`fixed left-0 top-0 h-screen bg-base-200 border-r border-base-300 flex flex-col transition-all duration-300 z-50 ${
        collapsed ? "w-16" : "w-56"
      }`}
    >
      {/* Logo */}
      <div className="h-16 flex items-center gap-3 px-4 border-b border-base-300">
        <div className="btn btn-square btn-primary btn-sm">
          <Zap className="h-4 w-4" />
        </div>
        {!collapsed && (
          <div className="flex flex-col sidebar-logo-text">
            <span className="text-sm font-bold">TinyGrid</span>
            <span className="text-xs text-base-content/50">Grid Analytics</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        <ul className="menu menu-sm gap-1 px-2">
          {navItems.map(({ path, label, icon: Icon }) => {
            const isActive = location.pathname === path;
            return (
              <li key={path}>
                <Link
                  to={path}
                  className={isActive ? "active" : ""}
                  data-tip={collapsed ? label : undefined}
                >
                  <Icon className="h-4 w-4" />
                  {!collapsed && <span className="sidebar-text">{label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Theme toggle */}
      <div className="px-2 py-2 border-t border-base-300">
        <button
          onClick={toggleTheme}
          className={`btn btn-ghost btn-sm w-full ${collapsed ? "btn-square" : "justify-start"}`}
          data-tip={collapsed ? (theme === "dark" ? "Light mode" : "Dark mode") : undefined}
        >
          {theme === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
          {!collapsed && (
            <span className="sidebar-text">
              {theme === "dark" ? "Light Mode" : "Dark Mode"}
            </span>
          )}
        </button>
      </div>

      {/* Status indicator */}
      <div className="px-4 py-3 border-t border-base-300">
        <div className="flex items-center gap-2">
          <span className="badge badge-success badge-xs"></span>
          {!collapsed && (
            <span className="text-xs text-base-content/50 sidebar-text">Connected</span>
          )}
        </div>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={onToggle}
        className="btn btn-ghost btn-sm absolute -right-3 top-20 bg-base-200 border border-base-300 rounded-full w-6 h-6 p-0 min-h-0"
      >
        {collapsed ? (
          <ChevronRight className="h-3 w-3" />
        ) : (
          <ChevronLeft className="h-3 w-3" />
        )}
      </button>
    </aside>
  );
}
