import React from "react";

type Props = { sidebarOpen: boolean; setSidebarOpen: (open: boolean) => void; onLogout: () => void };

const Header: React.FC<Props> = ({ sidebarOpen, setSidebarOpen, onLogout }) => {
    return (
        <header className="sticky top-0 z-40 border-b border-slate-200/60 bg-white/70 backdrop-blur supports-[backdrop-filter]:bg-white/60">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <button
                        className="lg:hidden rounded-md border border-slate-200 px-2.5 py-1.5 text-xs text-slate-700 hover:bg-slate-50"
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                    >
                        {sidebarOpen ? "Hide" : "Show"}
                    </button>
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-md bg-gradient-to-br from-indigo-500 to-violet-500" />
                        <span className="font-semibold tracking-tight text-slate-900">KB Console</span>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={onLogout}
                        className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 shadow-sm"
                    >
                        Logout
                    </button>
                </div>
            </div>
            <div className="h-1 w-full bg-gradient-to-r from-indigo-500 via-sky-500 to-emerald-500" />
        </header>
    );
};

export default Header;
