// src/pages/Dashboard/components/IndexingPanel.tsx
import React from "react";
import StatusBadge from "./StatusBadge";
import type { IndexingStatus } from "../types";
import SectionHeader from "./SectionHeader";

type Props = { status: IndexingStatus };

const IndexingPanel: React.FC<Props> = ({ status }) => {
    const text =
        status === "idle"
            ? "Idle"
            : status === "indexing"
                ? "Indexing in progress…"
                : "Index built.";

    return (
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
            <SectionHeader title="Indexing status" subtitle="Project-level indexing after parsing completes" />
            <div className="mt-3 flex items-center gap-3">
                <StatusBadge kind={status === "completed" ? "completed" : status} />
                <span className="text-sm text-slate-700">{text}</span>
            </div>
        </section>
    );
};

export default IndexingPanel;
