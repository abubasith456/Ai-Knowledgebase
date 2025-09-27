import React from "react";

type Props = {
    onMenu: () => void;   // open/close the left drawer on mobile
    onLogout: () => void; // navigate back to root or clear session
};

const AppBar: React.FC<Props> = ({ onMenu, onLogout }) => {
    return (
        <header className="sticky top-0 z-[60] border-b border-slate-200/60 bg-white/70 backdrop-blur supports-[backdrop-filter]:bg-white/60">
            <div className="mx-auto max-w-7xl h-16 px-4 sm:px-6 lg:px-8 flex items-center justify-between">
                {/* Brand + mobile menu */}
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

                {/* Actions: always visible, responsive widths */}
                <div className="flex items-center gap-2">
                    <input
                        type="search"
                        placeholder="Search projects, docs…"
                        className="w-32 xs:w-40 sm:w-52 md:w-64 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 placeholder:text-slate-400 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                    />
                    <button
                        className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 shadow-sm"
                        aria-label="Help"
                    >
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
            {/* Accent line */}
            <div className="h-[3px] w-full bg-gradient-to-r from-indigo-500 via-sky-500 to-emerald-500" />
        </header>
    );
};

export default AppBar;
