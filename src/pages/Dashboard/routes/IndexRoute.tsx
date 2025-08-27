import React, { useMemo, useState, useEffect } from "react";
import { useApp } from "../../../context/AppContext";
import SectionHeader from "../components/SectionHeader";
import StatusBadge from "../components/StatusBadge";

const IndexRoute: React.FC = () => {
    const {
        projects,
        documents,
        indexes,
        loading,
        createIndex,
        loadIndexes,
        startIndexing,
    } = useApp();

    const [projectId, setProjectId] = useState<string>("");
    const [creating, setCreating] = useState<boolean>(false);
    const [newIndexName, setNewIndexName] = useState<string>("");
    const [selectedDocs, setSelectedDocs] = useState<Record<string, boolean>>({});

    // Set first project as default if available
    useEffect(() => {
        if (projects.length > 0 && !projectId) {
            setProjectId(projects[0].id);
        }
    }, [projects, projectId]);

    // Load indexes when project changes
    useEffect(() => {
        if (projectId) {
            loadIndexes(projectId);
        }
    }, [projectId, loadIndexes]);

    const docs = useMemo(() => documents[projectId] ?? [], [documents, projectId]);
    const projectIndexes = useMemo(() => indexes[projectId] ?? [], [indexes, projectId]);
    const completedDocs = useMemo(() => docs.filter((d) => d.status === "completed"), [docs]);

    const toggleDoc = (id: string) =>
        setSelectedDocs((prev) => ({ ...prev, [id]: !prev[id] }));

    const handleCreateIndex = async () => {
        const ids = Object.keys(selectedDocs).filter((id) => selectedDocs[id]);
        if (!newIndexName.trim() || ids.length === 0) return;

        setCreating(true);
        try {
            await createIndex(projectId, newIndexName.trim(), ids);
            setCreating(false);
            setNewIndexName("");
            setSelectedDocs({});
        } catch (error) {
            setCreating(false);
            // Error is handled by context
        }
    };

    const handleStartIndexing = async (id: string) => {
        try {
            await startIndexing(projectId, id);
        } catch (error) {
            // Error is handled by context
        }
    };

    if (projects.length === 0) {
        return (
            <div className="text-center py-12">
                <p className="text-sm text-slate-500">No projects available. Create a project first.</p>
            </div>
        );
    }

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
                            <label className="block text-sm font-medium text-slate-700">Index name</label>
                            <input
                                type="text"
                                value={newIndexName}
                                onChange={(e) => setNewIndexName(e.target.value)}
                                placeholder="e.g., Main Index, Technical Docs"
                                className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                            />
                        </div>
                        
                        <div>
                            <label className="block text-sm font-medium text-slate-700">Select documents</label>
                            {completedDocs.length === 0 ? (
                                <p className="mt-2 text-sm text-slate-500">No completed documents available for indexing.</p>
                            ) : (
                                <div className="mt-2 space-y-2">
                                    {completedDocs.map((doc) => (
                                        <label key={doc.id} className="flex items-center">
                                            <input
                                                type="checkbox"
                                                checked={selectedDocs[doc.id] || false}
                                                onChange={() => toggleDoc(doc.id)}
                                                className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                                            />
                                            <span className="ml-2 text-sm text-slate-700">{doc.filename}</span>
                                        </label>
                                    ))}
                                </div>
                            )}
                        </div>
                        
                        <div className="flex gap-2">
                            <button
                                onClick={handleCreateIndex}
                                disabled={!newIndexName.trim() || Object.keys(selectedDocs).filter(id => selectedDocs[id]).length === 0 || creating}
                                className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {creating ? "Creating..." : "Create Index"}
                            </button>
                            <button
                                onClick={() => {
                                    setCreating(false);
                                    setNewIndexName("");
                                    setSelectedDocs({});
                                }}
                                className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm hover:bg-slate-50"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Indexes list */}
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
                <SectionHeader
                    title="Project Indexes"
                    subtitle={`${projectIndexes.length} index${projectIndexes.length !== 1 ? 'es' : ''} in this project`}
                />
                
                {projectIndexes.length === 0 ? (
                    <div className="mt-4 text-center py-8">
                        <p className="text-sm text-slate-500">No indexes created yet.</p>
                        <p className="text-xs text-slate-400 mt-1">Create an index to start organizing your documents.</p>
                    </div>
                ) : (
                    <div className="mt-4 space-y-3">
                        {projectIndexes.map((index) => (
                            <div key={index.id} className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-slate-50">
                                <div className="flex-1">
                                    <h3 className="text-sm font-medium text-slate-900">{index.name}</h3>
                                    <p className="text-xs text-slate-500">
                                        {index.document_ids.length} document{index.document_ids.length !== 1 ? 's' : ''} • ID: {index.id}
                                    </p>
                                </div>
                                <div className="flex items-center gap-3">
                                    <StatusBadge status={index.status} />
                                    {index.status === "idle" && (
                                        <button
                                            onClick={() => handleStartIndexing(index.id)}
                                            className="rounded-md bg-indigo-600 px-2 py-1 text-xs text-white shadow-sm hover:bg-indigo-500"
                                        >
                                            Start
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Loading indicator */}
            {loading && (
                <div className="text-center py-4">
                    <div className="inline-flex items-center gap-2 text-sm text-slate-500">
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600"></div>
                        Processing...
                    </div>
                </div>
            )}
        </div>
    );
};

export default IndexRoute;
