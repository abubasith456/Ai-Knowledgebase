import './App.css'
import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Root from './routes/Root';
import DashboardLayout from './pages/Dashboard/DashboardLayout';
import ProjectsRoute from './pages/Dashboard/routes/ProjectsRoute';
import IndexRoute from './pages/Dashboard/routes/IndexRoute';
import QueryRoute from './pages/Dashboard/routes/QueryRoute';
import ErrorNotification from './components/ErrorNotification';


const App: React.FC = () => {
  return (
    <>
      <ErrorNotification />
      <Router>
        <Routes>
          {/* Splash / Login decision */}
          <Route path="/" element={<Root />} />

          {/* Dashboard shell with sidebar + Outlet */}
          <Route path="/dashboard" element={<DashboardLayout />}>
            {/* Default to Projects tab */}
            <Route index element={<Navigate to="projects" replace />} />
            {/* Tabs in the left sidebar */}
            <Route path="projects" element={<ProjectsRoute />} />
            <Route path="index" element={<IndexRoute />} />
            <Route path="query" element={<QueryRoute />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </>
  );
};

export default App;
