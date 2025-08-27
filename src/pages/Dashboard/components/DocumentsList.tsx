import React from "react";
import StatusBadge from "./StatusBadge";
import type { DocumentItem, Project } from "../types";

type Props = { activeProject: Project | null; items: DocumentItem[] };

const DocumentsList: React.FC<Props> = ({ activeProject, items }) => {
    const mapDocToBadge = (s: DocumentItem["status"]) =>
        s === "pending" ? "idle" : s; // pending -> idle

    return (
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
                <div>
                    <h3 className="text-sm font-semibold text-slate-900">Documents</h3>
                    <p className="mt-1 text-xs text-slate-500">Track parsing progress and completion</p>
                </div>
                {activeProject && (
                    <div className="text-xs text-slate-500">
                        Project: <span className="font-mono">{activeProject.name}</span>
                    </div>
                )}
            </div>
            <ul className="divide-y divide-slate-200">
                {items.map((d) => (
                    <li key={d.id} className="px-4 py-3 flex items-center justify-between hover:bg-slate-50/60">
                        <div className="min-w-0">
                            <div className="text-sm text-slate-900 truncate">{d.filename}</div>
                            <div className="text-xs text-slate-500">{d.uploadedAt}</div>
                        </div>
                        <StatusBadge kind={mapDocToBadge(d.status)} />
                    </li>
                ))}
                {items.length === 0 && (
                    <li className="px-4 py-10 text-center text-sm text-slate-500">No documents uploaded yet.</li>
                )}
            </ul>
        </section>
    );
};

export default DocumentsList;
