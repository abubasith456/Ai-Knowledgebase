// src/pages/Dashboard/components/StatusBadge.tsx
import React from "react";

interface StatusBadgeProps {
    status: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
    const getStatusConfig = (status: string) => {
        switch (status) {
            case "pending":
                return {
                    label: "Pending",
                    className: "bg-yellow-100 text-yellow-800 ring-yellow-600/20",
                };
            case "parsing":
                return {
                    label: "Parsing",
                    className: "bg-blue-100 text-blue-800 ring-blue-600/20",
                };
            case "completed":
                return {
                    label: "Completed",
                    className: "bg-green-100 text-green-800 ring-green-600/20",
                };
            case "idle":
                return {
                    label: "Idle",
                    className: "bg-slate-100 text-slate-800 ring-slate-600/20",
                };
            case "indexing":
                return {
                    label: "Indexing",
                    className: "bg-purple-100 text-purple-800 ring-purple-600/20",
                };
            default:
                return {
                    label: status,
                    className: "bg-slate-100 text-slate-800 ring-slate-600/20",
                };
        }
    };

    const config = getStatusConfig(status);

    return (
        <span
            className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${config.className}`}
        >
            {config.label}
        </span>
    );
};

export default StatusBadge;
