import {
  NavLink,
  Outlet,
  useNavigate,
} from "react-router-dom";

import Button from "../components/common/Button";
import { useAuth } from "../context/AuthContext";

export default function StaffLayout() {
  const {
    user,
    logout,
  } = useAuth();

  const redirect = useNavigate();

  const staffLinks = [
    {
      to: "/staff/dashboard",
      label: "Dashboard",
      roles: ["ADMIN", "STAFF"],
    },
    {
      to: "/staff/profile",
      label: "Profile",
      roles: ["ADMIN", "STAFF"],
    },
    {
      to: "/staff/tables",
      label: "Dining tables",
      roles: ["ADMIN", "STAFF"],
    },
    {
      to: "/staff/reservations",
      label: "Reservations",
      roles: ["ADMIN", "STAFF"],
    },
    {
      to: "/staff/menu",
      label: "Menu",
      roles: ["ADMIN", "STAFF"],
    },
    {
      to: "/staff/orders",
      label: "Orders",
      roles: ["ADMIN", "STAFF"],
    },
    {
      to: "/staff/billing",
      label: "Billing",
      roles: ["ADMIN", "STAFF"],
    },
    {
      to: "/staff/customers",
      label: "Customers",
      roles: ["ADMIN", "STAFF"],
    },
    {
      to: "/staff/reports",
      label: "Reports",
      roles: ["ADMIN"],
    },
    {
      to: "/staff/settings",
      label: "Restaurant settings",
      roles: ["ADMIN"],
    },
  ];

  const visibleLinks = staffLinks.filter(
    (link) => link.roles.includes(user?.role),
  );

  async function handleLogout() {
    await logout();

    redirect("/login", {
      replace: true,
    });
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white p-5 lg:block">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-600 font-black text-white">
            L
          </div>

          <div>
            <p className="font-bold text-slate-900">
              LazyBites
            </p>

            <p className="text-xs text-slate-500">
              {user?.role}
            </p>
          </div>
        </div>

        <nav className="space-y-1">
          {visibleLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `block rounded-xl px-4 py-3 text-sm font-semibold ${
                  isActive
                    ? "bg-teal-50 text-teal-700"
                    : "text-slate-600 hover:bg-slate-50"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 px-5 py-4 backdrop-blur sm:px-8 print:hidden">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500">
                Signed in as
              </p>

              <p className="font-semibold text-slate-900">
                {user?.full_name}
              </p>
            </div>

            <Button
              variant="secondary"
              onClick={handleLogout}
            >
              Logout
            </Button>
          </div>
        </header>

        <nav className="flex gap-2 overflow-x-auto border-b border-slate-200 bg-white px-4 py-3 lg:hidden print:hidden">
          {visibleLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `whitespace-nowrap rounded-full px-3 py-2 text-sm font-semibold ${
                  isActive
                    ? "bg-teal-600 text-white"
                    : "bg-slate-100 text-slate-600"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <main className="p-5 sm:p-8 print:p-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
