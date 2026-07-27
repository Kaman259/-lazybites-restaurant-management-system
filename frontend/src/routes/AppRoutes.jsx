import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import AuthLayout from "../layouts/AuthLayout";
import CustomerLayout from "../layouts/CustomerLayout";
import StaffLayout from "../layouts/StaffLayout";
import ForgotPasswordPage from "../pages/auth/ForgotPasswordPage";
import LoginPage from "../pages/auth/LoginPage";
import RegisterPage from "../pages/auth/RegisterPage";
import BookTablePage from "../pages/customer/BookTablePage";
import CustomerHomePage from "../pages/customer/CustomerHomePage";
import CustomerProfilePage from "../pages/customer/CustomerProfilePage";
import MyReservationsPage from "../pages/customer/MyReservationsPage";
import NotFoundPage from "../pages/errors/NotFoundPage";
import UnauthorizedPage from "../pages/errors/UnauthorizedPage";
import BillingPage from "../pages/staff/BillingPage";
import CustomersPage from "../pages/staff/CustomersPage";
import DashboardPage from "../pages/staff/DashboardPage";
import MenuPage from "../pages/staff/MenuPage";
import OrdersPage from "../pages/staff/OrdersPage";
import ReportsPage from "../pages/staff/ReportsPage";
import ReservationsPage from "../pages/staff/ReservationsPage";
import SettingsPage from "../pages/staff/SettingsPage";
import TablesPage from "../pages/staff/TablesPage";
import ProtectedRoute from "./ProtectedRoute";
import RoleRoute from "./RoleRoute";

function RootRedirect() {
  const {
    loading,
    role,
    getDefaultPath,
  } = useAuth();

  if (loading) {
    return null;
  }

  return (
    <Navigate
      to={
        role
          ? getDefaultPath(role)
          : "/login"
      }
      replace
    />
  );
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/"
        element={<RootRedirect />}
      />

      <Route element={<AuthLayout />}>
        <Route
          path="/login"
          element={<LoginPage />}
        />

        <Route
          path="/register"
          element={<RegisterPage />}
        />

        <Route
          path="/forgot-password"
          element={<ForgotPasswordPage />}
        />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route
          element={
            <RoleRoute
              allowedRoles={[
                "ADMIN",
                "STAFF",
              ]}
            />
          }
        >
          <Route
            path="/staff"
            element={<StaffLayout />}
          >
            <Route
              index
              element={
                <Navigate
                  to="dashboard"
                  replace
                />
              }
            />

            <Route
              path="dashboard"
              element={<DashboardPage />}
            />

            <Route
              path="tables"
              element={<TablesPage />}
            />

            <Route
              path="reservations"
              element={<ReservationsPage />}
            />

            <Route
              path="menu"
              element={<MenuPage />}
            />

            <Route
              path="orders"
              element={<OrdersPage />}
            />

            <Route
              path="billing"
              element={<BillingPage />}
            />

            <Route
              path="customers"
              element={<CustomersPage />}
            />

            <Route
              element={
                <RoleRoute
                  allowedRoles={["ADMIN"]}
                />
              }
            >
              <Route
                path="reports"
                element={<ReportsPage />}
              />

              <Route
                path="settings"
                element={<SettingsPage />}
              />
            </Route>
          </Route>
        </Route>

        <Route
          element={
            <RoleRoute
              allowedRoles={["CUSTOMER"]}
            />
          }
        >
          <Route
            path="/customer"
            element={<CustomerLayout />}
          >
            <Route
              index
              element={<CustomerHomePage />}
            />

            <Route
              path="book-table"
              element={<BookTablePage />}
            />

            <Route
              path="reservations"
              element={<MyReservationsPage />}
            />

            <Route
              path="profile"
              element={<CustomerProfilePage />}
            />
          </Route>
        </Route>
      </Route>

      <Route
        path="/unauthorized"
        element={<UnauthorizedPage />}
      />

      <Route
        path="*"
        element={<NotFoundPage />}
      />
    </Routes>
  );
}