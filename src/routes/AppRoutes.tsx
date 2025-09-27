import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Login from "../pages/Login";
import { useAuth } from "../context/AuthContext";
import DashboardLayout from "../pages/Dashboard/DashboardLayout";

type GuardProps = { children: React.ReactElement };

const PrivateRoute: React.FC<GuardProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

const PublicRoute: React.FC<GuardProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Navigate to="/" replace /> : children;
};

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public: login shown only when not authenticated */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />

      {/* Private: dashboard requires authentication */}
      <Route
        path="/"
        element={
          <PrivateRoute>
            <DashboardLayout />
          </PrivateRoute>
        }
      />
    </Routes>
  );
};

export default AppRoutes;
