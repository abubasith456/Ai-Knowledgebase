// src/pages/Dashboard/components/StatusBadge.tsx
import React from "react";
import type { IndexingStatus } from "../types";

type StatusKind = "parsing" | "completed" | IndexingStatus;

type Props = {
    kind: StatusKind;
    className?: string;
    "aria-label"?: string;
};

const palette: Record<StatusKind, string> = {
    parsing: "bg-amber-50 text-amber-700 ring-amber-600/20",
    indexing: "bg-sky-50 text-sky-700 ring-sky-600/20",
    completed: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
    idle: "bg-slate-50 text-slate-700 ring-slate-500/20",
};

const toLabel = (k: StatusKind): string => k.charAt(0).toUpperCase() + k.slice(1);

const StatusBadge: React.FC<Props> = ({ kind, className, ...rest }) => (
    <span
        className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${palette[kind]} ${className ?? ""}`}
        role="status"
        aria-live="polite"
        aria-label={rest["aria-label"] ?? `${toLabel(kind)} status`}
    >
        {toLabel(kind)}
    </span>
);

export default StatusBadge;
