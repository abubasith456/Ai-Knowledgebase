import React, { useMemo, useState } from "react";
import type { DocumentItem, IndexItem, Project } from "../types";
import SectionHeader from "../components/SectionHeader";
import StatusBadge from "../components/StatusBadge";

const IndexRoute: React.FC = () => {
    // Demo sources (replace with context/API)
    const [projects] = useState<Project[]>([
        { id: "prj_demo1", name: "Knowledge Base", secret: "sec_xxxxx", indexingStatus: "idle" },
        { id: "prj_demo2", name: "Marketing Docs", secret: "sec_yyyyy", indexingStatus: "idle" },
    ]);
    const [docsByProject] = useState<Record<string, DocumentItem[]>>({
        prj_demo1: [
            { id: "d1", filename: "kb-intro.pdf", status: "completed", uploadedAt: "2025-08-26 10:30" },
            { id: "d2", filename: "release-notes.md", status: "completed", uploadedAt: "2025-08-26 10:40" },
            { id: "d3", filename: "draft.md", status: "parsing", uploadedAt: "2025-08-26 10:42" },
        ],
        prj_demo2: [{ id: "d4", filename: "q3-roadmap.docx", status: "completed", uploadedAt: "2025-08-26 10:41" }],
    });
    const [indexesByProject, setIndexesByProject] = useState<Record<string, IndexItem[]>>({
        prj_demo1: [],
        prj_demo2: [],
    });

    const [projectId, setProjectId] = useState<string>("prj_demo1");
    const docs = useMemo(() => docsByProject[projectId] ?? [], [docsByProject, projectId]);
    const indexes = useMemo(() => indexesByProject[projectId] ?? [], [indexesByProject, projectId]);

    const [creating, setCreating] = useState<boolean>(false);
    const [newIndexName, setNewIndexName] = useState<string>("");
    const [selectedDocs, setSelectedDocs] = useState<Record<string, boolean>>({});

    const completedDocs = useMemo(() => docs.filter((d) => d.status === "completed"), [docs]);

    const toggleDoc = (id: string) =>
        setSelectedDocs((prev) => ({ ...prev, [id]: !prev[id] }));

    const createIndex = () => {
        const ids = Object.keys(selectedDocs).filter((id) => selectedDocs[id]);
        if (!newIndexName.trim() || ids.length === 0) return;
        const idx: IndexItem = {
            id: `idx_${Date.now()}`,
            name: newIndexName.trim(),
            status: "idle",
            documentIds: ids,
        };
        setIndexesByProject((prev) => ({ ...prev, [projectId]: [idx, ...(prev[projectId] ?? [])] }));
        setCreating(false);
        setNewIndexName("");
        setSelectedDocs({});
    };

    const startIndexing = (id: string) => {
        setIndexesByProject((prev) => ({
            ...prev,
            [projectId]: (prev[projectId] ?? []).map((x) => (x.id === id ? { ...x, status: "indexing" } : x)),
        }));
        setTimeout(() => {
            setIndexesByProject((prev) => ({
                ...prev,
                [projectId]: (prev[projectId] ?? []).map((x) => (x.id === id ? { ...x, status: "completed" } : x)),
            }));
        }, 1500);
    };

    return (
        <div className="space-y-6">
            {/* Project selector */}
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
                <label className="block text-xs font-medium text-slate-700">Select project</label>
                <select
                    value={projectId}
                    onChange={(e) => setProjectId(e.target.value)}
                    className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                >
                    {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                            {p.name}
                        </option>
                    ))}
                </select>
            </div>

            {/* Create index */}
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
                <SectionHeader
                    title="Create index"
                    subtitle="Choose a name and select completed documents."
                    actions={
                        <button
                            onClick={() => setCreating((s) => !s)}
                            className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white shadow-sm hover:bg-indigo-500"
                        >
                            {creating ? "Close" : "New index"}
                        </button>
                    }
                />
                {creating && (
                    <div className="mt-4 space-y-4">
                        <div>
                            <label className="block text-xs font-medium text-slate-700">Index name</label>
                            <input
                                value={newIndexName}
                                onChange={(e) => setNewIndexName(e.target.value)}
                                placeholder="Support KB v1"
                                className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                            />
                        </div>

                        <div>
                            <div className="text-xs font-medium text-slate-700 mb-2">Select documents</div>
                            <div className="max-h-48 overflow-auto rounded-md border border-slate-200">
                                <ul className="divide-y divide-slate-200">
                                    {completedDocs.map((d) => (
                                        <li key={d.id} className="px-3 py-2 flex items-center gap-3">
                                            <input
                                                type="checkbox"
                                                checked={!!selectedDocs[d.id]}
                                                onChange={() => toggleDoc(d.id)}
                                                className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                                            />
                                            <div className="min-w-0">
                                                <div className="text-sm text-slate-900 truncate">{d.filename}</div>
                                                <div className="text-xs text-slate-500">{d.uploadedAt}</div>
                                            </div>
                                        </li>
                                    ))}
                                    {completedDocs.length === 0 && (
                                        <li className="px-3 py-8 text-sm text-slate-500 text-center">
                                            No completed documents in this project.
                                        </li>
                                    )}
                                </ul>
                            </div>
                        </div>

                        <div className="flex justify-end">
                            <button
                                onClick={createIndex}
                                className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white shadow-sm hover:bg-indigo-500"
                            >
                                Create index
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Index list */}
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="p-4 border-b border-slate-200">
                    <h3 className="text-sm font-semibold text-slate-900">Indexes</h3>
                </div>
                <ul className="divide-y divide-slate-200">
                    {indexes.map((x) => (
                        <li key={x.id} className="px-4 py-3 flex items-center justify-between">
                            <div>
                                <div className="text-sm font-medium text-slate-900">{x.name}</div>
                                <div className="text-xs text-slate-500">{x.documentIds.length} documents</div>
                            </div>
                            <div className="flex items-center gap-3">
                                <StatusBadge kind={x.status === "completed" ? "completed" : x.status === "indexing" ? "indexing" : "idle"} />
                                {x.status !== "completed" && (
                                    <button
                                        onClick={() => startIndexing(x.id)}
                                        className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 shadow-sm"
                                    >
                                        {x.status === "idle" ? "Start indexing" : "Indexing…"}
                                    </button>
                                )}
                            </div>
                        </li>
                    ))}
                    {indexes.length === 0 && (
                        <li className="px-4 py-10 text-center text-sm text-slate-500">No indexes created yet.</li>
                    )}
                </ul>
            </div>
        </div>
    );
};

export default IndexRoute;
