import React, { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

const AppBar: React.FC<{ onMenu: () => void; onLogout: () => void }> = ({ onMenu, onLogout }) => {
    return (
        <header className="sticky top-0 z-[14] border-b border-slate-200/60 bg-white/70 backdrop-blur supports-[backdrop-filter]:bg-white/60">
            <div className="mx-auto max-w-7xl h-16 px-4 sm:px-6 lg:px-8 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <button
                        className="lg:hidden rounded-md border border-slate-200 px-2.5 py-1.5 text-xs text-slate-700 hover:bg-slate-50"
                        onClick={onMenu}
                        aria-label="Open menu"
                    >
                        Menu
                    </button>
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-md bg-gradient-to-br from-indigo-500 to-violet-500 shadow-sm" />
                        <span className="font-semibold tracking-tight text-slate-900">KB Console</span>
                        <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600 ring-1 ring-inset ring-slate-200">
                            Beta
                        </span>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <input
                        type="search"
                        placeholder="Search projects, docs…"
                        className="w-32 xs:w-40 sm:w-52 md:w-64 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 placeholder:text-slate-400 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                    />
                    <button className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 shadow-sm">
                        Help
                    </button>
                    <button
                        onClick={onLogout}
                        className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white shadow-sm hover:bg-indigo-500"
                    >
                        Logout
                    </button>
                </div>
            </div>
            <div className="h-[3px] w-full bg-gradient-to-r from-indigo-500 via-sky-500 to-emerald-500" />
        </header>
    );
};

const SidebarLink: React.FC<{ to: string; label: string; onClick?: () => void }> = ({ to, label, onClick }) => {
    return (
        <NavLink
            to={to}
            onClick={onClick}
            className={({ isActive }) =>
                `block rounded-lg px-3 py-2 text-sm font-medium transition-colors ${isActive ? "bg-indigo-50 text-indigo-700" : "text-slate-700 hover:bg-slate-50"
                }`
            }
        >
            {label}
        </NavLink>
    );
};

const Sidebar: React.FC<{ open: boolean; onClose: () => void }> = ({ open, onClose }) => {
    return (
        <>
            {/* Mobile overlay */}
            {open && <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-[2px] lg:hidden" onClick={onClose} />}

            {/* Mobile drawer */}
            <div
                className={`fixed z-50 inset-y-0 left-0 w-72 transform bg-white shadow-xl transition-transform duration-300 ease-out lg:hidden ${open ? "translate-x-0" : "-translate-x-full"
                    }`}
            >
                <nav className="h-full p-4 space-y-2">
                    <div className="text-xs font-semibold text-slate-500 px-2">Navigation</div>
                    <SidebarLink to="/dashboard/projects" label="Project" onClick={onClose} />
                    <SidebarLink to="/dashboard/index" label="Index" onClick={onClose} />
                </nav>
            </div>

            {/* Desktop sidebar */}
            <aside className="hidden lg:block lg:sticky lg:top-20 self-start h-[calc(100vh-5rem)] w-72 xl:w-80">
                <nav className="h-full rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-2">
                    <div className="text-xs font-semibold text-slate-500 px-2">Navigation</div>
                    <SidebarLink to="/dashboard/projects" label="Project" />
                    <SidebarLink to="/dashboard/index" label="Index" />
                </nav>
            </aside>
        </>
    );
};

const DashboardLayout: React.FC = () => {
    const [open, setOpen] = useState(false);
    const nav = useNavigate();

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
            <AppBar onMenu={() => setOpen(true)} onLogout={() => nav("/", { replace: true })} />

            <div className="mx-auto max-w-7xl grid h-[calc(100vh-4rem)] grid-cols-1 grid-rows-1 px-4 sm:px-6 lg:px-8">
                <div className="grid grid-cols-1 lg:grid-cols-[18rem_minmax(0,1fr)] xl:grid-cols-[20rem_minmax(0,1fr)] gap-6 py-6">
                    <Sidebar open={open} onClose={() => setOpen(false)} />
                    <main className="min-h-0 overflow-auto space-y-6">
                        <Outlet />
                    </main>
                </div>
            </div>
        </div>
    );
};

export default DashboardLayout;
