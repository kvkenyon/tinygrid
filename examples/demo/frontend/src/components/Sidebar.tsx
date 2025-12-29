import { Link, useLocation } from "react-router-dom";
import { cn } from "../lib/utils";
import {
  LayoutDashboard,
  DollarSign,
  TrendingUp,
  Database,
  Activity,
  ChevronRight,
} from "lucide-react";

const navItems = [
  { 
    path: "/", 
    label: "Dashboard", 
    icon: LayoutDashboard,
    description: "Grid overview"
  },
  { 
    path: "/prices", 
    label: "Prices", 
    icon: DollarSign,
    description: "SPP & LMP data"
  },
  { 
    path: "/forecasts", 
    label: "Forecasts", 
    icon: TrendingUp,
    description: "Load & renewables"
  },
  { 
    path: "/historical", 
    label: "Historical", 
    icon: Database,
    description: "Archive data"
  },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside 
      className="fixed left-0 top-0 h-screen w-56 border-r flex flex-col"
      style={{ 
        backgroundColor: 'var(--bg-secondary)',
        borderColor: 'var(--border-primary)'
      }}
    >
      {/* Logo */}
      <div 
        className="h-14 flex items-center gap-3 px-4 border-b"
        style={{ borderColor: 'var(--border-primary)' }}
      >
        <div 
          className="flex items-center justify-center w-8 h-8"
          style={{ backgroundColor: 'var(--accent-cyan)' }}
        >
          <Activity className="h-5 w-5 text-black" />
        </div>
        <div className="flex flex-col">
          <span 
            className="text-sm font-bold tracking-wider"
            style={{ color: 'var(--text-primary)' }}
          >
            TINYGRID
          </span>
          <span 
            className="text-[9px] tracking-widest"
            style={{ color: 'var(--text-muted)' }}
          >
            ERCOT TERMINAL
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2">
        <div className="space-y-1">
          {navItems.map(({ path, label, icon: Icon, description }) => {
            const isActive = location.pathname === path;
            return (
              <Link
                key={path}
                to={path}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 transition-all group",
                  isActive && "border-l-2"
                )}
                style={{
                  backgroundColor: isActive ? 'var(--bg-tertiary)' : 'transparent',
                  borderColor: isActive ? 'var(--accent-cyan)' : 'transparent',
                }}
              >
                <Icon 
                  className="h-4 w-4 flex-shrink-0" 
                  style={{ color: isActive ? 'var(--accent-cyan)' : 'var(--text-muted)' }}
                />
                <div className="flex-1 min-w-0">
                  <span 
                    className="text-sm font-medium block"
                    style={{ color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)' }}
                  >
                    {label}
                  </span>
                  <span 
                    className="text-[10px] block truncate"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    {description}
                  </span>
                </div>
                {isActive && (
                  <ChevronRight 
                    className="h-3 w-3 flex-shrink-0" 
                    style={{ color: 'var(--accent-cyan)' }}
                  />
                )}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Status */}
      <div 
        className="px-4 py-3 border-t"
        style={{ borderColor: 'var(--border-primary)' }}
      >
        <div className="flex items-center gap-2">
          <div 
            className="w-2 h-2 rounded-full animate-pulse"
            style={{ backgroundColor: 'var(--status-normal)' }}
          />
          <span 
            className="text-[10px] tracking-widest"
            style={{ color: 'var(--text-muted)' }}
          >
            CONNECTED
          </span>
        </div>
        <div 
          className="text-[9px] mt-1 font-mono"
          style={{ color: 'var(--text-muted)' }}
        >
          api.ercot.com
        </div>
      </div>
    </aside>
  );
}
