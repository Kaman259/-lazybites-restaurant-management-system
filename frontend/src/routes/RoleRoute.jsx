import { Navigate, Outlet } from "react-router-dom";

import Spinner from "../components/common/Spinner";
import { useAuth } from "../context/AuthContext";

export default function RoleRoute({ allowedRoles }) {
  const { loading, isAuthenticated, role, getDefaultPath } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(role)) {
    return (
      <Navigate
        to={
          role
            ? getDefaultPath(role)
            : "/unauthorized"
        }
        replace
      />
    );
  }

  return <Outlet />;
}