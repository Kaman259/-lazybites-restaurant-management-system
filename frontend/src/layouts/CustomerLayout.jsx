import { NavLink, Outlet, useNavigate } from "react-router-dom";

import Button from "../components/common/Button";
import { useAuth } from "../context/AuthContext";

const customerLinks = [
  { to: "/customer", label: "Home", end: true },
  { to: "/customer/book-table", label: "Book a table" },
  { to: "/customer/reservations", label: "My reservations" },
  { to: "/customer/profile", label: "Profile" },
];

export default function CustomerLayout() {
  const { user, logout } = useAuth();
  const redirect = useNavigate();

  async function handleLogout() {
    await logout();
    redirect("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-[#f6fbfa]">
      <header className="sticky top-0 z-30 border-b border-teal-100 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <NavLink to="/customer" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-teal-600 font-black text-white">
              L
            </div>

            <div>
              <p className="font-bold text-slate-900">LazyBites</p>
              <p className="text-xs text-teal-700">
                Food, tables and calm water
              </p>
            </div>
          </NavLink>

          <nav className="hidden items-center gap-1 md:flex">
            {customerLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  `rounded-xl px-3 py-2 text-sm font-semibold ${
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

          <Button variant="secondary" onClick={handleLogout}>
            Logout
          </Button>
        </div>

        <nav className="flex gap-2 overflow-x-auto border-t border-teal-50 px-4 py-2 md:hidden">
          {customerLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
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
      </header>

      <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
        <div className="mb-6">
          <p className="text-sm text-slate-500">Welcome back</p>
          <p className="font-semibold text-slate-900">{user?.full_name}</p>
        </div>

        <Outlet />
      </main>
    </div>
  );
}