import { NavLink } from "react-router-dom";
import React from "react";

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

export default SidebarLink;
